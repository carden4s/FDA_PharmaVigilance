# Ingestion Layer - FDA PharmaVigilance

## Overview

The ingestion layer is a Python-based service that:
1. Queries the FDA Adverse Event Reporting System (FAERS) API daily
2. Extracts and flattens JSON responses
3. Validates data quality
4. Loads raw data directly to Snowflake's Bronze layer
5. Maintains an audit trail of all loads

## Architecture

```
FDA API
  ↓
Python Ingestion Service
  ├── Authentication
  ├── Request Management
  ├── Response Parsing
  ├── Data Flattening
  ├── Validation
  └── Error Handling
  ↓
Snowflake Bronze Layer
  └── RAW_FDA_ADVERSE_EVENTS
```

## Project Structure

```
ingestion/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── fda_client.py        # FDA API client
│   ├── data_processor.py    # JSON extraction & flattening
│   ├── validator.py         # Data validation rules
│   ├── snowflake_loader.py  # Snowflake connector
│   ├── logger.py            # Logging setup
│   └── config.py            # Configuration management
├── tests/
│   ├── __init__.py
│   ├── test_fda_client.py
│   ├── test_data_processor.py
│   ├── test_validator.py
│   └── test_snowflake_loader.py
├── data/
│   ├── sample/              # Sample FDA responses for testing
│   └── mappings/            # Lookup tables (drug IDs, etc.)
├── requirements.txt         # Python dependencies
├── requirements-dev.txt     # Development dependencies
├── setup.py                 # Package setup
├── .env.example             # Environment variables template
├── logging_config.yaml      # Logging configuration
└── README.md                # This file
```

## Setup

### Prerequisites
- Python 3.9+
- pip or conda
- Snowflake account with write access
- FDA API key (get from https://api.fda.gov)

### Installation

1. **Install dependencies**
   ```bash
   cd ingestion
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Snowflake credentials and FDA API key
   ```

3. **Verify Snowflake connection**
   ```bash
   python -c "from src.snowflake_loader import SnowflakeLoader; SnowflakeLoader().test_connection()"
   ```

## Usage

### Run Daily Ingestion

```bash
python src/main.py
```

### Run for Specific Drug

```bash
python src/main.py --drug "aspirin"
```

### Load Sample Data (Testing)

```bash
python src/main.py --mode test
```

### Command Line Options

```
--drug NAME          Specific drug to ingest (default: all configured drugs)
--date YYYY-MM-DD    Specific date to query (default: today)
--batch-size N       Records per batch to load (default: 1000)
--mode test|prod     Test or production mode (default: prod)
--dry-run            Don't load to Snowflake, just validate
--log-level DEBUG    Logging level (DEBUG, INFO, WARNING, ERROR)
```

## Configuration

### Environment Variables (.env)

```
# Snowflake
SNOWFLAKE_ACCOUNT=xyzabc.us-east-1
SNOWFLAKE_USER=ingestion_user
SNOWFLAKE_PASSWORD=***
SNOWFLAKE_WAREHOUSE=compute_wh
SNOWFLAKE_DATABASE=pharma_db
SNOWFLAKE_SCHEMA=bronze
SNOWFLAKE_ROLE=ingestion_role

# FDA API
FDA_API_KEY=***
FDA_API_BASE_URL=https://api.fda.gov/drug/event.json

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/ingestion.log
```

### Drugs Configuration

Edit `config.py` to define drugs to monitor:

```python
MONITORED_DRUGS = [
    {
        "name": "Aspirin",
        "fda_id": "ASPIRIN",
        "therapeutic_class": "Analgesic",
        "priority": "high"
    },
    {
        "name": "Ibuprofen",
        "fda_id": "IBUPROFEN",
        "therapeutic_class": "NSAID",
        "priority": "high"
    }
]
```

## Data Processing

### FDA API Response Structure

```json
{
  "results": [
    {
      "safetyreportid": "12345678",
      "reporttype": "EXP",
      "serious": 1,
      "seriousnessdeath": 1,
      "receiver": {...},
      "sender": {...},
      "patient": {
        "patientonsetage": 45,
        "patientsex": 1,
        "reaction": [
          {
            "reactionmeddrapt": "Myocardial infarction",
            "reactionoutcome": 1
          }
        ]
      },
      "drug": [
        {
          "drugname": "ASPIRIN",
          "drugseparatedosagenumber": 100
        }
      ]
    }
  ]
}
```

### Flattening Process

Raw nested JSON is flattened into normalized rows:

**Input**: One adverse event with multiple drugs and reactions
**Output**: One row per drug-reaction combination

Example:
- If an event reports 2 drugs with 3 reactions each
- Output: 2 rows (one per drug, with concatenated reactions)

### Data Validation

All records validated against:

```python
VALIDATION_RULES = {
    "safetyreportid": {"required": True, "type": str, "unique": True},
    "patient.patientonsetage": {"type": int, "range": [0, 150]},
    "patient.patientsex": {"allowed": [1, 2, "U"]},  # M, F, U
    "drug.drugname": {"required": True, "type": str},
    "serious": {"allowed": [0, 1]},
    "seriousnessdeath": {"allowed": [0, 1]},
}
```

Records failing validation:
- Are logged with error details
- Are NOT loaded to Snowflake
- Are stored in quarantine for manual review

## Data Load Process

### Bronze Layer (RAW_FDA_ADVERSE_EVENTS)

Columns added at load:

| Column | Type | Source | Purpose |
|--------|------|--------|---------|
| `loaded_at` | TIMESTAMP | System | Load timestamp |
| `source_drug` | VARCHAR | Config | Which drug was queried |
| `fda_response_id` | VARCHAR | FDA API | FDA response unique ID |
| `ingestion_batch_id` | VARCHAR | System | Batch identifier |
| All FDA fields | ... | FDA | Original data |

### Load Strategy

1. **Batch loading**: Groups records in configurable batches (default 1000)
2. **Upsert logic**: On `safetyreportid`, update if exists, insert if new
3. **Error handling**: Failed batches logged, processing continues
4. **Audit trail**: Load summary stored in `LOAD_AUDIT` table

### Example Load Query

```sql
INSERT OR REPLACE INTO bronze.raw_fda_adverse_events
SELECT 
    safetyreportid,
    report_type,
    serious,
    patient_age,
    patient_sex,
    reaction_name,
    reaction_outcome,
    drug_name,
    loaded_at,
    source_drug,
    ingestion_batch_id
FROM (
    SELECT * FROM @python_staging
    WHERE validation_status = 'PASSED'
)
```

## Monitoring & Logging

### Log Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Detailed API requests, data transformations |
| `INFO` | Load summaries, record counts |
| `WARNING` | Validation failures, retries |
| `ERROR` | Connection failures, critical errors |

### Log Output

```
2026-06-03 14:25:10 [INFO] Starting FDA ingestion for Aspirin
2026-06-03 14:25:12 [INFO] FDA API Response: 1,245 records
2026-06-03 14:25:15 [INFO] Flattened to 1,847 rows
2026-06-03 14:25:16 [WARNING] 3 records failed validation
2026-06-03 14:25:20 [INFO] Loaded 1,844 records to Snowflake
2026-06-03 14:25:21 [INFO] Ingestion complete in 11.2 seconds
```

## Error Handling

### FDA API Errors

| Error | Handling |
|-------|----------|
| Rate limit (429) | Exponential backoff, retry up to 5 times |
| Server error (5xx) | Retry with exponential backoff |
| Invalid request (4xx) | Log and skip |
| Network timeout | Retry up to 3 times |

### Snowflake Errors

| Error | Handling |
|-------|----------|
| Connection failed | Halt ingestion, alert ops |
| Authentication failed | Halt, check credentials |
| Table not found | Create if doesn't exist |
| Constraint violation | Log details, skip record |

## Scheduling

### Cron Scheduling (Linux/Mac)

```bash
# Daily at 2 AM
0 2 * * * cd /path/to/ingestion && python src/main.py >> logs/cron.log 2>&1
```

### Windows Task Scheduler

Create task to run:
```
python C:\path\to\ingestion\src\main.py
```
Daily at 2:00 AM

### Cloud Scheduling

**AWS Lambda**: Trigger via CloudWatch Events
**Azure**: Use Logic Apps or Functions on schedule
**GCP**: Cloud Scheduler triggers Cloud Function

## Testing

### Run Unit Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html
```

### Test Sample Data

```bash
python src/main.py --mode test --dry-run
```

### Manual Integration Test

```python
from src.fda_client import FDAClient
from src.data_processor import DataProcessor

client = FDAClient()
response = client.fetch_adverse_events("aspirin", limit=10)
processor = DataProcessor()
flattened = processor.flatten(response)
print(f"Flattened {len(response['results'])} events into {len(flattened)} rows")
```

## Troubleshooting

### "Unable to connect to Snowflake"
- Verify credentials in `.env`
- Check firewall/network rules
- Ensure Snowflake warehouse is running
- Try from different network

### "FDA API rate limit exceeded"
- Wait and retry - backoff is automatic
- Check FDA API documentation for limits
- Consider using API key with higher quota

### "Validation failed for X records"
- Check `quarantine/` directory for failed records
- Review error messages in logs
- May indicate FDA API schema changes

### "Memory error with large datasets"
- Reduce `--batch-size` (e.g., 500 instead of 1000)
- Run multiple passes for different drugs
- Check available system memory

## Performance Tips

1. **Parallel processing**: Run for different drugs in parallel
2. **Batch sizing**: Larger batches = fewer Snowflake connections (but more memory)
3. **Scheduling**: Run during off-peak hours to avoid resource contention
4. **Indexing**: Ensure Snowflake table has clustered keys on common filters

## Security

⚠️ **NEVER hardcode credentials in source code**

1. Always use `.env` file (already in `.gitignore`)
2. Rotate API keys quarterly
3. Use Snowflake role with minimal required permissions
4. Audit all data access
5. Enable Snowflake query logging

## Next Steps

- Silver layer transformations: See [../dbt/README.md](../dbt/README.md)
- Consumption layer: See [../streamlit/README.md](../streamlit/README.md)
- Full architecture: See [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)

## Resources

- [FDA OpenAPI Documentation](https://open.fda.gov/apis/drug/event/searchable-fields/)
- [Python Snowflake Connector](https://docs.snowflake.com/en/user-guide/python-connector.html)
- [Request Library](https://requests.readthedocs.io/)

## Support

Issues or questions?
1. Check existing issues
2. Review test files for examples
3. Consult logs for error details
4. Contact maintainers

---

**Last Updated**: June 3, 2026
