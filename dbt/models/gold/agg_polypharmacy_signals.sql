{{ config(materialized='table') }}

-- Collapse to report-level drug sets FIRST (removes the reaction-grain explosion),
-- then self-join only distinct drug pairs per report.
WITH report_drug AS (
    SELECT DISTINCT report_id, drug_name
    FROM {{ ref('stg_fda_adverse_events') }}
    WHERE drug_name IS NOT NULL
),
report_flags AS (
    SELECT report_id,
           MAX(serious)  AS is_serious,
           MAX(is_fatal) AS is_fatal
    FROM {{ ref('stg_fda_adverse_events') }}
    GROUP BY report_id
),
pairs AS (
    SELECT a.report_id,
           a.drug_name AS drug_1_name,
           b.drug_name AS drug_2_name
    FROM report_drug a
    JOIN report_drug b
      ON a.report_id = b.report_id
     AND a.drug_name < b.drug_name      -- unordered, de-duplicated pairs
)
SELECT
    p.drug_1_name,
    p.drug_2_name,
    COUNT(*)                                                              AS co_occurrence_count,
    ROUND(100.0 * SUM(CASE WHEN f.is_serious = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS combined_serious_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN f.is_fatal   = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS combined_fatal_rate_pct,
    CURRENT_TIMESTAMP() AS updated_at
FROM pairs p
JOIN report_flags f ON p.report_id = f.report_id
GROUP BY p.drug_1_name, p.drug_2_name
HAVING COUNT(*) >= 5                      -- prune rare/noise pairs (huge output reduction)