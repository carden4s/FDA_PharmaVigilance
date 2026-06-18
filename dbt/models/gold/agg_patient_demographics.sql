-- Gold: age/sex demographic breakdown per monitored drug (min report base to avoid N=1 noise)

{{ config(materialized='table') }}

SELECT
  drug_name,
  patient_age_group,
  patient_sex,
  COUNT(DISTINCT report_id) as patient_count,
  COUNT(*) as event_count,
  SUM(CASE WHEN serious = 1 THEN 1 ELSE 0 END) as serious_event_count,
  ROUND(100.0 * SUM(CASE WHEN serious = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as serious_rate_pct,
  SUM(CASE WHEN is_fatal = 1 THEN 1 ELSE 0 END) as fatal_event_count,
  ROUND(100.0 * SUM(CASE WHEN is_fatal = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fatal_rate_pct,
  ROUND(AVG(patient_age), 1) as avg_patient_age,
  CURRENT_TIMESTAMP() as updated_at

FROM {{ ref('stg_fda_adverse_events') }}

WHERE drug_name IS NOT NULL
  AND patient_age_group IS NOT NULL
  AND drug_name IN (SELECT drug_name FROM {{ ref('monitored_drugs') }})

GROUP BY drug_name, patient_age_group, patient_sex
HAVING COUNT(DISTINCT report_id) >= 10