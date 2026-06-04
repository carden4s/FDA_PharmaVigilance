{{ config(
    materialized='table',
    indexes=[{'columns': ['drug_name']}]
) }}

SELECT
  drug_name,
  COUNT(*) as total_events,
  SUM(CASE WHEN is_serious = 1 THEN 1 ELSE 0 END) as serious_events,
  ROUND(100.0 * SUM(CASE WHEN is_serious = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as serious_rate_pct,
  SUM(CASE WHEN is_fatal = 1 THEN 1 ELSE 0 END) as fatal_events,
  ROUND(100.0 * SUM(CASE WHEN is_fatal = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fatal_rate_pct,
  SUM(CASE WHEN is_hospitalized = 1 THEN 1 ELSE 0 END) as hospitalized_events,
  ROUND(100.0 * SUM(CASE WHEN is_hospitalized = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as hospitalization_rate_pct,
  SUM(CASE WHEN is_life_threatening = 1 THEN 1 ELSE 0 END) as life_threatening_events,
  ROUND(100.0 * SUM(CASE WHEN is_life_threatening = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as life_threatening_rate_pct,
  SUM(CASE WHEN is_disability = 1 THEN 1 ELSE 0 END) as disability_events,
  ROUND(100.0 * SUM(CASE WHEN is_disability = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as disability_rate_pct,
  COUNT(DISTINCT report_id) as approx_unique_patients,
  MIN(event_date) as date_first_event,
  MAX(event_date) as date_last_event,
  DATEDIFF(day, MIN(event_date), MAX(event_date)) as event_date_range_days,
  CURRENT_TIMESTAMP() as updated_at

FROM {{ ref('stg_fda_adverse_events') }}

WHERE drug_name IS NOT NULL

GROUP BY drug_name
