-- Gold: PRR/ROR/chi-squared disproportionality signals, restricted to the monitored drug cohort
-- Co-authored with CoCo
{{ config(materialized='table') }}

-- Background (n_total, n_drug, n_reaction) is computed over ALL ingested reports so the
-- comparator is "this drug vs every other drug". We only OUTPUT rows for monitored drugs,
-- which removes one-off co-suspect noise (e.g. PARAGARD, DOVONEX) while keeping the stats valid.
-- NOTE: background is limited to the ~40 ingested drugs, not all of FAERS (see AGENTS.md).

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
),
calc AS (
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
        -- Chi-squared (Pearson, no Yates); high values = stronger evidence
        ROUND(
            (t.n * POWER((ac.a * (t.n - dt.n_drug - (rt.n_reaction - ac.a))) - ((dt.n_drug - ac.a) * (rt.n_reaction - ac.a)), 2))
            / (dt.n_drug * (t.n - dt.n_drug) * rt.n_reaction * (t.n - rt.n_reaction))
        , 2) AS chi_squared
    FROM a_counts ac
    JOIN drug_tot dt     ON ac.drug_name = dt.drug_name
    JOIN reaction_tot rt ON ac.reaction_name = rt.reaction_name
    CROSS JOIN n_total t
    WHERE ac.drug_name IN (SELECT drug_name FROM {{ ref('monitored_drugs') }})
      AND dt.n_drug >= 50          -- drug needs a real report base
      AND rt.n_reaction >= 5       -- drop one-off reactions
)
SELECT
    calc.*,
    -- Lower bound of the 95% CI for ROR (Haldane); rank real signals by this, not raw ROR
    ROUND(
        EXP(LN(ror) - 1.96 * SQRT(1.0/(reports_with_both + 0.5) + 1.0/(b + 0.5) + 1.0/(c + 0.5) + 1.0/(d + 0.5)))
    , 3) AS ror_lower_95,
    -- EMA signal-of-disproportionate-reporting criteria
    (prr >= 2 AND chi_squared >= 4 AND reports_with_both >= 3) AS is_signal,
    CURRENT_TIMESTAMP() AS updated_at
FROM calc