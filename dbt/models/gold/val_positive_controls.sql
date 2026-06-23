-- Validation: positive controls vs disproportionality results (face validity)

{{ config(materialized='table') }}

-- Joins the auditable positive-control seed (documented FDA associations) to the
-- disproportionality results. If the pipeline is sound, these known pairs should
-- be flagged as signals. This is the face-validity evidence for the thesis.
SELECT
    pc.drug_name,
    pc.reaction_name,
    pc.expected_signal,
    pc.source,
    d.reports_with_both                          AS a,
    d.prr,
    d.prr_lower_95,
    d.prr_upper_95,
    d.ror,
    d.ror_lower_95,
    d.ror_upper_95,
    d.chi_squared,
    d.prr_signal,
    d.ror_signal,
    d.signal_flag,
    COALESCE(d.signal_flag, FALSE)               AS detected,
    CASE
        WHEN d.drug_name IS NULL THEN 'Not in results (below thresholds or not ingested)'
        WHEN d.signal_flag      THEN 'Detected as consensus signal'
        WHEN d.prr_signal OR d.ror_signal THEN 'Partial: one criterion met'
        ELSE 'Present but below signal threshold (see limitations: class dilution)'
    END                                          AS validation_note,
    CURRENT_TIMESTAMP()                          AS updated_at
FROM {{ ref('positive_controls') }} pc
LEFT JOIN {{ ref('agg_disproportionality') }} d
    ON d.drug_name = pc.drug_name
   AND d.reaction_name = pc.reaction_name