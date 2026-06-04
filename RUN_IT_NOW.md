# 🚀 FDA PharmaVigilance - Run It Now (Simple Version)

## What You Need to Know

This project has **3 moving parts** that must work together:

```
YOU RUN THIS              →  DATA FLOW              →  YOU SEE THIS
┌──────────────────┐        ┌─────────────┐         ┌──────────────┐
│ python main.py   │   →    │ Snowflake   │    →    │  Streamlit   │
│ (Get FDA data)   │        │ (Database)  │         │ (Dashboard)  │
└──────────────────┘        └─────────────┘         └──────────────┘
  LAYER 1                      STORAGE               LAYER 3
 INGESTION                      LAYER 2           (THE INTERFACE)
                           TRANSFORMATION
```

---

## 📋 QUICKEST PATH (30 minutes)

### **1️⃣ Get Your Credentials Ready**

Before running anything, gather:
- ✅ Snowflake account ID (example: `xy12345.us-east-1`)
- ✅ Snowflake username
- ✅ Snowflake password  
- ✅ FDA API key (get from https://open.fda.gov/apis/authenticate/)
- ✅ Snowflake database name (or create one, e.g., `PHARMA_DB`)

**Don't have Snowflake?** Use free tier: https://signup.snowflake.com/

---

### **2️⃣ Set Up Configuration** (5 minutes)

Create the `.env` file with your credentials:

```bash
# In project root, create .env
# Copy contents from .env.example and edit with YOUR info:

SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=PHARMA_DB
SNOWFLAKE_SCHEMA=BRONZE
FDA_API_KEY=your_fda_key_here
```

**Also create Streamlit secrets:**

```bash
# Copy this file:
streamlit/.streamlit/secrets.toml.example

# To:
streamlit/.streamlit/secrets.toml

# Edit with SAME Snowflake credentials
```

---

### **3️⃣ Run the Project** (Choose ONE)

#### **Option A: EASIEST - Docker Compose (One command!)**

```bash
# Make sure Docker Desktop is running, then:
docker-compose up
```

Wait for all services to start, then open: **http://localhost:8501**

✅ Done! Dashboard should appear.

---

#### **Option B: Manual Run (See what's happening)**

Open **3 separate PowerShell/terminal windows** and run in order:

**Window 1 - Ingestion (Gets data from FDA)**
```bash
cd ingestion
python src/main.py
```

**Expected output:**
```
Loaded config from .env
Testing FDA API connection...
✓ FDA API connected
Testing Snowflake connection...
✓ Snowflake connected
Fetching Aspirin adverse events...
Fetched 1,250 events
Flattened to 3,540 rows
Validated 3,540 records (3,450 passed, 90 failed)
Loaded 3,450 records to Snowflake BRONZE.RAW_FDA_ADVERSE_EVENTS
✅ DONE! Loaded 3,450 records in 45 seconds
```

☝️ **Stop here and verify:**
```sql
-- In Snowflake, run:
SELECT COUNT(*) FROM PHARMA_DB.BRONZE.RAW_FDA_ADVERSE_EVENTS;
-- Should return: 3450 (or similar number)
```

**Window 2 - Transformation (Process data)**
```bash
cd dbt
dbt run
```

**Expected output:**
```
Running with dbt 1.7.0
13:15:36  Running 6 nodes...

13:15:40    Completed successfully
6 nodes have finished successfully
```

☝️ **Stop here and verify:**
```sql
-- In Snowflake, run:
SELECT * FROM PHARMA_DB.GOLD.AGG_DRUG_SAFETY_PROFILE LIMIT 5;
-- Should return: Drugs with safety metrics
```

**Window 3 - Dashboard (View results)**
```bash
cd streamlit
streamlit run app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.X:8501
```

🎉 **Open browser → http://localhost:8501**

---

## 👀 What You Should See

### **Dashboard Homepage**
- Drug selector dropdown at top
- 4 big metric boxes (Total Events, Serious %, Fatal %, Approx. Patients)
- Bar chart of top 10 reactions
- Pie chart of serious vs non-serious
- Table of all reactions

### **Pages (Click sidebar)**
- **Drug Safety**: Compare multiple drugs side-by-side
- **Demographics**: See who's affected (age, gender)
- **Polypharmacy**: See dangerous drug combinations

---

## 🔍 Verify Each Stage

**After Ingestion** → Check Snowflake:
```sql
SELECT COUNT(*) FROM PHARMA_DB.BRONZE.RAW_FDA_ADVERSE_EVENTS;
```
Should show: **3,000+** rows

**After dbt** → Check Snowflake:
```sql
SELECT drug_name, total_events, serious_rate_pct FROM PHARMA_DB.GOLD.AGG_DRUG_SAFETY_PROFILE LIMIT 5;
```
Should show: **Drug safety data** (e.g., Aspirin with 1,250 events, 45% serious)

**After Streamlit** → Open browser:
```
http://localhost:8501
```
Should show: **Interactive dashboard** with charts and metrics

---

## ⚠️ Common Issues & Fixes

### **"Connection refused - Snowflake"**
```
❌ Problem: Can't connect to Snowflake
✅ Fix:
   1. Check .env has correct account ID (no https://, just: xy12345.us-east-1)
   2. Test manually in Snowflake SQL editor
   3. Verify username/password correct
   4. Make sure account is active (not suspended)
```

### **"FDA API key invalid"**
```
❌ Problem: FDA API call fails
✅ Fix:
   1. Get key from: https://open.fda.gov/apis/authenticate/
   2. Copy exact key to .env
   3. Make sure no extra spaces/quotes
```

### **"No data in dashboard"**
```
❌ Problem: Dashboard shows no charts
✅ Fix (in order):
   1. Verify ingestion completed (Window 1 shows "DONE")
   2. Check Snowflake has BRONZE data: 
      SELECT COUNT(*) FROM PHARMA_DB.BRONZE.RAW_FDA_ADVERSE_EVENTS;
   3. Verify dbt completed (Window 2 shows "6 nodes completed")
   4. Check Snowflake has GOLD data:
      SELECT * FROM PHARMA_DB.GOLD.AGG_DRUG_SAFETY_PROFILE;
   5. Restart Streamlit (Ctrl+C in Window 3, then run again)
```

### **"Module not found" error**
```
❌ Problem: Missing Python packages
✅ Fix:
   1. Install requirements: pip install -r ingestion/requirements.txt
   2. Install dbt: pip install -r dbt/requirements.txt
   3. Install streamlit: pip install -r streamlit/requirements.txt
```

---

## 📊 Example of What Happens

**Input (FDA API):**
```json
{
  "drug": "Aspirin",
  "patient_age": 65,
  "reactions": ["chest pain", "myocardial infarction"]
}
```

↓ Ingestion flattens & validates ↓

**Bronze (Raw):**
```
| safetyreportid | drug_name | reaction_name | patient_age | is_serious |
|---|---|---|---|---|
| 10001234 | ASPIRIN | CHEST PAIN | 65 | 1 |
| 10001234 | ASPIRIN | MYOCARDIAL INFARCTION | 65 | 1 |
```

↓ dbt transforms & aggregates ↓

**Gold (Analytics):**
```
| drug_name | total_events | serious_rate_pct | fatal_rate_pct |
|---|---|---|---|
| ASPIRIN | 1250 | 45.3% | 12.1% |
```

↓ Streamlit displays ↓

**Dashboard:**
- Metric Box 1: "Total Events: 1,250"
- Metric Box 2: "Serious Rate: 45.3%"
- Chart: Bar graph of all reactions
- Table: Top 10 reactions with counts

---

## 🎯 Next Steps

**Once it's running:**
1. ✅ Try selecting different drugs
2. ✅ Check out all 4 dashboard pages
3. ✅ Run ingestion again to get fresh data
4. ✅ Explore dbt models in Snowflake
5. ✅ Set up alerts/monitoring

**To stop:**
- **Option A**: `Ctrl+C` in each terminal
- **Option B**: `docker-compose down`

---

## ✨ You're Ready!

The project is fully built. All you need to do is:
1. Create `.env` with your credentials
2. Run the 3 commands (or docker-compose)
3. Watch the data flow through
4. View the dashboard

**That's it! You have a complete pharmaceutical safety monitoring system!**

Questions? Check the logs in each terminal - they tell you exactly what's happening.
