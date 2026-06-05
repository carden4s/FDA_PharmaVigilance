{{ config(materialized='table') }}

SELECT
  MD5(CAST(event_id AS VARCHAR)) as fact_id,
  event_id,
  drug_name,
  reaction_name,
  patient_age_group,
  patient_sex,
  reaction_outcome,
  TO_DECIMAL(TO_CHAR(event_date, 'YYYYMMDD'), 8) as event_date_key,
  serious as is_serious,
  is_fatal,
  1 as event_count,
  CURRENT_TIMESTAMP() as loaded_at

FROM {{ ref('stg_fda_adverse_events') }}
