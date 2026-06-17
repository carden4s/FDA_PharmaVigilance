-- Singular test: every silver row must have a usable normalized drug_name
-- Co-authored with CoCo
-- Fails (returns rows) if drug_name is NULL, empty, or still looks like a
-- pure dosage/number token after normalization.
SELECT
    event_id,
    drug_name_raw,
    drug_name
FROM {{ ref('stg_fda_adverse_events') }}
WHERE drug_name IS NULL
   OR TRIM(drug_name) = ''
   OR REGEXP_LIKE(drug_name, '^[0-9 .]+$')