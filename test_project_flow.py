"""
Visual demonstration of how the FDA PharmaVigilance project works
This script shows you what each layer does
"""

import json
from datetime import datetime

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_step(step_num, title):
    """Print formatted step"""
    print(f"\n[STEP {step_num}] {title}")
    print("-" * 70)

# ============================================================================
print_header("🏥 FDA PHARMAVIGILANCE PROJECT FLOW - VISUAL DEMO")

print("""
This project has 3 LAYERS that work together:

┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: INGESTION (Python)                                    │
│  ├─ Connects to FDA API                                          │
│  ├─ Fetches adverse events                                       │
│  ├─ Validates data                                               │
│  └─ Loads to Snowflake BRONZE schema (raw data)                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: TRANSFORMATION (dbt)                                   │
│  ├─ Reads from BRONZE (raw)                                      │
│  ├─ Cleans & normalizes data (SILVER schema)                     │
│  ├─ Creates analytics tables (GOLD schema)                       │
│  └─ 5 analytical tables ready for dashboard                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: DASHBOARD (Streamlit)                                  │
│  ├─ Reads from GOLD schema                                       │
│  ├─ Creates interactive charts                                   │
│  └─ Shows at http://localhost:8501                               │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================================
print_header("📊 LAYER 1: INGESTION - Sample Data Flow")

print_step(1, "FDA API returns raw JSON for Aspirin")
sample_fda_api = {
    "results": [
        {
            "safetyreportid": "10001234",
            "patient": {
                "onsetage": 65,
                "patientsex": 1,
                "patientweight": 75
            },
            "drugs": [
                {"medicinalproduct": "ASPIRIN", "drugroute": "ORAL", "dose": "500mg"}
            ],
            "reactions": [
                {"reactionmeddrapt": "Myocardial infarction", "reactionoutcome": 1},
                {"reactionmeddrapt": "Chest pain", "reactionoutcome": 2}
            ]
        }
    ]
}
print("✓ FDA API Response (nested JSON):")
print(json.dumps(sample_fda_api, indent=2)[:300] + "...")

print_step(2, "Python flattens to columnar format")
print("""
Raw JSON (1 event) → Multiple rows (1 per drug-reaction combo):

┌────────────┬──────────────┬────────────────────────────┐
│ report_id  │ drug_name    │ reaction_name              │
├────────────┼──────────────┼────────────────────────────┤
│ 10001234   │ ASPIRIN      │ Myocardial infarction      │
│ 10001234   │ ASPIRIN      │ Chest pain                 │
└────────────┴──────────────┴────────────────────────────┘

Result: 1 event → 2 rows in database
""")

print_step(3, "Data validated against business rules")
print("""
✓ Checking patient age (0-150)
✓ Checking patient sex (1=M, 2=F, U=Unknown)
✓ Checking drug name not empty
✓ Checking reaction name not empty
✓ Checking serious flag (0 or 1)

Result: 3,450 records passed, 90 failed → 3,450 loaded to Snowflake
""")

print_step(4, "Loaded to Snowflake BRONZE schema")
print("""
Table: PHARMA_DB.BRONZE.RAW_FDA_ADVERSE_EVENTS

Columns:
  ├─ safetyreportid (primary key)
  ├─ patient_age
  ├─ patient_sex
  ├─ patient_weight
  ├─ drug_name
  ├─ drug_route
  ├─ drug_dose
  ├─ reaction_name
  ├─ reaction_outcome
  ├─ is_serious
  └─ loaded_at (timestamp)

Query result:
  SELECT COUNT(*) FROM BRONZE.RAW_FDA_ADVERSE_EVENTS
  → 3,450 rows
""")

# ============================================================================
print_header("🔄 LAYER 2: TRANSFORMATION - dbt Processing")

print_step(5, "dbt reads BRONZE (raw) and cleans it")
print("""
BRONZE (Raw)                → SILVER (Cleaned)
├─ patient_sex: 1           ├─ patient_sex: "Male"
├─ patient_sex: 2           ├─ patient_sex: "Female"
├─ onsetage: 65             ├─ age_group: "41-60"
├─ reaction_outcome: 1      ├─ outcome: "Fatal"
└─ null values exist        └─ nulls standardized

dbt SQL does:
  ✓ Decode 1→Male, 2→Female
  ✓ Create age groups (0-18, 19-40, 41-60, 60+)
  ✓ Decode outcome codes
  ✓ Remove duplicates
  ✓ Standardize column names
""")

print_step(6, "dbt creates 5 GOLD analytical tables")
print("""
✓ fct_adverse_events
  └─ One row per event
  └─ Query: SELECT COUNT(*) → 3,450 rows

✓ agg_drug_safety_profile
  └─ One row per DRUG
  └─ Columns: drug_name, total_events, serious_rate_pct, fatal_rate_pct
  └─ Query: SELECT * WHERE drug_name='Aspirin'
      → Drug: Aspirin
         Total Events: 1,250
         Serious Rate: 45.3%
         Fatal Rate: 12.1%

✓ agg_reaction_frequency
  └─ Top reactions per drug
  └─ Query: SELECT * WHERE drug_name='Aspirin' LIMIT 10
      → Aspirin → Myocardial infarction (250 events, 20%)
      → Aspirin → Chest pain (180 events, 14.4%)
      → Aspirin → Gastrointestinal bleed (120 events, 9.6%)

✓ agg_patient_demographics
  └─ Demographics breakdown
  └─ Query: SELECT * WHERE drug_name='Aspirin'
      → Age Group 0-18: 50 patients, 2% serious
      → Age Group 19-40: 300 patients, 35% serious
      → Age Group 41-60: 500 patients, 48% serious
      → Age Group 60+: 400 patients, 62% serious

✓ agg_polypharmacy_signals
  └─ Drug combinations
  └─ Query: SELECT * LIMIT 10
      → Aspirin + Ibuprofen: 120 co-occurrences, 65% serious
      → Aspirin + Warfarin: 85 co-occurrences, 78% serious
""")

# ============================================================================
print_header("📊 LAYER 3: DASHBOARD - What You See")

print_step(7, "Streamlit reads GOLD tables and creates dashboard")
print("""
When you run: streamlit run app.py
And open: http://localhost:8501

You see:

PAGE 1 - MAIN DASHBOARD
├─ Drug Selector Dropdown: [Aspirin ▼]
├─ KEY METRICS
│  ├─ Total Events: 1,250
│  ├─ Serious Rate: 45.3%
│  ├─ Fatal Rate: 12.1%
│  └─ Approx. Patients: 1,250
├─ CHART 1: Top 10 Reactions (Bar Chart)
│  ├─ Myocardial infarction: 250
│  ├─ Chest pain: 180
│  ├─ Gastrointestinal bleed: 120
│  └─ ... (7 more)
├─ CHART 2: Serious vs Non-Serious (Pie Chart)
│  ├─ Serious: 567
│  └─ Non-Serious: 683
└─ TABLE: All reactions with counts

PAGE 2 - DRUG SAFETY
├─ Multi-drug selector: [Aspirin, Ibuprofen, Acetaminophen]
├─ Comparison Table
└─ Side-by-side serious rate comparison

PAGE 3 - DEMOGRAPHICS
├─ Age Distribution (Histogram)
├─ Gender Distribution (Pie Chart)
├─ Serious Rate by Age Group
└─ Detailed demographics table

PAGE 4 - POLYPHARMACY
├─ Drug Combination Summary
├─ Top 10 Combinations (Bar Chart)
├─ Frequency vs Serious Rate (Scatter)
└─ Full combinations table
""")

# ============================================================================
print_header("🎯 HOW TO RUN - Step by Step")

print("""
STEP 1: Create .env file with your credentials
───────────────────────────────────────────────

  1. Find: .env.example
  2. Copy to: .env
  3. Edit .env with:
     ├─ SNOWFLAKE_ACCOUNT
     ├─ SNOWFLAKE_USER
     ├─ SNOWFLAKE_PASSWORD
     ├─ SNOWFLAKE_DATABASE
     └─ FDA_API_KEY


STEP 2: Setup Streamlit Secrets (same credentials)
────────────────────────────────────────────────────

  1. Copy: streamlit/.streamlit/secrets.toml.example
  2. To: streamlit/.streamlit/secrets.toml
  3. Edit with Snowflake credentials


STEP 3: Run the project (Pick ONE option)
──────────────────────────────────────────

OPTION A - EASIEST (Docker Compose - runs all 3 at once):
  
  docker-compose up
  
  Then open: http://localhost:8501


OPTION B - MANUAL (Run in 3 separate terminals):

  TERMINAL 1 (Ingestion - gets data):
  ──────────
  cd ingestion
  python src/main.py
  
  Wait for completion (shows "Done!")
  
  
  TERMINAL 2 (Transformation - processes data):
  ───────────────────────────────────────────
  cd dbt
  dbt run
  
  Wait for completion (shows "6 nodes completed")
  
  
  TERMINAL 3 (Dashboard - shows results):
  ─────────────────────────────────────
  cd streamlit
  streamlit run app.py
  
  Open browser: http://localhost:8501
  
  DONE! You should see the dashboard!


STEP 4: Track data through the pipeline
───────────────────────────────────────────

  You can verify data at each stage:
  
  After Step 1 (Ingestion):
    SELECT COUNT(*) FROM PHARMA_DB.BRONZE.RAW_FDA_ADVERSE_EVENTS;
    → Should return: 3,450
  
  After Step 2 (dbt Transformation):
    SELECT * FROM PHARMA_DB.GOLD.AGG_DRUG_SAFETY_PROFILE;
    → Should return: Drug metrics
  
  After Step 3 (Streamlit):
    Open browser at http://localhost:8501
    → Should see interactive dashboard!
""")

# ============================================================================
print_header("⚠️ TROUBLESHOOTING")

print("""
Problem: "No data in dashboard"
Solution:
  1. Check .env has correct credentials
  2. Run ingestion (Terminal 1): python src/main.py
  3. Wait for completion message
  4. Run dbt (Terminal 2): dbt run
  5. Wait for "6 nodes completed"
  6. Then run streamlit


Problem: "Ingestion fails - Connection error"
Solution:
  1. Verify .env is updated with YOUR Snowflake details
  2. Check FDA_API_KEY is correct
  3. Test Snowflake connection in Snowflake console


Problem: "dbt run fails"
Solution:
  1. Make sure ingestion ran first (data in BRONZE)
  2. Update dbt/profiles.yml with YOUR Snowflake details
  3. Run: dbt run


Problem: "Streamlit won't connect to Snowflake"
Solution:
  1. Copy streamlit/.streamlit/secrets.toml.example to secrets.toml
  2. Edit with YOUR Snowflake credentials (same as .env)
  3. Restart Streamlit: Ctrl+C, then streamlit run app.py
""")

# ============================================================================
print_header("✅ VERIFICATION CHECKLIST")

print("""
Before running, verify you have:

  [ ] .env file created with credentials
  [ ] streamlit/.streamlit/secrets.toml created with credentials
  [ ] Python 3.11+ installed
  [ ] Snowflake account and access
  [ ] FDA API key
  [ ] Git repo cloned to your machine

When running:

  [ ] Terminal 1: Ingestion completes without errors
  [ ] Check Snowflake: BRONZE table has data (3,450+ rows)
  [ ] Terminal 2: dbt run completes (6 nodes)
  [ ] Check Snowflake: GOLD tables populated
  [ ] Terminal 3: Streamlit shows at http://localhost:8501
  [ ] Dashboard: Can select drugs and see charts
  [ ] Dashboard: All 4 pages load without errors

If all ✓, you're done! The project is working!
""")

print("\n" + "=" * 70)
print("  🎉 Ready to run? Follow the steps above!")
print("=" * 70 + "\n")
