# dbt Layer - Data Transformation

## Overview

This dbt project transforms raw FDA adverse event data through two layers:

1. **Silver Layer** (stg_*): Cleaning, standardization, and data type conversion
2. **Gold Layer** (fct_* and agg_*): Business-ready fact tables and aggregations

## Project Structure

```
dbt/
├── models/
│   ├── bronze/
│   │   └── _bronze_sources.yml
│   ├── silver/
│   │   ├── stg_fda_adverse_events.sql
│   │   └── stg_fda_adverse_events.yml
│   └── gold/
│       ├── fct_adverse_events.sql
│       ├── agg_reaction_frequency.sql
│       ├── agg_drug_safety_profile.sql
│       ├── agg_patient_demographics.sql
│       ├── agg_polypharmacy_signals.sql
│       └── _gold_models.yml
├── macros/
│   ├── generate_alias_name.sql
│   └── custom_transformations.sql
├── tests/
│   ├── generic/
│   └── singular/
├── dbt_project.yml
├── profiles.yml
└── README.md
```

## Setup

### Prerequisites
- dbt Core 1.5+
- Snowflake connector for dbt
- Python 3.9+

### Installation

1. **Install dbt and dependencies**
   ```bash
   cd dbt
   pip install -r requirements.txt
   ```

2. **Configure dbt profiles**
   ```bash
   dbt debug
   # Creates/validates ~/.dbt/profiles.yml
   ```

3. **Initialize Snowflake connection**
   - Update `profiles.yml` with your Snowflake credentials
   - Or use environment variables (recommended)

4. **Install dbt packages**
   ```bash
   dbt deps
   ```

## Layers

### Silver Layer

**Purpose**: Clean and standardize raw data

**Model**: `stg_fda_adverse_events`

**Transformations**:
- Decode coded fields (sex: 1→Male, outcome: 1→Fatal)
- Convert dates to DATE type
- Standardize column names to snake_case
- Remove exact duplicates
- One row per drug-reaction combination
- Parse patient demographics
- Parse drug information

**Key Columns**:
```
event_id (PK)
report_type
serious (0/1)
is_fatal (0/1)
patient_age
patient_sex (Male/Female/Unknown)
patient_weight_kg
reaction_name
reaction_outcome
drug_name
drug_route
drug_dosage_value
drug_dosage_unit
event_date
reported_date
loaded_at
source_drug (ingestion source)
```

### Gold Layer

#### fct_adverse_events (Fact Table)

**Purpose**: Central fact table for all adverse events

**Grain**: One row per event-drug-reaction combination

**Dimensions**:
- `dim_drug` - Drug information
- `dim_patient` - Patient demographics
- `dim_reaction` - Reaction details
- `dim_outcome` - Outcome types
- `dim_date` - Event date

**Measures**:
- Count of events
- Seriousness indicator
- Fatality indicator
- Outcome codes

#### agg_reaction_frequency

**Purpose**: Top reactions per drug

**Grain**: Drug + Reaction

**Columns**:
```
drug_name
reaction_name
reaction_count
reaction_frequency_pct
rank (by count within drug)
last_observed_date
```

#### agg_drug_safety_profile

**Purpose**: Key safety metrics per drug

**Grain**: Drug

**Columns**:
```
drug_name
total_events
serious_events
serious_rate_pct
fatal_events
fatal_rate_pct
serious_non_fatal_events
non_serious_events
outcome_distribution (JSON)
last_updated
```

#### agg_patient_demographics

**Purpose**: Patient characteristics per drug

**Grain**: Drug + Demographics

**Columns**:
```
drug_name
patient_age_group (0-18, 19-40, 41-60, 60+)
patient_sex
patient_count
event_count
avg_age
serious_rate_pct
last_updated
```

#### agg_polypharmacy_signals

**Purpose**: Multi-drug adverse event signals

**Grain**: Drug combination

**Columns**:
```
drug_1_name
drug_2_name
co_occurrence_count
combined_serious_rate_pct
combined_fatal_rate_pct
most_common_reaction
last_updated
```

## Running dbt

### Full Build

```bash
dbt run
```

Runs all models:
1. Source freshness checks (bronze)
2. Silver layer transformations
3. Gold layer aggregations

### Build Specific Models

```bash
# Build silver layer only
dbt run -s stg_fda_adverse_events

# Build gold layer only
dbt run -s tag:gold

# Build fact table and its dependencies
dbt run -s +fct_adverse_events
```

### Build & Test

```bash
dbt run --select state:modified
dbt test
```

### Test Models

```bash
# Test all
dbt test

# Test specific model
dbt test -s stg_fda_adverse_events

# Test data (not documentation)
dbt test --select test_type:data
```

### Generate Documentation

```bash
dbt docs generate
dbt docs serve  # Opens on http://localhost:8000
```

### View DAG

```bash
dbt dag
```

## Model Naming Conventions

| Pattern | Layer | Example |
|---------|-------|---------|
| `stg_*` | Silver | `stg_fda_adverse_events` |
| `fct_*` | Gold | `fct_adverse_events` |
| `agg_*` | Gold | `agg_reaction_frequency` |
| `dim_*` | Gold | `dim_drug` (if needed) |

## Testing Strategy

### Generic Tests (Built-in)

```yaml
columns:
  - name: event_id
    tests:
      - unique
      - not_null
  
  - name: patient_sex
    tests:
      - accepted_values:
          values: ['Male', 'Female', 'Unknown']
```

### Singular Tests (Custom SQL)

```sql
-- tests/check_serious_rate.sql
-- Should not have serious rates > 100%

SELECT *
FROM {{ ref('agg_drug_safety_profile') }}
WHERE serious_rate_pct > 100
```

### Key Tests

- **Uniqueness**: event_id is unique in fct_adverse_events
- **Not Null**: All foreign keys are populated
- **Accepted Values**: Coded fields match domain
- **Referential Integrity**: All drug names exist
- **Data Freshness**: Data loaded within last 24 hours
- **Range Checks**: Ages between 0-150, percentages 0-100

## Configuration

### dbt_project.yml

```yaml
name: 'pharma_vigilance'
version: '1.0.0'

config-version: 2
profile: 'pharma_vigilance'

model-paths: ["models"]
macro-paths: ["macros"]
test-paths: ["tests"]
data-paths: ["data"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  pharma_vigilance:
    materialized: view  # or table
    bronze:
      materialized: view
    silver:
      materialized: table
      indexes:
        - columns: [drug_name]
        - columns: [event_date]
    gold:
      materialized: table
      indexes:
        - columns: [drug_name]
        - columns: [patient_sex]
```

### Profiles.yml

Use environment variables (recommended):

```yaml
pharma_vigilance:
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      database: "{{ env_var('SNOWFLAKE_DATABASE') }}"
      schema: "{{ env_var('SNOWFLAKE_SCHEMA_DEV', 'silver') }}"
      threads: 4
      client_session_keep_alive: false
```

## Advanced Features

### Macros

Custom SQL macros for common transformations:

```jinja
-- macros/decode_sex.sql
{% macro decode_sex(sex_code) %}
  CASE {{ sex_code }}
    WHEN 1 THEN 'Male'
    WHEN 2 THEN 'Female'
    ELSE 'Unknown'
  END
{% endmacro %}

-- Usage in model
SELECT
  {{ decode_sex('patient_sex') }} as patient_sex
FROM {{ source('bronze', 'raw_fda_adverse_events') }}
```

### Packages

Dependencies in `packages.yml`:

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.0
  - package: dbt-labs/expect
    version: 0.3.0
```

Install with: `dbt deps`

### Seeds

Static lookup tables in `data/`:

```yaml
# data/drug_mappings.csv
fda_drug_id,drug_name_standardized,therapeutic_class
ASPIRIN,Aspirin,Analgesic
IBU,Ibuprofen,NSAID
```

Load with: `dbt seed`

## Best Practices

1. **Always test new models**
   - Add `unique` and `not_null` tests on keys
   - Add range/accepted value tests
   - Document with descriptions

2. **Materialize strategically**
   - Silver: Tables (frequently queried)
   - Gold: Tables (for dashboards)
   - Use views for intermediate steps

3. **Optimize for performance**
   - Cluster Snowflake tables on filter columns
   - Partition fact tables by date
   - Use incremental models for large datasets

4. **Document thoroughly**
   - Add model descriptions
   - Add column descriptions
   - Include business logic in comments

5. **Version control**
   - Commit `dbt_project.yml`
   - Don't commit profiles.yml (use env vars)
   - Include `packages.yml` for reproducibility

## Troubleshooting

### "Compilation Error"
```bash
dbt debug  # Check connection
dbt parse  # Check for syntax errors
```

### "Unable to connect to Snowflake"
- Check credentials in `.env` or `profiles.yml`
- Verify account identifier format
- Ensure warehouse exists and is running

### "Relations not found"
```bash
# Check source tables exist
SELECT * FROM raw_fda_adverse_events LIMIT 1;

# Check schema names
SHOW SCHEMAS IN DATABASE;
```

### "Out of memory"
- Use incremental models: `dbt run --models +agg_*`
- Reduce data volume in dev environment
- Increase Snowflake warehouse size

### "Tests failing"
```bash
dbt test --fail-fast  # Stop on first failure
dbt test -s model_name  # Test single model
dbt test --store-failures  # Save failures to table
```

## Performance Monitoring

### Check Model Execution Time

```bash
dbt run --profiles-dir ~/.dbt --select state:modified+ | grep "Completed successfully in"
```

### Snowflake Query History

```sql
SELECT 
  query_text,
  execution_time,
  rows_produced,
  compilation_time
FROM snowflake.account_usage.query_history
WHERE database_name = 'PHARMA_DB'
ORDER BY start_time DESC
LIMIT 20;
```

## Incremental Models

For large datasets, use incremental models:

```sql
-- models/gold/agg_reaction_frequency_incremental.sql

{{
  config(
    materialized = 'incremental',
    unique_key = ['drug_name', 'reaction_name'],
    on_schema_change = 'fail'
  )
}}

SELECT
  drug_name,
  reaction_name,
  COUNT(*) as reaction_count,
  MAX(event_date) as last_observed_date
FROM {{ ref('stg_fda_adverse_events') }}

{% if execute %}
  {% if run_started_at is defined %}
    WHERE event_date >= '{{ run_started_at }}'
  {% endif %}
{% endif %}

GROUP BY drug_name, reaction_name
```

## Next Steps

- Streamlit consumption: See [../streamlit/README.md](../streamlit/README.md)
- Full architecture: See [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- Data dictionary: See [../docs/DATA_DICTIONARY.md](../docs/DATA_DICTIONARY.md)

## Resources

- [dbt Docs](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [Snowflake + dbt](https://docs.getdbt.com/docs/supported-databases/snowflake-setup)
- [dbt CLI Commands](https://docs.getdbt.com/reference/dbt-cli-overview)

## Support

- Issues: Check dbt logs in `target/` directory
- Questions: Review documentation first
- Debugging: Run `dbt debug` and `dbt parse`

---

**Last Updated**: June 3, 2026
