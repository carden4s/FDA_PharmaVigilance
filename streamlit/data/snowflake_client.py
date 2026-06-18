# Snowflake client for Streamlit dashboard
# Co-authored with CoCo
"""Snowflake data access layer for the dashboard."""

import streamlit as st
from snowflake.connector import connect
import pandas as pd
from typing import List, Dict, Any, Optional


@st.cache_resource
def get_connection():
    """Get Snowflake connection (cached)"""
    try:
        conn = connect(
            account=st.secrets["snowflake"]["account"],
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"]
        )
        return conn
    except Exception as e:
        st.error(f"Error al conectar con Snowflake: {str(e)}")
        return None


class SnowflakeClient:
    """Snowflake data access layer"""

    def __init__(self):
        self.conn = get_connection()

    def query(self, sql: str, params: List[Any] = None) -> Optional[pd.DataFrame]:
        if not self.conn:
            st.error("Sin conexión a la base de datos")
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params or [])
            df = cursor.fetch_pandas_all()
            cursor.close()
            return df
        except Exception as e:
            st.error(f"La consulta falló: {str(e)}")
            return None

    def get_drugs(self) -> List[str]:
        df = self.query("SELECT DISTINCT drug_name FROM agg_drug_safety_profile ORDER BY drug_name")
        return df["DRUG_NAME"].tolist() if df is not None else []

    def get_drug_profile(self, drug_name: str) -> Optional[Dict]:
        """Get report-level safety profile for a drug"""
        sql = """
        SELECT
            drug_name,
            total_reports,
            serious_reports,
            serious_rate_pct,
            fatal_reports,
            fatal_rate_pct,
            hospitalized_reports,
            hospitalization_rate_pct,
            avg_patient_age
        FROM agg_drug_safety_profile
        WHERE drug_name = %s
        """
        df = self.query(sql, [drug_name])
        return df.to_dict("records")[0] if df is not None and len(df) > 0 else None

    def get_top_reactions(self, drug_name: str, limit: int = 10) -> Optional[pd.DataFrame]:
        sql = """
        SELECT
            reaction_name,
            reaction_count,
            reaction_frequency_pct,
            serious_reaction_count,
            fatal_reaction_count
        FROM agg_reaction_frequency
        WHERE drug_name = %s
        ORDER BY reaction_count DESC
        LIMIT %s
        """
        return self.query(sql, [drug_name, limit])

    def get_disproportionality(self, drug_name: str = None, limit: int = 100):
        """PRR/ROR signals already flagged is_signal, ranked by the 95% CI lower bound."""
        base = """
        SELECT drug_name, reaction_name, reports_with_both,
               n_drug, n_reaction, prr, ror, ror_lower_95, chi_squared, is_signal
        FROM agg_disproportionality
        WHERE is_signal = TRUE
        """
        if drug_name:
            sql = base + " AND drug_name = %s ORDER BY ror_lower_95 DESC LIMIT %s"
            return self.query(sql, [drug_name, limit])
        sql = base + " ORDER BY ror_lower_95 DESC LIMIT %s"
        return self.query(sql, [limit])

    def get_demographics(self, drug_name: str) -> Optional[pd.DataFrame]:
        sql = """
        SELECT
            patient_age_group,
            patient_sex,
            patient_count,
            event_count,
            serious_event_count,
            serious_rate_pct,
            fatal_event_count
        FROM agg_patient_demographics
        WHERE drug_name = %s
        ORDER BY patient_age_group, patient_sex
        """
        return self.query(sql, [drug_name])

    def get_polypharmacy_signals(self, limit: int = 20) -> Optional[pd.DataFrame]:
        sql = """
        SELECT
            drug_1_name,
            drug_2_name,
            co_occurrence_count,
            combined_serious_rate_pct,
            combined_fatal_rate_pct
        FROM agg_polypharmacy_signals
        ORDER BY co_occurrence_count DESC
        LIMIT %s
        """
        return self.query(sql, [limit])