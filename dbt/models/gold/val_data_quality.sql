-- Data-quality metrics across layers for the thesis limitations chapter

{{ config(materialized='table') }}

-- One row per metric: counts, null/Unknown rates, dedup rate, and date coverage.
-- Numeric metrics use VALUE / VALUE_PCT; non-numeric (dates) use DETAIL.

SELECT 'bronze_rows'              AS metric, 'bronze' AS scope,
       COUNT(*)::FLOAT            AS value,  NULL::FLOAT AS value_pct, NULL::VARCHAR AS detail
FROM {{ source('bronze', 'raw_fda_adverse_events') }}

UNION ALL
SELECT 'silver_rows', 'silver', COUNT(*)::FLOAT, NULL, NULL
FROM {{ ref('stg_fda_adverse_events') }}
UNION ALL
SELECT 'silver_distinct_reports', 'silver', COUNT(DISTINCT report_id)::FLOAT, NULL, NULL
FROM {{ ref('stg_fda_adverse_events') }}
UNION ALL
SELECT 'silver_distinct_drugs', 'silver', COUNT(DISTINCT drug_name)::FLOAT, NULL, NULL
FROM {{ ref('stg_fda_adverse_events') }}
UNION ALL
SELECT 'silver_distinct_reactions', 'silver', COUNT(DISTINCT reaction_name)::FLOAT, NULL, NULL
FROM {{ ref('stg_fda_adverse_events') }}

UNION ALL
SELECT 'pct_patient_sex_unknown', 'silver',
       SUM(CASE WHEN patient_sex = 'Unknown' THEN 1 ELSE 0 END)::FLOAT,
       ROUND(100.0 * SUM(CASE WHEN patient_sex = 'Unknown' THEN 1 ELSE 0 END) / COUNT(*), 2), NULL
FROM {{ ref('stg_fda_adverse_events') }}
UNION ALL
SELECT 'pct_patient_age_null', 'silver',
       SUM(CASE WHEN patient_age IS NULL THEN 1 ELSE 0 END)::FLOAT,
       ROUND(100.0 * SUM(CASE WHEN patient_age IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2), NULL
FROM {{ ref('stg_fda_adverse_events') }}
UNION ALL
SELECT 'pct_reaction_name_null', 'silver',
       SUM(CASE WHEN reaction_name IS NULL THEN 1 ELSE 0 END)::FLOAT,
       ROUND(100.0 * SUM(CASE WHEN reaction_name IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2), NULL
FROM {{ ref('stg_fda_adverse_events') }}

UNION ALL
SELECT 'event_id_duplicate_rate', 'silver',
       (COUNT(*) - COUNT(DISTINCT event_id))::FLOAT,
       ROUND(100.0 * (COUNT(*) - COUNT(DISTINCT event_id)) / COUNT(*), 4), NULL
FROM {{ ref('stg_fda_adverse_events') }}

UNION ALL
SELECT 'received_date_min', 'silver', NULL, NULL, TO_VARCHAR(MIN(received_date))
FROM {{ ref('stg_fda_adverse_events') }}
UNION ALL
SELECT 'received_date_max', 'silver', NULL, NULL, TO_VARCHAR(MAX(received_date))
FROM {{ ref('stg_fda_adverse_events') }}