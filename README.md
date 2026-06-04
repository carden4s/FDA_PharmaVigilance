# FDA PharmaVigilance Data Platform

## Overview
A comprehensive data analytics platform for FDA adverse event monitoring and pharmaceutical safety tracking. This project implements a modern data lakehouse architecture using Python for data ingestion, dbt for transformations, Snowflake for storage, and Streamlit for visualization.

## Project Architecture

```
INGESTION LAYER (Python)
    ↓
FDA API (daily, per drug)
    ↓
Python extracts + flattens JSON
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BRONZE LAYER (Raw Data)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Snowflake: RAW_FDA_ADVERSE_EVENTS
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SILVER LAYER (Cleaned & Standardized - dbt)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
stg_fda_adverse_events
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GOLD LAYER (Aggregated & Business-Ready - dbt)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
├── fct_adverse_events
├── agg_reaction_frequency
├── agg_drug_safety_profile
├── agg_patient_demographics
└── agg_polypharmacy_signals
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONSUMPTION LAYER (Streamlit)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Interactive Dashboard
```

## Project Structure

```
FDA_PharmaVigilance/
├── .github/
│   ├── workflows/           # CI/CD pipeline definitions
│   └── ISSUE_TEMPLATE/      # Issue templates
├── ingestion/               # Python data ingestion layer
│   ├── src/
│   │   ├── main.py
│   │   ├── fda_client.py
│   │   ├── data_processor.py
│   │   └── snowflake_loader.py
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
├── dbt/                     # dbt transformations (Silver & Gold layers)
│   ├── models/
│   │   ├── bronze/
│   │   ├── silver/
│   │   └── gold/
│   ├── macros/
│   ├── tests/
│   ├── dbt_project.yml
│   └── README.md
├── streamlit/               # Streamlit dashboard (Consumption layer)
│   ├── app.py
│   ├── pages/
│   ├── assets/
│   ├── requirements.txt
│   └── README.md
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   ├── SETUP.md
│   └── DEPLOYMENT.md
├── .env.example             # Example environment variables (DO NOT COMMIT .env)
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── CONTRIBUTING.md          # Contribution guidelines
└── LICENSE                  # License file
```

## Key Components

### 1. Ingestion Layer (Python)
- Daily FDA API polling
- JSON extraction and flattening
- Data validation and preprocessing
- Direct loading to Snowflake Bronze layer

**See**: [ingestion/README.md](ingestion/README.md)

### 2. Bronze Layer (Snowflake)
- Raw data storage exactly as received from FDA
- All original fields preserved
- Minimal transformations (timestamps, source tracking only)
- Table: `RAW_FDA_ADVERSE_EVENTS`

### 3. Silver Layer (dbt)
- Data standardization and cleaning
- Coded value mapping (sex, outcomes, etc.)
- Duplicate removal
- Data type conversions
- Model: `stg_fda_adverse_events`

**See**: [dbt/README.md](dbt/README.md)

### 4. Gold Layer (dbt)
- Business-ready aggregations
- Fact and dimension tables
- Pre-calculated metrics

**Models**:
- `fct_adverse_events`: Fact table with all events
- `agg_reaction_frequency`: Top reactions ranked by count
- `agg_drug_safety_profile`: Serious/fatal rates, outcome distribution
- `agg_patient_demographics`: Age and sex breakdowns
- `agg_polypharmacy_signals`: Common drug combinations

### 5. Consumption Layer (Streamlit)
- Interactive dashboard for safety analysis
- Drug selector with dynamic filtering
- Reaction frequency visualization
- Demographics and polypharmacy signals

**See**: [streamlit/README.md](streamlit/README.md)

## Quick Start

### Prerequisites
- Python 3.9+
- Snowflake account with appropriate permissions
- dbt Core installed
- Git configured

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FDA_PharmaVigilance
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Snowflake credentials
   ```

3. **Install dependencies**
   ```bash
   # Ingestion layer
   cd ingestion
   pip install -r requirements.txt
   
   # dbt
   cd ../dbt
   dbt deps
   
   # Streamlit
   cd ../streamlit
   pip install -r requirements.txt
   ```

4. **Run the ingestion pipeline**
   ```bash
   cd ingestion
   python src/main.py
   ```

5. **Execute dbt transformations**
   ```bash
   cd dbt
   dbt run
   dbt test
   ```

6. **Launch Streamlit dashboard**
   ```bash
   cd streamlit
   streamlit run app.py
   ```

See detailed setup instructions in [docs/SETUP.md](docs/SETUP.md)

## ⚠️ Security & Credentials

**NEVER commit credentials to git.** This project is configured with a comprehensive `.gitignore` that excludes:
- `.env` files
- API keys and tokens
- Snowflake configuration files
- Private credentials

**Always**:
- Use `.env.example` as a template
- Store sensitive data in `.env` (local only)
- Use environment variables at runtime
- Rotate credentials regularly
- Use Snowflake role-based access control

See [Security Best Practices](#security-best-practices) below.

## Development Workflow

### Feature Development
1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -m "Add your feature"`
3. Push and create a Pull Request: `git push origin feature/your-feature`
4. Ensure CI/CD passes before merging
5. Merge to main and deploy

### Data Validation
- All data changes should have corresponding dbt tests
- Run `dbt test` before committing transformations
- Update data dictionary when schema changes

### Local Testing
- Test ingestion locally with sample data
- Use dbt `--select` for targeted model testing
- Test Streamlit app with mock data before production

## CI/CD Pipeline

See `.github/workflows/` for automated pipeline definitions:
- Data quality checks on each commit
- dbt model testing and documentation generation
- Automated deployment on main branch

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for details.

## Monitoring & Alerting

The system monitors:
- FDA API availability and response times
- Snowflake load failures
- Data quality metrics
- Streamlit app uptime

Set up alerts in your cloud provider (AWS CloudWatch, Azure Monitor, etc.)

## Security Best Practices

1. **Credentials Management**
   - Never hardcode credentials
   - Use environment variables exclusively
   - Rotate API keys and tokens quarterly

2. **Data Access**
   - Implement role-based access control (RBAC) in Snowflake
   - Limit user permissions to necessary roles
   - Audit data access logs

3. **Git Security**
   - Review `.gitignore` regularly
   - Use `git-secrets` or similar pre-commit hooks
   - Never force-push to main branch

4. **Snowflake Security**
   - Use separate credentials for development and production
   - Enable MFA for Snowflake console access
   - Encrypt data in transit and at rest

5. **Code Review**
   - Require 2+ reviewers for main branch PRs
   - Review `.env.example` changes carefully
   - Check for hardcoded secrets in code

## Documentation

- [Architecture Deep Dive](docs/ARCHITECTURE.md)
- [Data Dictionary](docs/DATA_DICTIONARY.md)
- [Setup Instructions](docs/SETUP.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contribution Guidelines](CONTRIBUTING.md)

## Troubleshooting

### Common Issues

**FDA API connection fails**
- Check internet connectivity
- Verify API key in `.env`
- Check FDA API status page

**Snowflake connection fails**
- Verify Snowflake credentials in `.env`
- Check network/firewall rules
- Ensure Snowflake warehouse is running

**dbt model errors**
- Run `dbt debug` to check connection
- Review model dependencies: `dbt DAG`
- Check Snowflake logs for SQL errors

**Streamlit app won't load**
- Verify Snowflake connection
- Check browser console for errors
- Restart streamlit: `streamlit run app.py`

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style guidelines
- Pull request process
- Testing requirements
- Commit message conventions

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Contact & Support

For questions or support:
- Create an issue in the GitHub repository
- Contact the data engineering team
- Check existing documentation first

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

## Roadmap

Future enhancements:
- Real-time alerting dashboard
- Machine learning-based anomaly detection
- Multi-drug interaction analysis
- Regulatory compliance reports
- API for external consumers

---

**Last Updated**: June 3, 2026
**Status**: Active Development
