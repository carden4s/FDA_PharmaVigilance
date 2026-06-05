"""Main entry point for FDA ingestion pipeline"""

import argparse
import sys
import uuid
import time
from datetime import datetime, timedelta, timezone

from config import get_config
from logger import logger
from fda_client import FDAClient
from data_processor import DataProcessor
from validator import Validator
from snowflake_loader import SnowflakeLoader


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="FDA PharmaVigilance Data Ingestion Pipeline"
    )
    parser.add_argument("--drug", type=str,
                        help="Specific drug to ingest (default: all configured drugs)")
    parser.add_argument("--batch-size", type=int, default=16000,
                        help="Records per write_pandas chunk (default: 16000)")
    parser.add_argument("--mode", choices=["test", "prod"], default="prod",
                        help="Test or production mode")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate without loading")
    parser.add_argument("--truncate", action="store_true",
                        help="[DEV ONLY] Truncate Bronze before loading. "
                             "Do not use in prod (Bronze is append-only).")

    # Date-window controls for daily recon / backfill (receivedate, YYYYMMDD)
    parser.add_argument("--start-date", type=str,
                        help="Window start (YYYYMMDD), inclusive")
    parser.add_argument("--end-date", type=str,
                        help="Window end (YYYYMMDD), inclusive")
    parser.add_argument("--days-back", type=int,
                        help="Rolling window: receivedate in [today-N, today]. "
                             "Overrides --start/--end if set.")

    parser.add_argument("--log-level",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO",
                        help="Logging level")
    return parser.parse_args()


def resolve_window(args):
    """Return (start_date, end_date, source_date) as YYYYMMDD strings (or None)."""
    if args.days_back is not None:
        end_dt = datetime.now(timezone.utc).date()
        start_dt = end_dt - timedelta(days=args.days_back)
        start = start_dt.strftime("%Y%m%d")
        end = end_dt.strftime("%Y%m%d")
        return start, end, end
    if args.start_date and args.end_date:
        return args.start_date, args.end_date, args.end_date
    # No window → pull all recent matching reports (paginated)
    return None, None, datetime.now(timezone.utc).strftime("%Y%m%d")


def main():
    """Main ingestion pipeline"""
    args = parse_args()
    config = get_config()

    is_valid, errors = config.validate()
    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return 1

    start_date, end_date, source_date = resolve_window(args)
    window_str = f"{start_date}..{end_date}" if start_date else "ALL (recent)"

    logger.info("=" * 60)
    logger.info("FDA PharmaVigilance Ingestion Pipeline")
    logger.info("=" * 60)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Window (receivedate): {window_str}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info(f"Truncate: {args.truncate}")

    batch_id = str(uuid.uuid4())
    logger.info(f"Batch ID: {batch_id}")

    fda_client = FDAClient(api_key=config.FDA_API_KEY)
    loader = SnowflakeLoader()

    if not fda_client.test_connection():
        logger.error("Failed to connect to FDA API")
        return 1
    if not loader.test_connection():
        logger.error("Failed to connect to Snowflake")
        return 1
    if not loader.create_table_if_not_exists():
        logger.error("Failed to create table")
        loader.close()
        return 1

    if args.truncate and not args.dry_run:
        logger.warning("TRUNCATE requested — Bronze is meant to be append-only. "
                       "Use only for dev resets.")
        if not loader.truncate_table():
            logger.error("Failed to truncate table")
            loader.close()
            return 1

    if args.drug:
        drugs_to_ingest = [{"name": args.drug, "fda_id": args.drug.upper()}]
    else:
        drugs_to_ingest = config.MONITORED_DRUGS

    total_records = 0
    total_loaded = 0
    start_time = time.time()

    try:
        for drug_config in drugs_to_ingest:
            drug_name = drug_config["name"]
            logger.info("-" * 60)
            logger.info(f"Ingesting: {drug_name}")
            logger.info("-" * 60)

            fda_response = fda_client.fetch_adverse_events(
                drug_name=drug_name,
                start_date=start_date,
                end_date=end_date,
            )
            if not fda_response or not fda_response.get("results"):
                logger.warning(f"No data returned for {drug_name}")
                continue

            flattened = DataProcessor.flatten_response(fda_response)
            if not flattened:
                logger.warning(f"No records to process for {drug_name}")
                continue

            validation_results = Validator.validate_records(flattened)
            logger.info(Validator.generate_report(validation_results))

            records_to_load = validation_results["passed"]
            total_records += len(flattened)

            # Metadata + recon date tag
            for record in records_to_load:
                DataProcessor.add_metadata(record, drug_name, batch_id)
                record["source_date"] = source_date

            if not args.dry_run:
                load_result = loader.load_batch(records_to_load, args.batch_size)
                logger.info(f"Load result: {load_result}")
                total_loaded += load_result["loaded"]
            else:
                logger.info(f"[DRY RUN] Would load {len(records_to_load)} records")
                total_loaded += len(records_to_load)

    finally:
        loader.close()

    elapsed_time = max(time.time() - start_time, 1e-9)
    logger.info("=" * 60)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Window (receivedate): {window_str}")
    logger.info(f"Total Events: {total_records}")
    logger.info(f"Loaded Records: {total_loaded}")
    logger.info(f"Elapsed Time: {elapsed_time:.1f} seconds")
    logger.info(f"Records/sec: {total_loaded / elapsed_time:.1f}")
    logger.info("=" * 60)

    return 0 if total_loaded > 0 else 1


if __name__ == "__main__":
    sys.exit(main())