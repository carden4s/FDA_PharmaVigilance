{# Co-authored with CoCo #}
{#
  normalize_drug_name(column)
  Regex-cleans a raw openFDA medicinalproduct string so brand/dosage noise
  collapses to a comparable base name. Brand->generic overrides are applied
  separately via the drug_synonyms seed (LEFT JOIN in the silver model).
  Steps: uppercase/trim -> drop parentheticals -> drop dosage tokens
  (e.g. 81MG, 10 MG) -> drop common form/route words -> strip punctuation
  -> collapse whitespace.
#}
{% macro normalize_drug_name(column) %}
  TRIM(
    REGEXP_REPLACE(
      REGEXP_REPLACE(
        REGEXP_REPLACE(
          REGEXP_REPLACE(
            REGEXP_REPLACE(
              UPPER(TRIM({{ column }})),
              '\\(.*?\\)', ' '
            ),
            '\\b[0-9]+(\\.[0-9]+)?\\s*(MG|MCG|G|ML|IU|%|UNITS?)\\b', ' '
          ),
          '\\b(TABLET|TABLETS|CAPSULE|CAPSULES|EC|XR|ER|SR|CR|DR|ODT|ORAL|SOLUTION|SUSPENSION|INJECTION|EXTENDED RELEASE|DELAYED RELEASE)\\b', ' '
        ),
        '[^A-Z0-9 ]', ' '
      ),
      '\\s+', ' '
    )
  )
{% endmacro %}