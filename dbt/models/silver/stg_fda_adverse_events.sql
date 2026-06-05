{{ config(
    materialized='incremental',
    unique_key='event_id',
    incremental_strategy='merge'
) }}

SELECT
  MD5(CONCAT(CAST(safetyreportid AS VARCHAR), CAST(drug_name AS VARCHAR), CAST(reaction_name AS VARCHAR))) as event_id,
  safetyreportid as report_id,
  report_type,

  -- Seriousness flags
  COALESCE(serious, 0) as serious,
  COALESCE(seriousness_death, 0) as is_fatal,
  COALESCE(seriousness_hospitalization, 0) as is_hospitalized,
  COALESCE(seriousness_lifethreatening, 0) as is_life_threatening,
  COALESCE(seriousness_disability, 0) as is_disability,

  -- Patient demographics
  NULLIF(TRY_TO_NUMBER(patient_onsetage), 0) as patient_age,
  CASE
    WHEN patient_onsetage < 18 THEN '0-18'
    WHEN patient_onsetage < 40 THEN '19-40'
    WHEN patient_onsetage < 60 THEN '41-60'
    ELSE '60+'
  END as patient_age_group,
  CASE
    WHEN patient_sex = 1 THEN 'Male'
    WHEN patient_sex = 2 THEN 'Female'
    ELSE 'Unknown'
  END as patient_sex,
  TRY_TO_DECIMAL(patient_weight, 10, 2) as patient_weight_kg,

  -- Drug information
  UPPER(TRIM(drug_name)) as drug_name,
  drug_route,
  TRY_TO_DECIMAL(drug_dose_value, 18, 4) as drug_dosage_value,
  drug_dose_unit as drug_dosage_unit,
  drug_indication,

  -- Reaction information
  UPPER(TRIM(reaction_name)) as reaction_name,
  reaction_meddra_pt,
  reaction_meddra_llt,
  CASE
    WHEN reaction_outcome = 1 THEN 'Fatal'
    WHEN reaction_outcome = 2 THEN 'Serious'
    WHEN reaction_outcome = 3 THEN 'Hospitalized'
    WHEN reaction_outcome = 4 THEN 'Disability'
    WHEN reaction_outcome = 5 THEN 'Congenital Anomaly'
    ELSE 'Other'
  END as reaction_outcome,

  -- Dates
  TRY_TO_DATE(event_date, 'YYYYMMDD') as event_date,
  TRY_TO_DATE(report_date, 'YYYYMMDD') as report_date,
  TRY_TO_DATE(received_date, 'YYYYMMDD') as received_date,
  DATEDIFF(day, TRY_TO_DATE(event_date, 'YYYYMMDD'), TRY_TO_DATE(report_date, 'YYYYMMDD')) as days_to_event,

  -- Audit fields
  loaded_at,
  source_drug,
  source_date,
  CURRENT_TIMESTAMP() as dbt_loaded_at

FROM {{ source('bronze', 'raw_fda_adverse_events') }}

WHERE safetyreportid IS NOT NULL
  AND drug_name IS NOT NULL
  -- Rolling 3-year retention anchored on receivedate
  AND TRY_TO_DATE(received_date, 'YYYYMMDD') >= DATEADD(year, -3, CURRENT_DATE)

{% if is_incremental() %}
  -- Only process Bronze rows newer than what we've already pulled
  AND loaded_at > (SELECT COALESCE(MAX(loaded_at), '1900-01-01'::timestamp) FROM {{ this }})
{% endif %}

QUALIFY ROW_NUMBER() OVER (
  PARTITION BY safetyreportid, drug_name, reaction_name
  ORDER BY loaded_at DESC
) = 1