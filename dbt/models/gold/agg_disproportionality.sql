{{ config(materialized='table') }}

-- Disproportionality analysis: PRR & ROR per drug-reaction pair
-- 2x2 table at the report level:
--   a = reports with drug AND reaction
--   b = reports with drug, without reaction
--   c = reports without drug, with reaction
--   d = reports with neither
WITH base AS (
    SELECT DISTINCT report_id, drug_name, reaction_name
    FROM {{ ref('stg_fda_adverse_events') }}
    WHERE drug_name IS NOT NULL
      AND reaction_name IS NOT NULL
),
totals AS (
    SELECT COUNT(DISTINCT report_id) AS n_total FROM base
),
drug_reaction AS (
    SELECT drug_name, reaction_name, COUNT(DISTINCT report_id) AS a
    FROM base GROUP BY 1, 2
),
drug_tot AS (
    SELECT drug_name, COUNT(DISTINCT report_id) AS n_drug
    FROM base GROUP BY 1
),
reaction_tot AS (
    SELECT reaction_name, COUNT(DISTINCT report_id) AS n_reaction
    FROM base GROUP BY 1
)
SELECT
    dr.drug_name,
    dr.reaction_name,
    dr.a                                            AS reports_with_both,
    (dt.n_drug - dr.a)                              AS b,
    (rt.n_reaction - dr.a)                          AS c,
    (t.n_total - dt.n_drug - (rt.n_reaction - dr.a)) AS d,
    dt.n_drug,
    rt.n_reaction,
    t.n_total,
    ROUND(
        (dr.a::FLOAT / NULLIF(dt.n_drug, 0)) /
        NULLIF((rt.n_reaction - dr.a)::FLOAT / NULLIF(t.n_total - dt.n_drug, 0), 0)
    , 3) AS prr,
    ROUND(
        (dr.a::FLOAT * (t.n_total - dt.n_drug - (rt.n_reaction - dr.a))) /
        NULLIF((dt.n_drug - dr.a)::FLOAT * (rt.n_reaction - dr.a), 0)
    , 3) AS ror,
    CURRENT_TIMESTAMP() AS updated_at
FROM drug_reaction dr
JOIN drug_tot dt      ON dr.drug_name = dt.drug_name
JOIN reaction_tot rt  ON dr.reaction_name = rt.reaction_name
CROSS JOIN totals t
WHERE dr.a >= 3   -- minimum cell count for signal stability