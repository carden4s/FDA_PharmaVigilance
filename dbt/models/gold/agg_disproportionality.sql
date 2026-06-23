-- Gold: rigorous PRR/ROR disproportionality with 95% CIs and signal criteria (monitored cohort)

{{ config(materialized='table') }}

-- ============================================================================
-- DISPROPORTIONALITY ANALYSIS (pharmacovigilance signal detection)
-- For each drug-reaction pair we build the 2x2 contingency table:
--
--                    reaction +        reaction -
--   drug +              a                  b           (a+b = n_drug)
--   drug -              c                  d           (c+d = n_total - n_drug)
--
--   a = reports with drug AND reaction      (reports_with_both)
--   b = reports with drug, without reaction = n_drug - a
--   c = reports without drug, with reaction = n_reaction - a
--   d = reports with neither                = n_total - n_drug - c
--
-- PRR = [a/(a+b)] / [c/(c+d)]      (Proportional Reporting Ratio)
-- ROR = (a*d) / (b*c)              (Reporting Odds Ratio)
-- 95% CIs use the ln-based standard error (Rothman):
--   SE(ln ROR) = sqrt(1/a + 1/b + 1/c + 1/d)
--   SE(ln PRR) = sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d))
-- chi-squared (Pearson, no Yates) = n*(ad-bc)^2 / [(a+b)(c+d)(a+c)(b+d)]
-- A Haldane-Anscombe 0.5 continuity correction is applied throughout to avoid
-- division by zero and stabilise sparse cells.
--
-- Background (n_total, n_drug, n_reaction) is computed over ALL ingested reports
-- so the comparator is "this drug vs every other reported drug". We only OUTPUT
-- rows for the monitored cohort (see seed monitored_drugs) to keep the results
-- interpretable; the statistical background is unaffected.
-- LIMITATION: the comparator is the ~100 ingested drugs, not all of FAERS.
-- ============================================================================

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
    FROM dr_pairs GROUP BY 1, 2 HAVING COUNT(*) >= 3      -- a >= 3 required by both criteria
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
        ac.a                                            AS reports_with_both,   -- a
        (dt.n_drug - ac.a)                              AS b,                    -- b
        (rt.n_reaction - ac.a)                          AS c,                    -- c
        (t.n - dt.n_drug - (rt.n_reaction - ac.a))      AS d,                    -- d
        dt.n_drug,
        rt.n_reaction,
        t.n                                             AS n_total,
        -- PRR = [a/(a+b)] / [c/(c+d)]  (Haldane +0.5)
        ROUND(
            ((ac.a + 0.5) / ((ac.a + 0.5) + ((dt.n_drug - ac.a) + 0.5))) /
            (((rt.n_reaction - ac.a) + 0.5) / (((rt.n_reaction - ac.a) + 0.5) + ((t.n - dt.n_drug - (rt.n_reaction - ac.a)) + 0.5)))
        , 3) AS prr,
        -- ROR = (a*d)/(b*c)  (Haldane +0.5)
        ROUND(
            ((ac.a + 0.5) * ((t.n - dt.n_drug - (rt.n_reaction - ac.a)) + 0.5)) /
            (((dt.n_drug - ac.a) + 0.5) * ((rt.n_reaction - ac.a) + 0.5))
        , 3) AS ror,
        -- chi-squared (Pearson, no Yates)
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
),
stats AS (
    SELECT
        calc.*,
        -- ROR 95% CI: exp( ln(ROR) +/- 1.96 * sqrt(1/a + 1/b + 1/c + 1/d) )
        ROUND(EXP(LN(ror) - 1.96 * SQRT(1.0/(reports_with_both + 0.5) + 1.0/(b + 0.5) + 1.0/(c + 0.5) + 1.0/(d + 0.5))), 3) AS ror_lower_95,
        ROUND(EXP(LN(ror) + 1.96 * SQRT(1.0/(reports_with_both + 0.5) + 1.0/(b + 0.5) + 1.0/(c + 0.5) + 1.0/(d + 0.5))), 3) AS ror_upper_95,
        -- PRR 95% CI: exp( ln(PRR) +/- 1.96 * sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d)) )
        --   a+b = n_drug ; c+d = n_total - n_drug
        ROUND(EXP(LN(prr) - 1.96 * SQRT(1.0/(reports_with_both + 0.5) - 1.0/(n_drug + 0.5) + 1.0/(c + 0.5) - 1.0/((n_total - n_drug) + 0.5))), 3) AS prr_lower_95,
        ROUND(EXP(LN(prr) + 1.96 * SQRT(1.0/(reports_with_both + 0.5) - 1.0/(n_drug + 0.5) + 1.0/(c + 0.5) - 1.0/((n_total - n_drug) + 0.5))), 3) AS prr_upper_95
    FROM calc
)
SELECT
    stats.*,
    -- Evans (2001) PRR criterion: PRR >= 2 AND chi2 >= 4 AND a >= 3
    (prr >= 2 AND chi_squared >= 4 AND reports_with_both >= 3)                  AS prr_signal,
    -- ROR criterion: lower bound of 95% CI > 1 AND a >= 3
    (ror_lower_95 > 1 AND reports_with_both >= 3)                               AS ror_signal,
    -- Conservative consensus signal (both criteria must agree)
    ((prr >= 2 AND chi_squared >= 4 AND reports_with_both >= 3)
        AND (ror_lower_95 > 1 AND reports_with_both >= 3))                      AS signal_flag,
    -- Alias kept for the dashboard; points at the conservative consensus flag
    ((prr >= 2 AND chi_squared >= 4 AND reports_with_both >= 3)
        AND (ror_lower_95 > 1 AND reports_with_both >= 3))                      AS is_signal,
    CURRENT_TIMESTAMP() AS updated_at
FROM stats