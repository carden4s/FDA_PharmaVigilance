{{ config(materialized='table') }}

WITH dr_pairs AS (
    SELECT DISTINCT report_id, drug_name, reaction_name
    FROM {{ ref('stg_fda_adverse_events') }}
    WHERE drug_name IS NOT NULL AND reaction_name IS NOT NULL
),
drug_reports AS (
    SELECT DISTINCT report_id, drug_name
    FROM {{ ref('stg_fda_adverse_events') }}
    WHERE drug_name IS NOT NULL
),
reaction_reports AS (
    SELECT DISTINCT report_id, reaction_name
    FROM {{ ref('stg_fda_adverse_events') }}
    WHERE reaction_name IS NOT NULL
),
n_total AS (
    SELECT COUNT(DISTINCT report_id) AS n FROM {{ ref('stg_fda_adverse_events') }}
),
a_counts AS (
    SELECT drug_name, reaction_name, COUNT(*) AS a
    FROM dr_pairs GROUP BY 1, 2 HAVING COUNT(*) >= 3
),
drug_tot AS (
    SELECT drug_name, COUNT(*) AS n_drug FROM drug_reports GROUP BY 1
),
reaction_tot AS (
    SELECT reaction_name, COUNT(*) AS n_reaction FROM reaction_reports GROUP BY 1
)
SELECT
    ac.drug_name,
    ac.reaction_name,
    ac.a                                            AS reports_with_both,
    (dt.n_drug - ac.a)                              AS b,
    (rt.n_reaction - ac.a)                          AS c,
    (t.n - dt.n_drug - (rt.n_reaction - ac.a))      AS d,
    dt.n_drug,
    rt.n_reaction,
    t.n                                             AS n_total,
    ROUND(
        ((ac.a + 0.5) / ((ac.a + 0.5) + ((dt.n_drug - ac.a) + 0.5))) /
        (((rt.n_reaction - ac.a) + 0.5) / (((rt.n_reaction - ac.a) + 0.5) + ((t.n - dt.n_drug - (rt.n_reaction - ac.a)) + 0.5)))
    , 3) AS prr,
    ROUND(
        ((ac.a + 0.5) * ((t.n - dt.n_drug - (rt.n_reaction - ac.a)) + 0.5)) /
        (((dt.n_drug - ac.a) + 0.5) * ((rt.n_reaction - ac.a) + 0.5))
    , 3) AS ror,
    -- Chi-squared (Yates not applied); high values = stronger evidence
    ROUND(
        (t.n * POWER((ac.a * (t.n - dt.n_drug - (rt.n_reaction - ac.a))) - ((dt.n_drug - ac.a) * (rt.n_reaction - ac.a)), 2))
        / (dt.n_drug * (t.n - dt.n_drug) * rt.n_reaction * (t.n - rt.n_reaction))
    , 2) AS chi_squared,
    CURRENT_TIMESTAMP() AS updated_at
FROM a_counts ac
JOIN drug_tot dt     ON ac.drug_name = dt.drug_name
JOIN reaction_tot rt ON ac.reaction_name = rt.reaction_name
CROSS JOIN n_total t
WHERE dt.n_drug >= 50          -- only assess drugs with a real report base (drops 5-report curiosities)
  AND rt.n_reaction >= 5       -- drop one-off reactions