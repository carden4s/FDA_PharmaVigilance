"""Main entry point for FDA ingestion pipeline"""

"""Main entry point for FDA ingestion pipeline"""

import argparse
import sys
import uuid
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import get_config
from logger import logger
from fda_client import FDAClient
from data_processor import DataProcessor
from validator import Validator
from snowflake_loader import SnowflakeLoader


def parse_args():
    parser = argparse.ArgumentParser(description="FDA PharmaVigilance Data Ingestion Pipeline")
    parser.add_argument("--drug", type=str, help="Specific drug to ingest (default: all configured drugs)")
    parser.add_argument("--batch-size", type=int, default=16000, help="Records per write_pandas chunk")
    parser.add_argument("--workers", type=int, default=8, help="Parallel API fetch workers (default: 8)")
    parser.add_argument("--mode", choices=["test", "prod"], default="prod")
    parser.add_argument("--dry-run", action="store_true", help="Validate without loading")
    parser.add_argument("--truncate", action="store_true",
                        help="[DEV ONLY] Truncate Bronze before loading (Bronze is append-only).")
    parser.add_argument("--start-date", type=str, help="Window start (YYYYMMDD), inclusive")
    parser.add_argument("--end-date", type=str, help="Window end (YYYYMMDD), inclusive")
    parser.add_argument("--days-back", type=int, help="Rolling window: receivedate in [today-N, today].")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    return parser.parse_args()


def resolve_window(args):
    if args.days_back is not None:
        end_dt = datetime.now(timezone.utc).date()
        start_dt = end_dt - timedelta(days=args.days_back)
        return start_dt.strftime("%Y%m%d"), end_dt.strftime("%Y%m%d"), end_dt.strftime("%Y%m%d")
    if args.start_date and args.end_date:
     return args.start_date, args.end_date, args.end_date
    return None, None, datetime.now(timezone.utc).strftime("%Y%m%d")


def fetch_and_flatten(api_key, drug_name, start_date, end_date):
    """Worker: fetch + flatten one drug (network-bound, runs in a thread)."""
    client = FDAClient(api_key=api_key)
    resp = client.fetch_adverse_events(drug_name=drug_name, start_date=start_date, end_date=end_date)
    if not resp or not resp.get("results"):
        return []
    return DataProcessor.flatten_response(resp)


def main():
    args = parse_args()
    config = get_config()

    is_valid, errors = config.validate()
    if not is_valid:
        logger.error("Configuration validation failed:")
        for e in errors:
            logger.error(f"  - {e}")
        return 1

    start_date, end_date, source_date = resolve_window(args)
    window_str = f"{start_date}..{end_date}" if start_date else "ALL (recent)"

    logger.info("=" * 60)
    logger.info("FDA PharmaVigilance Ingestion Pipeline")
    logger.info("=" * 60)
    logger.info(f"Mode: {args.mode} | Window: {window_str} | Workers: {args.workers}")
    logger.info(f"Dry Run: {args.dry_run} | Truncate: {args.truncate}")

    batch_id = str(uuid.uuid4())
    logger.info(f"Batch ID: {batch_id}")

    loader = SnowflakeLoader()

    if not FDAClient(api_key=config.FDA_API_KEY).test_connection():
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
        logger.warning("TRUNCATE requested — Bronze is append-only; dev use only.")
        if not loader.truncate_table():
            loader.close()
            return 1

    drugs_to_ingest = [{"name": args.drug}] if args.drug else config.MONITORED_DRUGS

    total_records = 0
    total_loaded = 0
    start_time = time.time()

    try:
        # Fetch in parallel (I/O-bound); load sequentially in main thread (connection isn't thread-safe)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(fetch_and_flatten, config.FDA_API_KEY, d["name"], start_date, end_date): d["name"]
                for d in drugs_to_ingest
            }
            for fut in as_completed(futures):
                drug_name = futures[fut]
                try:
                    flattened = fut.result()
                except Exception as e:
                    logger.error(f"Fetch failed for {drug_name}: {e}")
                    continue
                if not flattened:
                    logger.warning(f"No records for {drug_name}")
                    continue

                vr = Validator.validate_records(flattened)
                recs = vr["passed"]
                for r in recs:
                    DataProcessor.add_metadata(r, drug_name, batch_id)
                    r["source_date"] = source_date
                total_records += len(flattened)

                if not args.dry_run:
                    result = loader.load_batch(recs, args.batch_size)
                    logger.info(f"{drug_name}: {result['loaded']} loaded")
                    total_loaded += result["loaded"]
                else:
                    total_loaded += len(recs)
    finally:
        loader.close()

    elapsed = max(time.time() - start_time, 1e-9)
    logger.info("=" * 60)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Window: {window_str}")
    logger.info(f"Total Events: {total_records}")
    logger.info(f"Loaded Records: {total_loaded}")
    logger.info(f"Elapsed: {elapsed:.1f}s | Records/sec: {total_loaded / elapsed:.1f}")
    logger.info("=" * 60)
    return 0 if total_loaded > 0 else 1


if __name__ == "__main__":
    sys.exit(main())