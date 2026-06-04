# Setup Guide - FDA PharmaVigilance

Complete setup instructions for the FDA PharmaVigilance data platform.

## Prerequisites

Before starting, ensure you have:

- **Python 3.9+** - [Download](https://www.python.org/)
- **Git** - [Download](https://git-scm.com/)
- **Snowflake Account** - [Sign up](https://www.snowflake.com/)
- **dbt Core 1.5+** - Will be installed via pip
- **FDA API Key** - [Request here](https://api.fda.gov)
- **Code Editor** - VS Code recommended

### System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows, macOS, or Linux |
| Memory | 4GB minimum (8GB recommended) |
| Disk Space | 2GB for tools and dependencies |
| Internet | Required for FDA API and Snowflake |

## Step 1: Clone Repository

```bash
cd /path/to/projects
git clone https://github.com/your-org/FDA_PharmaVigilance.git
cd FDA_PharmaVigilance
```

## Step 2: Set Up Snowflake

### Create Snowflake Account

1. Go to [snowflake.com](https://www.snowflake.com/)
2. Sign up for free trial (30 days, $400 credit)
3. Choose region closest to you
4. Complete setup wizard

### Create Database and Schema

Connect to Snowflake and run:

```sql
-- Create database
CREATE DATABASE pharma_db;

-- Create schemas
CREATE SCHEMA pharma_db.bronze;      -- Raw data
CREATE SCHEMA pharma_db.silver;      -- Cleaned data
CREATE SCHEMA pharma_db.gold;        -- Aggregated data

-- Create warehouse
CREATE WAREHOUSE compute_wh
    WITH WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

-- Create role for ingestion
CREATE ROLE ingestion_role;

-- Create role for dbt
CREATE ROLE dbt_role;

-- Create role for dashboard
CREATE ROLE dashboard_role;

-- Grant permissions
-- Ingestion role
GRANT USAGE ON DATABASE pharma_db TO ROLE ingestion_role;
GRANT USAGE ON SCHEMA pharma_db.bronze TO ROLE ingestion_role;
GRANT CREATE TABLE ON SCHEMA pharma_db.bronze TO ROLE ingestion_role;
GRANT ALL PRIVILEGES ON WAREHOUSE compute_wh TO ROLE ingestion_role;

-- dbt role
GRANT USAGE ON DATABASE pharma_db TO ROLE dbt_role;
GRANT USAGE ON ALL SCHEMAS IN DATABASE pharma_db TO ROLE dbt_role;
GRANT ALL PRIVILEGES ON WAREHOUSE compute_wh TO ROLE dbt_role;
GRANT CREATE TABLE ON ALL SCHEMAS IN DATABASE pharma_db TO ROLE dbt_role;

-- Dashboard role
GRANT USAGE ON DATABASE pharma_db TO ROLE dashboard_role;
GRANT USAGE ON ALL SCHEMAS IN DATABASE pharma_db TO ROLE dashboard_role;
GRANT SELECT ON ALL TABLES IN SCHEMA pharma_db.gold TO ROLE dashboard_role;
GRANT USAGE ON WAREHOUSE compute_wh TO ROLE dashboard_role;

-- Create users
CREATE USER ingestion_user
    PASSWORD = 'secure_password_here'
    DEFAULT_WAREHOUSE = compute_wh
    DEFAULT_DATABASE = pharma_db
    DEFAULT_SCHEMA = bronze
    DEFAULT_ROLE = ingestion_role;

CREATE USER dbt_user
    PASSWORD = 'secure_password_here'
    DEFAULT_WAREHOUSE = compute_wh
    DEFAULT_DATABASE = pharma_db
    DEFAULT_ROLE = dbt_role;

CREATE USER dashboard_user
    PASSWORD = 'secure_password_here'
    DEFAULT_WAREHOUSE = compute_wh
    DEFAULT_DATABASE = pharma_db
    DEFAULT_SCHEMA = gold
    DEFAULT_ROLE = dashboard_role;

-- Assign roles to users
GRANT ROLE ingestion_role TO USER ingestion_user;
GRANT ROLE dbt_role TO USER dbt_user;
GRANT ROLE dashboard_role TO USER dashboard_user;
```

### Get Connection Details

From Snowflake UI:
1. Account Settings → Account
2. Find "Account Identifier" (e.g., `xyzabc.us-east-1`)
3. Note your region

## Step 3: Get FDA API Key

1. Visit [api.fda.gov](https://api.fda.gov/)
2. Click "Register"
3. Fill form with email
4. Check email for API key
5. Save for later

## Step 4: Set Up Environment Variables

### Copy Template

```bash
cp .env.example .env
```

### Edit .env

Open `.env` and fill in your values:

```env
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=xyzabc.us-east-1
SNOWFLAKE_USER=ingestion_user
SNOWFLAKE_PASSWORD=secure_password_here
SNOWFLAKE_WAREHOUSE=compute_wh
SNOWFLAKE_DATABASE=pharma_db
SNOWFLAKE_SCHEMA=bronze
SNOWFLAKE_ROLE=ingestion_role

# FDA API
FDA_API_KEY=your_api_key_here
FDA_API_BASE_URL=https://api.fda.gov/drug/event.json

# Environment
ENV=development
LOG_LEVEL=INFO

# Feature flags
ENABLE_REAL_TIME_ALERTS=false
ENABLE_ML_ANOMALY_DETECTION=false
```

### ⚠️ Security Note

✅ `.env` is in `.gitignore` - won't be committed
❌ Never commit `.env` file to git
❌ Never share `.env` file
❌ Rotate credentials quarterly

## Step 5: Set Up Python Ingestion Layer

### Install Dependencies

```bash
cd ingestion
pip install -r requirements.txt
```

### Test Snowflake Connection

```bash
python -c "
from src.snowflake_loader import SnowflakeLoader
loader = SnowflakeLoader()
print('Connection test:', loader.test_connection())
"
```

Expected output:
```
Connection test: True
```

### Test FDA API Connection

```bash
python -c "
from src.fda_client import FDAClient
client = FDAClient()
response = client.fetch_adverse_events('aspirin', limit=1)
print('FDA API test:', len(response['results']), 'records received')
"
```

Expected output:
```
FDA API test: 1 records received
```

## Step 6: Set Up dbt

### Install dbt

```bash
cd ../dbt
pip install -r requirements.txt
```

### Configure dbt Profile

Run:
```bash
dbt debug
```

This creates `~/.dbt/profiles.yml`. Edit it:

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
      schema: "{{ env_var('SNOWFLAKE_SCHEMA', 'silver') }}"
      threads: 4
      client_session_keep_alive: false
  
  target: dev
```

### Test dbt Connection

```bash
dbt debug
```

Expected output:
```
Connection test: ✓ passed
```

### Install dbt Packages

```bash
dbt deps
```

## Step 7: Set Up Streamlit Dashboard

### Install Dependencies

```bash
cd ../streamlit
pip install -r requirements.txt
```

### Configure Streamlit Secrets

```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
[snowflake]
account = "xyzabc.us-east-1"
user = "dashboard_user"
password = "secure_password_here"
warehouse = "compute_wh"
database = "pharma_db"
schema = "gold"
role = "dashboard_role"

[app]
max_query_rows = 100000
cache_ttl_minutes = 60
```

### Test Streamlit Connection

```bash
python data/snowflake_client.py
```

Expected output:
```
✓ Snowflake connection successful
✓ Gold layer tables accessible
```

## Step 8: Run First Ingestion

### Load Sample Data

```bash
cd ../ingestion
python src/main.py --mode test --batch-size 10
```

Expected output:
```
[INFO] Starting FDA ingestion
[INFO] Querying FDA API for aspirin...
[INFO] Extracted 42 records
[INFO] Flattened to 156 rows
[INFO] Loaded 156 records to Snowflake
[INFO] Completed in 3.2 seconds
```

### Verify Data in Bronze Layer

Connect to Snowflake and run:

```sql
SELECT COUNT(*) FROM pharma_db.bronze.raw_fda_adverse_events;
-- Should return > 0
```

## Step 9: Run dbt Transformations

### Build Models

```bash
cd ../dbt
dbt run
```

Expected output:
```
Running with dbt 1.5.0
Found 5 models

Completed successfully

Done. PASS=5 WARN=0 ERROR=0 RUNTIME=12.34s
```

### Run Tests

```bash
dbt test
```

Expected output:
```
Running with dbt 1.5.0
Found 8 tests

All tests passed!
```

### Generate Documentation

```bash
dbt docs generate
dbt docs serve
```

Opens documentation at http://localhost:8000

## Step 10: Launch Dashboard

```bash
cd ../streamlit
streamlit run app.py
```

Opens at http://localhost:8501

## Configuration Options

### Change Log Level

Edit `.env`:
```env
LOG_LEVEL=DEBUG  # More verbose
```

### Change Snowflake Warehouse Size

```sql
ALTER WAREHOUSE compute_wh SET WAREHOUSE_SIZE = 'MEDIUM';
```

Options: XSMALL, SMALL, MEDIUM, LARGE, XLARGE, 2XLARGE

### Change dbt Threads

Edit `dbt/dbt_project.yml`:
```yaml
config-version: 2
name: 'pharma_vigilance'
config:
  send_anonymous_usage_stats: False
  use_colors: True
```

Or override at runtime:
```bash
dbt run --threads 8
```

## Monitoring Setup

### Enable Query Logging in Snowflake

```sql
-- Check query history
SELECT 
  query_id,
  query_text,
  execution_time,
  rows_produced
FROM snowflake.account_usage.query_history
WHERE database_name = 'PHARMA_DB'
ORDER BY start_time DESC
LIMIT 10;
```

### View dbt Logs

```bash
# Logs stored in target/
cat target/run_results.json
```

### Monitor Streamlit

Streamlit logs to terminal:
```
2026-06-03 10:00:00 INFO root: Loaded drug safety profile for Aspirin
2026-06-03 10:00:01 INFO root: Query took 0.45 seconds
```

## Scheduling (Production)

### Linux/Mac Cron

Add to crontab:
```bash
crontab -e

# Add line:
0 2 * * * cd /path/to/ingestion && python src/main.py >> logs/cron.log 2>&1
```

Runs daily at 2 AM

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2 AM
4. Action: Run `python C:\path\to\ingestion\src\main.py`
5. Save

### Cloud Scheduling

**AWS Lambda**:
- Upload code as ZIP
- Set environment variables
- Trigger via CloudWatch Events (daily at 2 AM)

**Azure Functions**:
- Create Python function app
- Set timer trigger: `0 0 2 * * *` (2 AM daily)
- Set environment variables

**GCP Cloud Functions**:
- Create Python function
- Trigger via Cloud Scheduler (daily at 2 AM)
- Set environment variables

## Troubleshooting Setup

### "ModuleNotFoundError: No module named 'snowflake'"

```bash
pip install snowflake-connector-python
```

### "Unable to connect to Snowflake"

Check:
- Credentials in `.env` are correct
- Snowflake account format: `xyzabc.us-east-1`
- Warehouse exists and is running
- Firewall allows Snowflake IPs

### "FDA API returns 401"

- Verify FDA API key in `.env`
- Check key hasn't expired
- Request new key if needed

### "dbt: Profile not found"

```bash
dbt init pharma_vigilance
# Select Snowflake as database
# Follow prompts
```

### "Streamlit: No internet connection"

- Check network connectivity
- Verify proxy settings if behind corporate firewall

## Next Steps

1. ✅ **Configured**: All systems set up
2. 📊 **Ingest Data**: Run daily ingestion
3. 🔄 **Transform**: dbt processes data
4. 📈 **Analyze**: Streamlit dashboard shows results
5. 🚀 **Deploy**: Set up production environment

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- AWS/Azure/GCP deployment
- Docker containerization
- CI/CD pipeline setup
- Monitoring and alerting
- Backup and disaster recovery

## Getting Help

1. Check logs for error details
2. Review [CONTRIBUTING.md](../CONTRIBUTING.md)
3. Search existing [GitHub issues](https://github.com/your-org/FDA_PharmaVigilance/issues)
4. Contact data engineering team

---

**Last Updated**: June 3, 2026
**Setup Time**: ~30-45 minutes
**Status**: Beginner-friendly
