{{ config(
    materialized='table',
    indexes=[{'columns': ['drug_name', 'patient_age_group']}]
) }}

SELECT
  drug_name,
  patient_age_group,
  patient_sex,
  COUNT(DISTINCT report_id) as patient_count,
  COUNT(*) as event_count,
  SUM(CASE WHEN is_serious = 1 THEN 1 ELSE 0 END) as serious_event_count,
  ROUND(100.0 * SUM(CASE WHEN is_serious = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as serious_rate_pct,
  SUM(CASE WHEN is_fatal = 1 THEN 1 ELSE 0 END) as fatal_event_count,
  ROUND(100.0 * SUM(CASE WHEN is_fatal = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fatal_rate_pct,
  ROUND(AVG(patient_age), 1) as avg_patient_age,
  CURRENT_TIMESTAMP() as updated_at

FROM {{ ref('stg_fda_adverse_events') }}

WHERE drug_name IS NOT NULL
  AND patient_age_group IS NOT NULL

GROUP BY drug_name, patient_age_group, patient_sex
