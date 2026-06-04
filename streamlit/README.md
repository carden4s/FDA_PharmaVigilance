# Streamlit Dashboard - Consumption Layer

## Overview

Interactive Streamlit dashboard for FDA adverse event analysis and pharmaceutical safety monitoring. Connects directly to Snowflake's gold layer for real-time insights.

## Features

- 📊 Dynamic drug selector with trend analysis
- 🔴 Serious vs. non-serious adverse event breakdown
- 🏥 Patient demographics visualization
- ⚠️ Safety profile metrics (serious rate, fatal rate)
- 💊 Polypharmacy signal detection
- 🔍 Reaction frequency rankings
- 📈 Temporal trend analysis

## Project Structure

```
streamlit/
├── app.py                   # Main application entry point
├── pages/
│   ├── 01_Dashboard.py      # Main dashboard view
│   ├── 02_Drug_Safety.py    # Drug safety profiles
│   ├── 03_Demographics.py   # Patient demographics analysis
│   ├── 04_Polypharmacy.py   # Multi-drug signals
│   └── 05_Reports.py        # Custom reports
├── components/
│   ├── __init__.py
│   ├── sidebar.py           # Shared sidebar logic
│   ├── charts.py            # Charting utilities
│   ├── tables.py            # Table formatting
│   └── metrics.py           # Metric cards
├── data/
│   ├── __init__.py
│   ├── snowflake_client.py  # Snowflake connection
│   ├── queries.py           # SQL query templates
│   └── cache.py             # Caching logic
├── assets/
│   ├── logo.png
│   ├── styles.css
│   └── images/
├── config/
│   ├── __init__.py
│   └── settings.py          # App configuration
├── tests/
│   ├── test_components.py
│   └── test_queries.py
├── requirements.txt         # Python dependencies
├── .streamlit/
│   ├── config.toml          # Streamlit configuration
│   └── secrets.toml.example # Secrets template
├── setup.sh                 # Setup script
└── README.md                # This file
```

## Setup

### Prerequisites
- Python 3.9+
- Streamlit 1.20+
- Snowflake account with read access to gold layer
- Access to dbt-generated tables

### Installation

1. **Install dependencies**
   ```bash
   cd streamlit
   pip install -r requirements.txt
   ```

2. **Configure Snowflake connection**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit with your Snowflake credentials
   ```

3. **Test connection**
   ```bash
   python data/snowflake_client.py
   ```

## Usage

### Run Dashboard

```bash
streamlit run app.py
```

Opens at `http://localhost:8501` by default

### Command Line Options

```bash
# Change port
streamlit run app.py --server.port 8502

# Disable file watcher
streamlit run app.py --logger.level=warning

# Configure client
streamlit run app.py --client.toolbar.mode="viewer"
```

## Dashboard Pages

### 1. Dashboard (Main)

**Overview**: Key metrics and trends at a glance

**Widgets**:
- Drug selector dropdown
- Date range picker
- Key metrics cards (total events, serious %, fatal %)
- Event count trend chart
- Serious vs. non-serious pie chart
- Top 10 reactions table

**Queries**:
- `agg_drug_safety_profile` for metrics
- `fct_adverse_events` for trends
- `agg_reaction_frequency` for top reactions

### 2. Drug Safety Profiles

**Overview**: Detailed safety metrics per drug

**Widgets**:
- Drug multi-selector
- Safety profile comparison table
- Serious rate comparison chart
- Fatal rate comparison chart
- Outcome distribution stacked bar

**Queries**:
- `agg_drug_safety_profile`
- `agg_reaction_frequency`

### 3. Patient Demographics

**Overview**: Demographics of affected patients

**Widgets**:
- Drug selector
- Age distribution histogram
- Sex breakdown pie chart
- Age group comparison
- Demographics table

**Queries**:
- `agg_patient_demographics`
- `fct_adverse_events`

### 4. Polypharmacy Signals

**Overview**: Multi-drug adverse event patterns

**Widgets**:
- Drug pair selector
- Co-occurrence table
- Common reactions for drug combos
- Serious rate comparison
- Network visualization (optional)

**Queries**:
- `agg_polypharmacy_signals`

### 5. Custom Reports

**Overview**: Build custom analyses

**Widgets**:
- SQL query editor (read-only)
- Preset report templates
- Export options (CSV, PDF)
- Share report links

## Configuration

### Streamlit Config (.streamlit/config.toml)

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[client]
toolbarMode = "minimal"

[logger]
level = "info"

[server]
port = 8501
headless = true
runOnSave = true
```

### Secrets (.streamlit/secrets.toml)

```toml
[snowflake]
account = "xyzabc.us-east-1"
user = "dashboard_user"
password = "***"
warehouse = "compute_wh"
database = "pharma_db"
schema = "gold"
role = "dashboard_role"

[app]
max_query_rows = 100000
cache_ttl_minutes = 60
```

## Features Deep Dive

### Caching Strategy

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_drug_safety_profile(drug_name: str):
    """Fetch from Snowflake and cache"""
    query = """
        SELECT * FROM agg_drug_safety_profile
        WHERE drug_name = ?
    """
    return snowflake_client.query(query, [drug_name])
```

Benefits:
- Reduces Snowflake queries
- Faster page loads
- Better user experience

### Responsive Design

Dashboard adapts to screen size:
- Desktop (1200px+): Side-by-side charts
- Tablet (768px-1199px): Stacked layouts
- Mobile (<768px): Single column, scrollable

### Export Functionality

**Supported formats**:
- CSV - All tables
- PDF - Reports and charts
- PNG - Individual charts
- Excel - Multiple sheets

```python
# Example
if st.button("Download as CSV"):
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="adverse_events.csv",
        mime="text/csv"
    )
```

## Security

### Secrets Management

**NEVER commit** `.streamlit/secrets.toml` to git (already in .gitignore)

**Always use**:
- Environment variables for local development
- Streamlit secrets for deployment
- Read-only Snowflake roles for dashboard user

### Access Control

```python
# Example: Restrict to authenticated users
import streamlit as st

if 'user_id' not in st.session_state:
    st.error("Please log in first")
    st.stop()
```

### Deployed Access

- **Self-hosted**: Use nginx reverse proxy with authentication
- **Streamlit Cloud**: Use Streamlit authentication
- **Enterprise**: Integrate with SSO (Okta, Azure AD)

## Performance Optimization

### Query Optimization

```python
# Pre-aggregate in Snowflake (Gold layer)
# DON'T query raw data in Streamlit

# Good: Query pre-aggregated gold table
SELECT * FROM agg_drug_safety_profile

# Avoid: Aggregate 1M rows in Streamlit
SELECT *, COUNT(*) FROM fct_adverse_events GROUP BY drug_name
```

### Cache Management

```python
# Clear cache when data updates
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
```

### Query Limits

```python
# Limit row count returned
MAX_ROWS = 100000
query += f" LIMIT {MAX_ROWS}"
```

## Troubleshooting

### "Unable to connect to Snowflake"
- Check credentials in `.streamlit/secrets.toml`
- Verify warehouse is running
- Check network/firewall rules
- Try connecting with SnowSQL directly

### "Data is stale"
- Check Snowflake load status
- Verify dbt pipeline ran successfully
- Adjust cache TTL in settings
- Clear cache: `st.cache_data.clear()`

### "Page is slow"
- Check Snowflake query performance
- Reduce date range in filters
- Lower cache TTL (more refreshes)
- Scale Snowflake warehouse up

### "Charts not displaying"
- Check data has no nulls
- Verify column names match queries
- Check browser console for errors
- Try different chart type

## Testing

### Run Tests

```bash
pytest tests/ -v
```

### Manual Testing Checklist

- [ ] All filters working
- [ ] Charts render correctly
- [ ] Download buttons work
- [ ] Mobile responsive
- [ ] No credential leaks
- [ ] Page load time < 3 seconds

## Deployment

### Local (Development)

```bash
streamlit run app.py
```

### Streamlit Cloud

```bash
# Connect GitHub repo
# Set secrets in cloud UI
# Deploy with single click
```

### Self-Hosted (Docker)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
docker build -t pharma-dashboard .
docker run -p 8501:8501 pharma-dashboard
```

### AWS/Azure/GCP

Use managed container services or Streamlit Cloud for simplest setup.

## Development Workflow

### Adding a New Page

1. Create `pages/06_New_Feature.py`
2. Define Streamlit UI
3. Add SQL queries in `data/queries.py`
4. Add caching with `@st.cache_data`
5. Test locally
6. Add to navigation (if needed)

### Modifying Queries

1. Update query in `data/queries.py`
2. Test directly in Snowflake first
3. Update page to use new query
4. Test in Streamlit
5. Commit changes

### Adding Charts

```python
import plotly.graph_objects as go
import streamlit as st

fig = go.Figure(data=[
    go.Bar(x=df.drug_name, y=df.serious_rate)
])
st.plotly_chart(fig, use_container_width=True)
```

## Advanced Features

### Real-time Updates (Optional)

```python
# Auto-refresh every 5 minutes
import time
placeholder = st.empty()

while True:
    with placeholder.container():
        data = fetch_latest_data()
        st.dataframe(data)
    time.sleep(300)
```

### Multi-language Support (Optional)

```python
import streamlit as st

lang = st.selectbox("Language", ["English", "Spanish"])
translations = {
    "Drug Safety": {"English": "Drug Safety", "Spanish": "Seguridad del Medicamento"},
}
st.header(translations["Drug Safety"][lang])
```

### Custom Themes

Edit `.streamlit/config.toml`:

```toml
[theme]
base = "dark"  # light or dark
primaryColor = "#FF6B35"
```

## Monitoring

### Track Usage

```python
# Log page views
with open('logs/dashboard_usage.log', 'a') as f:
    f.write(f"{datetime.now()}: {st.session_state.page}\n")
```

### Performance Metrics

```python
# Track query times
import time
start = time.time()
data = fetch_adverse_events()
duration = time.time() - start
st.metric("Query Time", f"{duration:.2f}s")
```

## Next Steps

- Ingestion layer: See [../ingestion/README.md](../ingestion/README.md)
- Data transformation: See [../dbt/README.md](../dbt/README.md)
- Full architecture: See [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)

## Resources

- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Charts](https://plotly.com/python/)
- [Snowflake Connector](https://docs.snowflake.com/en/user-guide/python-connector.html)
- [Streamlit Deployment](https://docs.streamlit.io/deploy/streamlit-cloud)

## Support

- Issues: Check browser console and Streamlit terminal
- Questions: Review documentation
- Performance: Check Snowflake query logs

---

**Last Updated**: June 3, 2026
