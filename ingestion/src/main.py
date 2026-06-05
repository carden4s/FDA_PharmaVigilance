"""Main entry point for FDA ingestion pipeline"""

import argparse
import sys
import uuid
import time
from datetime import datetime
from typing import Optional

from config import Config, get_config
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
    parser.add_argument(
        "--drug",
        type=str,
        help="Specific drug to ingest (default: all configured drugs)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Records per batch (default: 1000)"
    )
    parser.add_argument(
        "--mode",
        choices=["test", "prod"],
        default="prod",
        help="Test or production mode"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without loading"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    return parser.parse_args()


def main():
    """Main ingestion pipeline"""
    args = parse_args()
    config = get_config()
    
    # Validate configuration
    is_valid, errors = config.validate()
    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return 1
    
    logger.info("═" * 60)
    logger.info("FDA PharmaVigilance Ingestion Pipeline")
    logger.info("═" * 60)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Batch Size: {args.batch_size}")
    logger.info(f"Dry Run: {args.dry_run}")
    
    # Generate batch ID
    batch_id = str(uuid.uuid4())
    logger.info(f"Batch ID: {batch_id}")
    
    # Initialize clients
    fda_client = FDAClient(api_key=config.FDA_API_KEY)
    loader = SnowflakeLoader()
    
    # Test FDA API connection
    if not fda_client.test_connection():
        logger.error("Failed to connect to FDA API")
        return 1
    
    # Test Snowflake connection
    if not loader.test_connection():
        logger.error("Failed to connect to Snowflake")
        return 1
    
    # Create table
    if not loader.create_table_if_not_exists():
        logger.error("Failed to create table")
        loader.close()
        return 1
    
    # Determine drugs to ingest
    drugs_to_ingest = []
    if args.drug:
        drugs_to_ingest = [{"name": args.drug, "fda_id": args.drug.upper()}]
    else:
        drugs_to_ingest = config.MONITORED_DRUGS
    
    # Ingestion loop
    total_records = 0
    total_loaded = 0
    start_time = time.time()
    
    try:
        for drug_config in drugs_to_ingest:
            drug_name = drug_config["name"]
            logger.info(f"\n{'-' * 60}")
            logger.info(f"Ingesting: {drug_name}")
            logger.info(f"{'-' * 60}")
            
            # Fetch data
            fda_response = fda_client.fetch_adverse_events(
                drug_name=drug_name,
                limit=1000,
                skip=0
            )
            
            if not fda_response or "results" not in fda_response:
                logger.warning(f"No data returned for {drug_name}")
                continue
            
            # Flatten data
            flattened = DataProcessor.flatten_response(fda_response)
            if not flattened:
                logger.warning(f"No records to process for {drug_name}")
                continue
            
            # Validate data
            validation_results = Validator.validate_records(flattened)
            logger.info(Validator.generate_report(validation_results))
            
            # Load data (if not dry-run)
            records_to_load = validation_results["passed"]
            total_records += len(flattened)
            
            # Add metadata
            for record in records_to_load:
                DataProcessor.add_metadata(record, drug_name, batch_id)
            
            if not args.dry_run:
                load_result = loader.load_batch(records_to_load, args.batch_size)
                logger.info(f"Load result: {load_result}")
                total_loaded += load_result["loaded"]
            else:
                logger.info(f"[DRY RUN] Would load {len(records_to_load)} records")
                total_loaded += len(records_to_load)
    
    finally:
        loader.close()
    
    # Summary
    elapsed_time = time.time() - start_time
    logger.info(f"\n{'=' * 60}")
    logger.info("INGESTION SUMMARY")
    logger.info(f"{'=' * 60}")
    logger.info(f"Total Events: {total_records}")
    logger.info(f"Loaded Records: {total_loaded}")
    logger.info(f"Elapsed Time: {elapsed_time:.1f} seconds")
    logger.info(f"Records/sec: {total_loaded / elapsed_time:.1f}")
    logger.info(f"{'=' * 60}\n")
    
    return 0 if total_loaded > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
