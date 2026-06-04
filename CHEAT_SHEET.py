#!/usr/bin/env python3
"""
FDA PharmaVigilance - QUICK CHEAT SHEET
Copy-paste commands for each terminal
"""

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 FDA PHARMAVIGILANCE - QUICK CHEAT SHEET                      ║
║                         Copy-Paste Commands Below                            ║
╚══════════════════════════════════════════════════════════════════════════════╝


STEP 0: PREPARE (.env file)
═══════════════════════════════════════════════════════════════════════════════

Windows:
  notepad .env

Mac/Linux:
  nano .env

Then edit and save with:
  SNOWFLAKE_ACCOUNT=xy12345.us-east-1
  SNOWFLAKE_USER=your_username
  SNOWFLAKE_PASSWORD=your_password
  SNOWFLAKE_DATABASE=PHARMA_DB
  FDA_API_KEY=your_fda_api_key


OPTION A: DOCKER COMPOSE (EASIEST)
═══════════════════════════════════════════════════════════════════════════════

ONE COMMAND:
  docker-compose up

Then:
  → Open browser: http://localhost:8501
  → Press Ctrl+C to stop


OPTION B: MANUAL RUN (SEE WHAT'S HAPPENING)
═══════════════════════════════════════════════════════════════════════════════

Open 3 separate terminals/PowerShell windows and run in order:

┌─ TERMINAL 1 (Get data from FDA) ─────────────────────────────────────────────┐
│                                                                               │
│  cd ingestion                                                                 │
│  python src/main.py                                                           │
│                                                                               │
│  Expected output:                                                             │
│    ✓ FDA API connected                                                       │
│    ✓ Snowflake connected                                                     │
│    Fetching Aspirin adverse events...                                        │
│    Fetched 1,250 events                                                      │
│    Loaded 3,450 records to Snowflake                                         │
│    ✅ DONE!                                                                   │
│                                                                               │
│  ⏰ Wait for "DONE!" message before running Terminal 2                       │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ TERMINAL 2 (Process data) ──────────────────────────────────────────────────┐
│                                                                               │
│  cd dbt                                                                       │
│  dbt run                                                                       │
│                                                                               │
│  Expected output:                                                             │
│    13:15:36  Running 6 nodes...                                              │
│    13:15:40    Completed successfully                                        │
│    6 nodes have finished successfully                                        │
│                                                                               │
│  ⏰ Wait for completion before running Terminal 3                            │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ TERMINAL 3 (Show dashboard) ────────────────────────────────────────────────┐
│                                                                               │
│  cd streamlit                                                                 │
│  streamlit run app.py                                                         │
│                                                                               │
│  Expected output:                                                             │
│    You can now view your Streamlit app in your browser.                      │
│    Local URL: http://localhost:8501                                          │
│                                                                               │
│  🎉 Open browser: http://localhost:8501                                      │
│                                                                               │
│  Dashboard appears! Click through pages on left sidebar!                     │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘


VERIFY DATA AT EACH STAGE
═══════════════════════════════════════════════════════════════════════════════

After Terminal 1 (Ingestion):
  
  In Snowflake SQL editor:
    SELECT COUNT(*) FROM PHARMA_DB.BRONZE.RAW_FDA_ADVERSE_EVENTS;
  
  Should return: 3,450 (or similar)


After Terminal 2 (dbt):
  
  In Snowflake SQL editor:
    SELECT drug_name, total_events, serious_rate_pct 
    FROM PHARMA_DB.GOLD.AGG_DRUG_SAFETY_PROFILE 
    LIMIT 5;
  
  Should return: 
    Drug | Total Events | Serious Rate
    Aspirin | 1250 | 45.3%
    Ibuprofen | 980 | 38.2%
    etc...


After Terminal 3 (Streamlit):
  
  Open browser: http://localhost:8501
  
  Should show:
    ✓ Drug selector dropdown
    ✓ 4 metric boxes at top
    ✓ 2 charts in middle
    ✓ Table at bottom
    ✓ Left sidebar with navigation


TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

Error: "Connection refused"
  → Check .env file has correct credentials
  → Verify Snowflake account is active

Error: "Module not found"
  → pip install -r ingestion/requirements.txt
  → pip install -r dbt/requirements.txt
  → pip install -r streamlit/requirements.txt

Error: "No data in dashboard"
  → Verify Terminal 1 completed (shows DONE!)
  → Verify Terminal 2 completed (shows 6 nodes)
  → Check Snowflake queries above
  → Restart Streamlit (Ctrl+C, then streamlit run app.py)

Error: "FDA API key invalid"
  → Get correct key from: https://open.fda.gov/apis/authenticate/
  → No extra spaces or quotes


STOP THE PROJECT
═══════════════════════════════════════════════════════════════════════════════

Option A (Docker):
  Press Ctrl+C in terminal running "docker-compose up"

Option B (Manual):
  Press Ctrl+C in each terminal window


RE-RUN FRESH DATA
═══════════════════════════════════════════════════════════════════════════════

Terminal 1:
  cd ingestion
  python src/main.py --drug Ibuprofen    ← Different drug

Terminal 2:
  cd dbt
  dbt run --full-refresh                 ← Refresh all models

Terminal 3:
  cd streamlit
  streamlit run app.py
  
  Streamlit auto-reloads, try the new drug in dropdown!


WHAT'S BEING CREATED
═══════════════════════════════════════════════════════════════════════════════

Terminal 1 creates:
  └─ Table: PHARMA_DB.BRONZE.RAW_FDA_ADVERSE_EVENTS
     ├─ 3,450+ rows of raw FDA data
     └─ Columns: safetyreportid, patient_age, drug_name, reaction_name, etc.

Terminal 2 creates:
  ├─ Table: PHARMA_DB.SILVER.STG_FDA_ADVERSE_EVENTS (cleaned data)
  ├─ Table: PHARMA_DB.GOLD.FCT_ADVERSE_EVENTS (fact table)
  ├─ Table: PHARMA_DB.GOLD.AGG_DRUG_SAFETY_PROFILE (1 row per drug)
  ├─ Table: PHARMA_DB.GOLD.AGG_REACTION_FREQUENCY (top reactions)
  ├─ Table: PHARMA_DB.GOLD.AGG_PATIENT_DEMOGRAPHICS (age/gender breakdown)
  └─ Table: PHARMA_DB.GOLD.AGG_POLYPHARMACY_SIGNALS (drug combinations)

Terminal 3 creates:
  └─ Interactive Streamlit Dashboard at http://localhost:8501
     ├─ Page 1: Main Dashboard (metrics + charts)
     ├─ Page 2: Drug Safety (multi-drug comparison)
     ├─ Page 3: Demographics (age/gender analysis)
     └─ Page 4: Polypharmacy (drug combinations)


THE FLOW
═══════════════════════════════════════════════════════════════════════════════

FDA API data (JSON)
    ↓ [Terminal 1]
Raw data in Snowflake BRONZE
    ↓ [Terminal 2]
Cleaned & aggregated data in Snowflake SILVER & GOLD
    ↓ [Terminal 3]
Interactive dashboard in Streamlit
    ↓
YOU SEE RESULTS! 🎉


QUICK REFERENCE
═══════════════════════════════════════════════════════════════════════════════

Project Type:          Data pipeline + Analytics dashboard
Components:            3 layers (Ingestion, Transformation, Presentation)
Languages:             Python, SQL, Streamlit
Databases:             Snowflake (required)
Execution Time:        ~2-5 minutes per full run
Data Size:             Typically 3,000-5,000 adverse events per run
Refresh Frequency:     Can run on-demand or scheduled

Main Files:
  ingestion/src/main.py          ← Orchestration
  dbt/dbt_project.yml            ← Transformation config
  streamlit/app.py               ← Dashboard entry point
  .env                           ← Your credentials (create this!)


═══════════════════════════════════════════════════════════════════════════════

Ready? Start with: docker-compose up
                   OR
              [Terminal 1] cd ingestion && python src/main.py

═══════════════════════════════════════════════════════════════════════════════
""")
