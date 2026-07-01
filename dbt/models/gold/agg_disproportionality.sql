-- Gold: PRR/ROR/chi-squared disproportionality, SUSPECT drug only + non-ADR term filter (monitored cohort)

{{ config(materialized='table') }}

WITH susp AS (                       -- report x drug where the drug is the SUSPECT
    SELECT DISTINCT report_id, drug_name
    FROM {{ ref('stg_fda_adverse_events') }}
    WHERE drug_name IS NOT NULL AND is_suspect = 1
),
universe AS (                        -- reports that contain at least one suspect drug
    SELECT DISTINCT report_id FROM susp
),
rxn AS (                             -- reactions within the universe, non-ADR terms excluded
    SELECT DISTINCT s.report_id, s.reaction_name
    FROM {{ ref('stg_fda_adverse_events') }} s
    JOIN universe u ON s.report_id = u.report_id
    WHERE s.reaction_name IS NOT NULL
      AND s.reaction_name NOT IN (
        'OFF LABEL USE', 'PRODUCT USE ISSUE', 'PRODUCT USE IN UNAPPROVED INDICATION',
        'DRUG USE FOR UNKNOWN INDICATION', 'NO ADVERSE EVENT', 'INCORRECT DOSE ADMINISTERED',
        'PRODUCT DOSE OMISSION ISSUE', 'INTENTIONAL PRODUCT USE ISSUE',
        'ANTICOAGULATION DRUG LEVEL ABOVE THERAPEUTIC', 'ANTICOAGULATION DRUG LEVEL BELOW THERAPEUTIC',
        'DRUG LEVEL ABOVE THERAPEUTIC', 'DRUG LEVEL BELOW THERAPEUTIC',
        'INTERNATIONAL NORMALISED RATIO INCREASED', 'INTERNATIONAL NORMALISED RATIO ABNORMAL',
        'X-RAY ABNORMAL', 'ANTI-CYCLIC CITRULLINATED PEPTIDE ANTIBODY POSITIVE', 'CONGENITAL ANOMALY'
      )
            -- Laboratory / measurement results are never clinical reactions -> exclude by pattern.
      -- (Disease/indication terms and real ADRs are NOT excluded; see docs/LIMITATIONS.md.)
      AND NOT (
        s.reaction_name ILIKE '%TEST ABNORMAL'
        OR s.reaction_name ILIKE '%FACTOR POSITIVE'
        OR s.reaction_name ILIKE 'C-REACTIVE PROTEIN%'
        OR s.reaction_name ILIKE '%SEDIMENTATION RATE%'
        OR s.reaction_name ILIKE '%JOINT COUNT INCREASED%'
      )

),
n_total AS (
    SELECT COUNT(*) AS n FROM universe
),
a_counts AS (
    SELECT d.drug_name, r.reaction_name, COUNT(DISTINCT d.report_id) AS a
    FROM susp d
    JOIN rxn r ON d.report_id = r.report_id
    GROUP BY 1, 2 HAVING COUNT(DISTINCT d.report_id) >= 3
),
drug_tot AS (
    SELECT drug_name, COUNT(DISTINCT report_id) AS n_drug FROM susp GROUP BY 1
),
reaction_tot AS (
    SELECT reaction_name, COUNT(DISTINCT report_id) AS n_reaction FROM rxn GROUP BY 1
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
        ROUND(
            (t.n * POWER((ac.a * (t.n - dt.n_drug - (rt.n_reaction - ac.a))) - ((dt.n_drug - ac.a) * (rt.n_reaction - ac.a)), 2))
            / (dt.n_drug * (t.n - dt.n_drug) * rt.n_reaction * (t.n - rt.n_reaction))
        , 2) AS chi_squared
    FROM a_counts ac
    JOIN drug_tot dt     ON ac.drug_name = dt.drug_name
    JOIN reaction_tot rt ON ac.reaction_name = rt.reaction_name
    CROSS JOIN n_total t
    WHERE ac.drug_name IN (SELECT drug_name FROM {{ ref('monitored_drugs') }})
      AND dt.n_drug >= 50
      AND rt.n_reaction >= 5
),
stats AS (
    SELECT
        calc.*,
        ROUND(EXP(LN(ror) - 1.96 * SQRT(1.0/(reports_with_both + 0.5) + 1.0/(b + 0.5) + 1.0/(c + 0.5) + 1.0/(d + 0.5))), 3) AS ror_lower_95,
        ROUND(EXP(LN(ror) + 1.96 * SQRT(1.0/(reports_with_both + 0.5) + 1.0/(b + 0.5) + 1.0/(c + 0.5) + 1.0/(d + 0.5))), 3) AS ror_upper_95,
        ROUND(EXP(LN(prr) - 1.96 * SQRT(1.0/(reports_with_both + 0.5) - 1.0/(n_drug + 0.5) + 1.0/(c + 0.5) - 1.0/((n_total - n_drug) + 0.5))), 3) AS prr_lower_95,
        ROUND(EXP(LN(prr) + 1.96 * SQRT(1.0/(reports_with_both + 0.5) - 1.0/(n_drug + 0.5) + 1.0/(c + 0.5) - 1.0/((n_total - n_drug) + 0.5))), 3) AS prr_upper_95
    FROM calc
)
SELECT
    stats.*,
    (prr >= 2 AND chi_squared >= 4 AND reports_with_both >= 3)                  AS prr_signal,
    (ror_lower_95 > 1 AND reports_with_both >= 3)                               AS ror_signal,
    ((prr >= 2 AND chi_squared >= 4 AND reports_with_both >= 3)
        AND (ror_lower_95 > 1 AND reports_with_both >= 3))                      AS signal_flag,
    ((prr >= 2 AND chi_squared >= 4 AND reports_with_both >= 3)
        AND (ror_lower_95 > 1 AND reports_with_both >= 3))                      AS is_signal,
    CURRENT_TIMESTAMP() AS updated_at
FROM stats