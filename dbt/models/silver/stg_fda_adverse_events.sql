-- Silver: cleaned/standardized FDA adverse events (normalized drug names + age-in-years)
-- Co-authored with CoCo
{{ config(
    materialized='incremental',
    unique_key='event_id',
    incremental_strategy='merge'
) }}

WITH src AS (

  SELECT
    *,
    -- Convert openFDA age unit codes (800=decade .. 805=hour) to YEARS.
    -- Legacy/sample rows without a unit are assumed to already be in years.
    CASE
      WHEN patient_onsetage IS NULL THEN NULL
      WHEN patient_onsetage_unit = 800 THEN patient_onsetage * 10            -- decade
      WHEN patient_onsetage_unit = 801 THEN patient_onsetage                 -- year
      WHEN patient_onsetage_unit = 802 THEN patient_onsetage / 12.0          -- month
      WHEN patient_onsetage_unit = 803 THEN patient_onsetage / 52.0          -- week
      WHEN patient_onsetage_unit = 804 THEN patient_onsetage / 365.0         -- day
      WHEN patient_onsetage_unit = 805 THEN patient_onsetage / 8760.0        -- hour
      WHEN patient_onsetage_unit IS NULL THEN patient_onsetage               -- assume years
      ELSE NULL
    END as patient_age_years
  FROM {{ source('bronze', 'raw_fda_adverse_events') }}

  WHERE safetyreportid IS NOT NULL
    AND drug_name IS NOT NULL
    AND TRY_TO_DATE(received_date, 'YYYYMMDD') >= DATEADD(year, -3, CURRENT_DATE)

  {% if is_incremental() %}
    AND loaded_at > (SELECT COALESCE(MAX(loaded_at), '1900-01-01'::timestamp) FROM {{ this }})
  {% endif %}

  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY safetyreportid, drug_name, reaction_name
    ORDER BY loaded_at DESC
  ) = 1

),

cleaned AS (

  SELECT
    -- event_id stays hashed on the RAW bronze drug name so existing keys are stable
    MD5(CONCAT_WS('||',
      CAST(safetyreportid AS VARCHAR),
      CAST(drug_name AS VARCHAR),
      COALESCE(CAST(reaction_name AS VARCHAR), 'NO_REACTION')
    )) as event_id,
    safetyreportid as report_id,
    report_type,

    -- Seriousness flags
    COALESCE(serious, 0) as serious,
    COALESCE(seriousness_death, 0) as is_fatal,
    COALESCE(seriousness_hospitalization, 0) as is_hospitalized,
    COALESCE(seriousness_lifethreatening, 0) as is_life_threatening,
    COALESCE(seriousness_disability, 0) as is_disability,

    -- Patient demographics (age normalized to years; implausible ages -> NULL/Unknown)
    CASE WHEN patient_age_years > 0 AND patient_age_years <= 150
         THEN ROUND(patient_age_years, 1) END as patient_age,
    CASE
      WHEN patient_age_years IS NULL OR patient_age_years <= 0 OR patient_age_years > 150 THEN 'Unknown'
      WHEN patient_age_years < 18 THEN '0-18'
      WHEN patient_age_years < 40 THEN '19-40'
      WHEN patient_age_years < 60 THEN '41-60'
      ELSE '60+'
    END as patient_age_group,
    
    CASE
      WHEN patient_sex = 1 THEN 'Male'
      WHEN patient_sex = 2 THEN 'Female'
      ELSE 'Unknown'
    END as patient_sex,
    TRY_TO_DECIMAL(patient_weight, 10, 2) as patient_weight_kg,

    -- Drug information: keep raw (upper/trim) for traceability + a cleaned key for canonical lookup
    UPPER(TRIM(drug_name)) as drug_name_raw,
    {{ normalize_drug_name('drug_name') }} as drug_name_clean,
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

  FROM src

)

SELECT
  cleaned.* EXCLUDE (drug_name_clean),
  -- canonical name: seed override (brand->generic), else cleaned name,
  -- else raw name when cleaning stripped everything (e.g. "ER", "ORAL", "SR")
  COALESCE(syn.canonical_name, NULLIF(cleaned.drug_name_clean, ''), cleaned.drug_name_raw) as drug_name
FROM cleaned
LEFT JOIN {{ ref('drug_synonyms') }} syn
  ON cleaned.drug_name_clean = syn.drug_name_variant