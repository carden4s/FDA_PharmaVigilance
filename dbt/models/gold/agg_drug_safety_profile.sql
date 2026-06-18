-- Gold: per-drug safety profile with REPORT-level rates (monitored cohort, min 30 reports)

{{ config(materialized='table') }}

-- Collapse to one row per report first, so multi-reaction reports don't inflate rates
-- (a single report with 54 reactions previously counted as 54 "events").
WITH report_level AS (
  SELECT
    drug_name,
    report_id,
    MAX(serious)              AS serious,
    MAX(is_fatal)             AS is_fatal,
    MAX(is_hospitalized)      AS is_hospitalized,
    MAX(is_life_threatening)  AS is_life_threatening,
    MAX(is_disability)        AS is_disability,
    MAX(patient_age)          AS patient_age
  FROM {{ ref('stg_fda_adverse_events') }}
  WHERE drug_name IS NOT NULL
  GROUP BY drug_name, report_id
)

SELECT
  drug_name,
  COUNT(*)                                                       AS total_reports,
  SUM(serious)                                                   AS serious_reports,
  ROUND(100.0 * SUM(serious) / COUNT(*), 2)                      AS serious_rate_pct,
  SUM(is_fatal)                                                  AS fatal_reports,
  ROUND(100.0 * SUM(is_fatal) / COUNT(*), 2)                     AS fatal_rate_pct,
  SUM(is_hospitalized)                                           AS hospitalized_reports,
  ROUND(100.0 * SUM(is_hospitalized) / COUNT(*), 2)              AS hospitalization_rate_pct,
  SUM(is_life_threatening)                                       AS life_threatening_reports,
  ROUND(100.0 * SUM(is_life_threatening) / COUNT(*), 2)          AS life_threatening_rate_pct,
  SUM(is_disability)                                             AS disability_reports,
  ROUND(100.0 * SUM(is_disability) / COUNT(*), 2)                AS disability_rate_pct,
  ROUND(AVG(patient_age), 1)                                     AS avg_patient_age,
  CURRENT_TIMESTAMP()                                            AS updated_at

FROM report_level

WHERE drug_name IN (SELECT drug_name FROM {{ ref('monitored_drugs') }})

GROUP BY drug_name
HAVING COUNT(*) >= 30