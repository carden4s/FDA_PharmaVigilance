{{ config(materialized='table') }}

WITH drug_pairs AS (
  SELECT
    LEAST(a.drug_name, b.drug_name) as drug_1_name,
    GREATEST(a.drug_name, b.drug_name) as drug_2_name,
    a.report_id,
    a.serious as is_serious,
    a.is_fatal,
    a.reaction_name
  
  FROM {{ ref('stg_fda_adverse_events') }} a
  
  INNER JOIN {{ ref('stg_fda_adverse_events') }} b
    ON a.report_id = b.report_id
    AND a.drug_name < b.drug_name
  
  WHERE a.drug_name IS NOT NULL
    AND b.drug_name IS NOT NULL
)

SELECT
  drug_1_name,
  drug_2_name,
  COUNT(DISTINCT report_id) as co_occurrence_count,
  ROUND(100.0 * SUM(CASE WHEN is_serious = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as combined_serious_rate_pct,
  ROUND(100.0 * SUM(CASE WHEN is_fatal = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as combined_fatal_rate_pct,
  MODE(reaction_name) as most_common_reaction,
  COUNT(DISTINCT reaction_name) as unique_reaction_combinations,
  CURRENT_TIMESTAMP() as updated_at

FROM drug_pairs

GROUP BY drug_1_name, drug_2_name
