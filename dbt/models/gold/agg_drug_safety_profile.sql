-- Gold: per-drug safety profile with REPORT-level rates (monitored cohort, min 30 reports)
-- Co-authored with CoCo
{{ config(materialized='table') }}

-- Collapse to one row per report first, so multi-reaction reports don't inflate rates
-- (a single report with 54 reactions previously counted as 54 "events").
-- NOTE: openFDA seriousness fields are coded 1=yes, 2=no (not 0/1), so EVERY flag must be
-- compared to = 1 before aggregating, or rates exceed 100%.
WITH report_level AS (
  SELECT
    drug_name,
    report_id,
    MAX(CASE WHEN serious = 1             THEN 1 ELSE 0 END)  AS is_serious,
    MAX(CASE WHEN is_fatal = 1            THEN 1 ELSE 0 END)  AS is_fatal,
    MAX(CASE WHEN is_hospitalized = 1     THEN 1 ELSE 0 END)  AS is_hospitalized,
    MAX(CASE WHEN is_life_threatening = 1 THEN 1 ELSE 0 END)  AS is_life_threatening,
    MAX(CASE WHEN is_disability = 1       THEN 1 ELSE 0 END)  AS is_disability,
    MAX(patient_age)                                          AS patient_age
  FROM {{ ref('stg_fda_adverse_events') }}
  WHERE drug_name IS NOT NULL
  GROUP BY drug_name, report_id
)

SELECT
  drug_name,
  COUNT(*)                                                       AS total_reports,
  SUM(is_serious)                                                AS serious_reports,
  ROUND(100.0 * SUM(is_serious) / COUNT(*), 2)                   AS serious_rate_pct,
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