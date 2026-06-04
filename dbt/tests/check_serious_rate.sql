-- Check for serious rates over 100%
SELECT *
FROM {{ ref('agg_drug_safety_profile') }}
WHERE serious_rate_pct > 100 OR serious_rate_pct < 0
