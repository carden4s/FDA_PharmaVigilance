"""Snowflake data loading for FDA adverse events"""

from typing import List, Dict, Any, Optional

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

from logger import logger
from config import Config

config = Config()


class SnowflakeLoader:
    """Load data to Snowflake"""

    TABLE_NAME = "RAW_FDA_ADVERSE_EVENTS"

    def __init__(self):
        self.conn = None
        self.config = config

    def connect(self) -> Optional[snowflake.connector.SnowflakeConnection]:
        """Connect to Snowflake."""
        try:
            self.conn = snowflake.connector.connect(
                account=self.config.SNOWFLAKE_ACCOUNT,
                user=self.config.SNOWFLAKE_USER,
                password=self.config.SNOWFLAKE_PASSWORD,
                warehouse=self.config.SNOWFLAKE_WAREHOUSE,
                database=self.config.SNOWFLAKE_DATABASE,
                schema=self.config.SNOWFLAKE_SCHEMA,
                role=self.config.SNOWFLAKE_ROLE,
            )
            logger.info("Connected to Snowflake")
            return self.conn
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {str(e)}")
            return None

    def test_connection(self) -> bool:
        """Test Snowflake connection."""
        try:
            conn = self.connect()
            if not conn:
                return False
            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_TIMESTAMP()")
            cursor.fetchone()
            cursor.close()
            logger.info("Snowflake connection test successful")
            return True
        except Exception as e:
            logger.error(f"Snowflake connection test failed: {str(e)}")
            return False

    def create_table_if_not_exists(self) -> bool:
        """Create Bronze layer table if not exists."""
        if not self.conn:
            if not self.connect():
                return False

        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.config.SNOWFLAKE_DATABASE}.{self.config.SNOWFLAKE_SCHEMA}.{self.TABLE_NAME} (
            safetyreportid VARCHAR,
            report_type VARCHAR,
            serious INT,
            seriousness_death INT,
            seriousness_hospitalization INT,
            seriousness_lifethreatening INT,
            seriousness_disability INT,
            patient_onsetage INT,
            patient_sex INT,
            patient_weight DECIMAL(10, 2),
            drug_name VARCHAR,
            drug_route VARCHAR,
            drug_dose_value VARCHAR,
            drug_dose_unit VARCHAR,
            drug_indication VARCHAR,
            reaction_name VARCHAR,
            reaction_outcome INT,
            reaction_meddra_pt VARCHAR,
            reaction_meddra_llt VARCHAR,
            event_date VARCHAR,
            report_date VARCHAR,
            received_date VARCHAR,
            loaded_at TIMESTAMP,
            source_drug VARCHAR,
            ingestion_batch_id VARCHAR,
            source_date VARCHAR
        )
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            cursor.close()
            logger.info("Bronze table created or already exists")
            return True
        except Exception as e:
            logger.error(f"Failed to create table: {str(e)}")
            return False

    def truncate_table(self) -> bool:
        """Truncate the Bronze table (for idempotent full reloads)."""
        if not self.conn and not self.connect():
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"TRUNCATE TABLE IF EXISTS "
                f"{self.config.SNOWFLAKE_DATABASE}.{self.config.SNOWFLAKE_SCHEMA}.{self.TABLE_NAME}"
            )
            cursor.close()
            logger.info("Bronze table truncated")
            return True
        except Exception as e:
            logger.error(f"Failed to truncate table: {str(e)}")
            return False

    def load_batch(self, records: List[Dict[str, Any]], batch_size: int = 16000) -> Dict[str, Any]:
        """Bulk-load records to Snowflake using write_pandas."""
        if not self.conn:
            if not self.connect():
                return {"success": False, "total": 0, "loaded": 0, "failed": 0}

        total = len(records)
        if total == 0:
            return {"success": True, "total": 0, "loaded": 0, "failed": 0}

        # Build a DataFrame; uppercase columns to match unquoted Snowflake identifiers
        df = pd.DataFrame(records)
        df.columns = [c.upper() for c in df.columns]

        logger.info(f"Loading {total} records via write_pandas (chunks of {batch_size})")

        try:
            success, n_chunks, n_rows, _ = write_pandas(
                conn=self.conn,
                df=df,
                table_name=self.TABLE_NAME,
                database=self.config.SNOWFLAKE_DATABASE,
                schema=self.config.SNOWFLAKE_SCHEMA,
                chunk_size=batch_size,
                quote_identifiers=False,
            )
            loaded = int(n_rows)
            failed = total - loaded
            logger.info(f"write_pandas: success={success}, chunks={n_chunks}, rows={loaded}")
            return {"success": bool(success) and failed == 0,
                    "total": total, "loaded": loaded, "failed": failed}
        except Exception as e:
            logger.error(f"Bulk load failed: {str(e)}")
            return {"success": False, "total": total, "loaded": 0, "failed": total}

    def close(self):
        """Close Snowflake connection."""
        if self.conn:
            self.conn.close()
            logger.info("Snowflake connection closed")