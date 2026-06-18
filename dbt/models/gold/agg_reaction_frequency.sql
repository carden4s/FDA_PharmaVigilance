-- Gold: top reactions per monitored drug (excludes administrative MedDRA terms)

{{ config(materialized='table') }}

SELECT
  drug_name,
  reaction_name,
  COUNT(*) as reaction_count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY drug_name), 2) as reaction_frequency_pct,
  ROW_NUMBER() OVER (PARTITION BY drug_name ORDER BY COUNT(*) DESC) as rank_within_drug,
  MAX(event_date) as last_observed_date,
  SUM(CASE WHEN serious = 1 THEN 1 ELSE 0 END) as serious_reaction_count,
  SUM(CASE WHEN is_fatal = 1 THEN 1 ELSE 0 END) as fatal_reaction_count,
  CURRENT_TIMESTAMP() as updated_at

FROM {{ ref('stg_fda_adverse_events') }}

WHERE drug_name IS NOT NULL
  AND reaction_name IS NOT NULL
  AND drug_name IN (SELECT drug_name FROM {{ ref('monitored_drugs') }})
  AND reaction_name NOT IN (
    'OFF LABEL USE',
    'PRODUCT USE ISSUE',
    'PRODUCT USE IN UNAPPROVED INDICATION',
    'DRUG USE FOR UNKNOWN INDICATION',
    'NO ADVERSE EVENT',
    'INCORRECT DOSE ADMINISTERED',
    'PRODUCT DOSE OMISSION ISSUE'
  )

GROUP BY drug_name, reaction_name