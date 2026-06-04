# FDA PharmaVigilance Architecture

## System Overview

A comprehensive data platform for FDA adverse event monitoring implementing a modern data lakehouse architecture with Bronze, Silver, and Gold layers.

```
┌─────────────────────────────────────────────────────────────┐
│                    CONSUMPTION LAYER                         │
│                   (Streamlit Dashboard)                      │
│  - Interactive analysis, drug comparison, safety profiles  │
└────────────────────────────┬────────────────────────────────┘
                             │
                   Gold Layer Tables
                  (dbt transformations)
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌─────────┐      ┌──────────────┐      ┌──────────────┐
    │Fact Tbl │      │Agg: Reactions│      │Agg: Safety   │
    │fct_*    │      │agg_reaction  │      │agg_drug_     │
    └─────────┘      │_frequency    │      │safety_profile│
                     └──────────────┘      └──────────────┘
                             │
┌────────────────────────────┼────────────────────────────────┐
│              SILVER LAYER (dbt transformations)             │
│  - Cleaning, standardization, mapping, deduplication      │
│  - stg_fda_adverse_events                                  │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────┐
│        BRONZE LAYER (Snowflake Raw Data)                    │
│  - Exactly as received from FDA                            │
│  - RAW_FDA_ADVERSE_EVENTS                                   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────┐
│      INGESTION LAYER (Python)                               │
│  - Daily FDA API polling                                    │
│  - JSON extraction and flattening                           │
│  - Data validation                                          │
│  - Direct load to Snowflake                                 │
└────────────────────────────┬────────────────────────────────┘
                             │
                      FDA API (FAERS)
                Daily adverse event data
```

## Layer Details

### Layer 1: Ingestion (Python)

**Purpose**: Extract data from FDA and prepare for loading

**Components**:
- `FDAClient`: Handles FDA API authentication and requests
- `DataProcessor`: Flattens nested JSON responses
- `Validator`: Applies business rules and data quality checks
- `SnowflakeLoader`: Bulk loads validated data to Bronze layer

**Key Responsibilities**:
- Daily polling of FDA API for configured drugs
- JSON extraction and normalization
- Data validation against domain rules
- Batch loading to Snowflake
- Error handling and audit trail

**Data Flow**:
```
FDA API Response (JSON)
    ↓
Extract adverse events array
    ↓
Flatten nested drug/reaction arrays (1 row per drug-reaction)
    ↓
Apply validation rules
    ↓
Add metadata (loaded_at, source_drug, batch_id)
    ↓
Batch insert into RAW_FDA_ADVERSE_EVENTS
```

**Technologies**:
- Python 3.9+
- `requests` for API calls
- `snowflake-connector-python` for data loading
- `pandas` for data transformation
- `pydantic` for validation

### Layer 2: Bronze (Raw Data)

**Purpose**: Immutable record of all data received from FDA

**Table**: `RAW_FDA_ADVERSE_EVENTS`

**Grain**: One row per drug per adverse event report

**Schema** (simplified):
```sql
CREATE TABLE raw_fda_adverse_events (
    -- PK
    safetyreportid VARCHAR PRIMARY KEY,
    
    -- Report metadata
    report_type VARCHAR,          -- EXP, INITIAL, FOLLOW-UP
    serious INT,                  -- 0/1
    serious_death INT,            -- 0/1
    
    -- Patient data (coded)
    patient_age INT,
    patient_sex INT,              -- 1=Male, 2=Female, null=Unknown
    
    -- Reaction data
    reaction_meddrapt VARCHAR,
    reaction_outcome INT,         -- 1=Fatal, 2=Serious, 3=Hospitalized...
    
    -- Drug data
    drug_name VARCHAR,
    drug_dosage_value DECIMAL,
    drug_dosage_unit VARCHAR,
    
    -- Audit trail
    loaded_at TIMESTAMP,
    source_drug VARCHAR,          -- Which drug was being queried
    ingestion_batch_id VARCHAR,
    fda_response_id VARCHAR
);
```

**Load Strategy**:
- Upsert on `safetyreportid`
- Preserves all original FDA fields exactly as received
- No transformations (except timestamp and metadata)
- Immutable historical record

**Freshness**: Daily updates from FDA API

### Layer 3: Silver (Cleaned & Standardized)

**Purpose**: Business-ready standardized data for analysis

**Model**: `stg_fda_adverse_events` (dbt)

**Transformations** applied to Bronze layer:
- Decode all coded fields (sex, outcome, seriousness)
- Date type conversions (parse and validate dates)
- Column name standardization (snake_case)
- Remove exact duplicates
- Parse demographics
- One row per drug-reaction combination

**Schema** (simplified):
```sql
SELECT
    event_id,
    report_type,
    serious,
    is_fatal,
    
    -- Decoded fields
    patient_age,
    patient_sex,                  -- 'Male', 'Female', 'Unknown'
    
    -- Reaction fields
    reaction_name,
    reaction_outcome,             -- 'Fatal', 'Serious', etc.
    
    -- Drug fields
    drug_name,
    drug_route,                   -- 'Oral', 'Intravenous', etc.
    drug_dosage_value,
    drug_dosage_unit,
    
    -- Dates
    event_date,
    reported_date,
    
    -- Audit
    loaded_at,
    source_drug
FROM raw_fda_adverse_events
```

**Key Transformations**:
```sql
-- Decode sex
CASE patient_sex
    WHEN 1 THEN 'Male'
    WHEN 2 THEN 'Female'
    ELSE 'Unknown'
END

-- Decode outcome
CASE reaction_outcome
    WHEN 1 THEN 'Fatal'
    WHEN 2 THEN 'Serious'
    WHEN 3 THEN 'Hospitalized'
    ...
END

-- Convert age to valid range
NULLIF(patient_age, 0) as patient_age  -- Remove placeholder zeros
```

**Materialization**: Table (for performance)

**Testing**:
- `unique` on event_id
- `not_null` on critical fields
- `accepted_values` on decoded enums
- Range checks on age, percentages

### Layer 4: Gold (Business-Ready Aggregations)

**Purpose**: Pre-calculated metrics and fact tables for consumption

**Models**:

#### fct_adverse_events (Fact Table)

**Grain**: One row per adverse event-drug-reaction combination

**Dimensions**:
- Drug name and characteristics
- Patient demographics (age, sex)
- Reaction details
- Outcome classification
- Report metadata

**Measures**:
- Seriousness flags
- Fatality flags
- Event counts

**Usage**: Underlying table for all gold aggregations

#### agg_reaction_frequency

**Grain**: Drug + Reaction

**Purpose**: Top adverse reactions per drug

**Columns**:
```
drug_name,
reaction_name,
reaction_count,
reaction_frequency_pct,
rank,
last_observed_date
```

**Query Pattern**:
```sql
SELECT
    drug_name,
    reaction_meddrapt,
    COUNT(*) as reaction_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY drug_name), 2) as frequency_pct,
    ROW_NUMBER() OVER (PARTITION BY drug_name ORDER BY COUNT(*) DESC) as rank
FROM stg_fda_adverse_events
GROUP BY drug_name, reaction_meddrapt
```

#### agg_drug_safety_profile

**Grain**: Drug

**Purpose**: Safety metrics aggregated by drug

**Key Metrics**:
- Total events
- Serious event count + %
- Fatal event count + %
- Outcome distribution

**Query Pattern**:
```sql
SELECT
    drug_name,
    COUNT(*) as total_events,
    SUM(CASE WHEN serious=1 THEN 1 ELSE 0 END) as serious_events,
    ROUND(100.0 * SUM(CASE WHEN serious=1 THEN 1 ELSE 0 END) / COUNT(*), 2) as serious_rate_pct,
    SUM(CASE WHEN is_fatal=1 THEN 1 ELSE 0 END) as fatal_events,
    ROUND(100.0 * SUM(CASE WHEN is_fatal=1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fatal_rate_pct
FROM stg_fda_adverse_events
GROUP BY drug_name
```

#### agg_patient_demographics

**Grain**: Drug + Demographics

**Purpose**: Patient characteristics by drug exposure

**Segments**:
- Age groups: 0-18, 19-40, 41-60, 60+
- Sex: Male, Female, Unknown
- Event counts and serious rates per segment

#### agg_polypharmacy_signals

**Grain**: Drug pair

**Purpose**: Multi-drug adverse event signals

**Identifies**:
- Most common drug combinations in adverse events
- Serious/fatal rates for combinations
- Most common reactions for each combination

**Value**: Detects potential drug interactions

## Data Flow Example

```
1. FDA API Response:
{
  "results": [{
    "safetyreportid": "12345",
    "patient": {
      "patientonsetage": 45,
      "patientsex": 1,
      "reaction": [
        {"reactionmeddrapt": "Myocardial infarction", "reactionoutcome": 1},
        {"reactionmeddrapt": "Chest pain", "reactionoutcome": 3}
      ]
    },
    "drug": [
      {"drugname": "ASPIRIN", "drugseparatedosagenumber": 100},
      {"drugname": "IBUPROFEN", "drugseparatedosagenumber": 200}
    ]
  }]
}

2. Bronze Layer (raw, as received):
safetyreportid | patient_sex | patient_age | reaction_meddrapt | drug_name | ...
12345          | 1           | 45          | Myocardial...      | ASPIRIN   | ...
12345          | 1           | 45          | Myocardial...      | IBUPROFEN | ...
12345          | 1           | 45          | Chest pain         | ASPIRIN   | ...
12345          | 1           | 45          | Chest pain         | IBUPROFEN | ...

3. Silver Layer (transformed):
event_id | patient_sex | patient_age | reaction_name | drug_name | ...
12345-1  | Male        | 45          | Myocardial... | Aspirin   | ...
12345-2  | Male        | 45          | Myocardial... | Ibuprofen | ...
12345-3  | Male        | 45          | Chest pain    | Aspirin   | ...
12345-4  | Male        | 45          | Chest pain    | Ibuprofen | ...

4. Gold Layer (aggregated):
drug_name | reaction_name     | reaction_count | frequency_pct
Aspirin   | Myocardial infarc | 1,245          | 2.3%
Aspirin   | Chest pain        | 982            | 1.8%
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Ingestion** | Python | API polling, data extraction |
| **API Client** | requests | HTTP communication with FDA |
| **Validation** | pydantic | Schema validation |
| **Data Loading** | snowflake-connector-python | Bulk load to Snowflake |
| **Bronze Store** | Snowflake | Raw data warehouse |
| **Transformations** | dbt | SQL-based transformations |
| **Analytics DB** | Snowflake | Gold layer tables |
| **Dashboard** | Streamlit | Interactive analysis UI |
| **Visualization** | Plotly | Charts and graphs |
| **CI/CD** | GitHub Actions | Automated pipelines |

## Data Flows & Processes

### Daily Ingestion Flow

```
02:00 AM (Daily)
  ├─ Ingestion scheduled
  ├─ For each monitored drug:
  │   ├─ Query FDA API
  │   ├─ Extract adverse events
  │   ├─ Flatten nested arrays
  │   ├─ Validate records
  │   └─ Load to Bronze layer
  ├─ Generate audit report
  └─ Alert on failures

Post-Load (same day)
  ├─ dbt runs transformations
  │   ├─ Silver layer cleanup
  │   └─ Gold layer aggregations
  └─ Dashboards refresh overnight
```

### Query Flow (Dashboard)

```
User opens Streamlit dashboard
  ├─ Selects drug from dropdown
  ├─ Streamlit queries:
  │   ├─ agg_drug_safety_profile
  │   ├─ agg_reaction_frequency
  │   ├─ agg_patient_demographics
  │   └─ agg_polypharmacy_signals
  ├─ Results cached for 1 hour
  └─ Charts and tables rendered
```

## Scalability Considerations

### Data Volume Growth

**Bronze Layer**:
- Stores exact copy of all FDA responses
- Growth rate: ~500MB/month (estimate)
- Partitioning: By `loaded_at` date

**Silver Layer**:
- Normalized, deduplicated data
- ~25% of Bronze size
- Clustering: By `drug_name` and `event_date`

**Gold Layer**:
- Heavily aggregated
- ~5% of Silver size
- Materialized tables for performance

### Query Performance

**Optimization Strategies**:
- Snowflake clustering on filter columns
- Materialized views for common queries
- Query result caching in Streamlit
- Incremental dbt models for large datasets

### Concurrent Users

**Dashboard Load**:
- Query results cached for 1 hour
- Reduced simultaneous Snowflake connections
- Auto-scaling warehouse if needed

## Disaster Recovery

### Backup Strategy

- Bronze layer: Snowflake Time Travel (30 days)
- Silver/Gold: Reproducible from Bronze via dbt
- Source code: GitHub with automatic backups

### Failure Scenarios

| Scenario | Recovery |
|----------|----------|
| FDA API down | Skip day, retry next day |
| Snowflake down | Halt until available |
| dbt failure | Manual investigation, rerun |
| Dashboard down | Infrastructure restart |

## Security Architecture

### Credential Management

- All secrets in `.env` (development)
- Environment variables (production)
- Snowflake role-based access control
- Separate credentials per environment

### Data Access

- Ingestion user: Write to Bronze only
- dbt user: Read Bronze, write Silver/Gold
- Dashboard user: Read Gold only
- No direct data access from dashboards

### Encryption

- Snowflake: Encryption at rest and in transit
- API: HTTPS only
- Credentials: Never logged or displayed

## Monitoring & Alerting

### Metrics Tracked

- Daily ingestion success/failure
- Data freshness (hours since last load)
- dbt model run times
- Dashboard query performance
- Data quality metrics

### Alerts

- Ingestion failures (email, Slack)
- SLA violations (data > 24 hours old)
- Query timeouts
- Authentication failures

## Future Enhancements

1. **Real-time Ingestion**: Replace daily batch with streaming
2. **ML Integration**: Anomaly detection for new safety signals
3. **Predictive Analytics**: Risk scoring by patient/drug combination
4. **Regulatory Reporting**: Automated compliance reports
5. **Multi-source**: Integrate EHR, clinical trial data

## References

- [FDA FAERS API Documentation](https://open.fda.gov/apis/drug/event/)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [dbt Documentation](https://docs.getdbt.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

**Last Updated**: June 3, 2026
**Version**: 1.0
