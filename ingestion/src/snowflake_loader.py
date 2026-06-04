"""Snowflake data loading for FDA adverse events"""

from typing import List, Dict, Any, Optional
import snowflake.connector
from logger import logger
from config import Config

config = Config()


class SnowflakeLoader:
    """Load data to Snowflake"""
    
    def __init__(self):
        """Initialize Snowflake loader"""
        self.conn = None
        self.config = config
    
    def connect(self) -> Optional[snowflake.connector.SnowflakeConnection]:
        """
        Connect to Snowflake
        
        Returns:
            Snowflake connection or None
        """
        try:
            self.conn = snowflake.connector.connect(
                account=self.config.SNOWFLAKE_ACCOUNT,
                user=self.config.SNOWFLAKE_USER,
                password=self.config.SNOWFLAKE_PASSWORD,
                warehouse=self.config.SNOWFLAKE_WAREHOUSE,
                database=self.config.SNOWFLAKE_DATABASE,
                role=self.config.SNOWFLAKE_ROLE,
            )
            logger.info("✓ Connected to Snowflake")
            return self.conn
        except Exception as e:
            logger.error(f"✗ Failed to connect to Snowflake: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test Snowflake connection
        
        Returns:
            True if connection successful
        """
        try:
            conn = self.connect()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_TIMESTAMP()")
            cursor.fetchone()
            cursor.close()
            
            logger.info("✓ Snowflake connection test successful")
            return True
        except Exception as e:
            logger.error(f"✗ Snowflake connection test failed: {str(e)}")
            return False
    
    def create_table_if_not_exists(self) -> bool:
        """
        Create Bronze layer table if not exists
        
        Returns:
            True if successful
        """
        if not self.conn:
            if not self.connect():
                return False
        
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.config.SNOWFLAKE_DATABASE}.{self.config.SNOWFLAKE_SCHEMA}.RAW_FDA_ADVERSE_EVENTS (
            safetyreportid VARCHAR PRIMARY KEY,
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
            ingestion_batch_id VARCHAR
        )
        """
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            logger.info("✓ Bronze table created or already exists")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create table: {str(e)}")
            return False
    
    def load_batch(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """
        Load batch of records to Snowflake
        
        Args:
            records: Records to load
            batch_size: Size of batches
        
        Returns:
            Load summary
        """
        if not self.conn:
            if not self.connect():
                return {"success": False, "total": 0, "loaded": 0, "failed": 0}
        
        total = len(records)
        loaded = 0
        failed = 0
        
        logger.info(f"Loading {total} records in batches of {batch_size}")
        
        for i in range(0, total, batch_size):
            batch = records[i:i + batch_size]
            batch_result = self._load_batch_internal(batch)
            loaded += batch_result["loaded"]
            failed += batch_result["failed"]
            
            logger.info(f"Batch {i//batch_size + 1}: {batch_result['loaded']} loaded, {batch_result['failed']} failed")
        
        return {
            "success": failed == 0,
            "total": total,
            "loaded": loaded,
            "failed": failed
        }
    
    def _load_batch_internal(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Load single batch of records
        
        Args:
            records: Records to load
        
        Returns:
            Count of loaded and failed
        """
        try:
            cursor = self.conn.cursor()
            
            # Insert records
            for record in records:
                columns = ", ".join(record.keys())
                placeholders = ", ".join(["%s"] * len(record))
                values = tuple(record.values())
                
                sql = f"""
                INSERT INTO {self.config.SNOWFLAKE_DATABASE}.{self.config.SNOWFLAKE_SCHEMA}.RAW_FDA_ADVERSE_EVENTS
                ({columns}) VALUES ({placeholders})
                """
                
                try:
                    cursor.execute(sql, values)
                except Exception as e:
                    logger.warning(f"Failed to insert record {record.get('safetyreportid')}: {str(e)}")
            
            cursor.close()
            return {"loaded": len(records), "failed": 0}
        
        except Exception as e:
            logger.error(f"Batch load failed: {str(e)}")
            return {"loaded": 0, "failed": len(records)}
    
    def close(self):
        """Close Snowflake connection"""
        if self.conn:
            self.conn.close()
            logger.info("Snowflake connection closed")
