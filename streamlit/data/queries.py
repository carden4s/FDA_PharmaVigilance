"""SQL queries for Streamlit dashboard"""


QUERY_DRUGS = """
SELECT DISTINCT drug_name 
FROM agg_drug_safety_profile 
ORDER BY drug_name
"""

QUERY_DRUG_PROFILE = """
SELECT 
    drug_name,
    total_events,
    serious_events,
    serious_rate_pct,
    fatal_events,
    fatal_rate_pct,
    approx_unique_patients
FROM agg_drug_safety_profile
WHERE drug_name = '{drug_name}'
"""

QUERY_TOP_REACTIONS = """
SELECT 
    reaction_name,
    reaction_count,
    reaction_frequency_pct,
    serious_reaction_count
FROM agg_reaction_frequency
WHERE drug_name = '{drug_name}'
ORDER BY reaction_count DESC
LIMIT {limit}
"""

QUERY_DEMOGRAPHICS = """
SELECT 
    patient_age_group,
    patient_sex,
    patient_count,
    serious_rate_pct
FROM agg_patient_demographics
WHERE drug_name = '{drug_name}'
ORDER BY patient_age_group
"""

QUERY_POLYPHARMACY = """
SELECT 
    drug_1_name,
    drug_2_name,
    co_occurrence_count,
    combined_serious_rate_pct
FROM agg_polypharmacy_signals
ORDER BY co_occurrence_count DESC
LIMIT {limit}
"""
