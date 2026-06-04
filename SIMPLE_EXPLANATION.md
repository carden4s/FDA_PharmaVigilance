# FDA PharmaVigilance - Simple Visual Guide

## The Problem You Had

You were used to running Streamlit apps like:
```bash
streamlit run app.py
```

And everything just works. **But this project is different** because it has **3 moving parts**.

---

## The Solution (Understanding the 3 Layers)

### 🔵 LAYER 1: INGESTION (Python)
**What it does**: Fetches adverse event data from FDA API
**Command**: `python src/main.py`
**Where**: `ingestion/` folder
**What you see**:
```
Testing FDA API connection...
✓ FDA API connected
Fetching Aspirin adverse events...
Loaded 3,450 records to Snowflake
✅ DONE!
```
**Result**: Data in **Snowflake BRONZE table** (raw data)

---

### 🟡 LAYER 2: TRANSFORMATION (dbt)
**What it does**: Cleans & processes data, creates analytics tables
**Command**: `dbt run`
**Where**: `dbt/` folder
**What you see**:
```
Running with dbt 1.7.0
13:15:36  Running 6 nodes...
13:15:40    Completed successfully
6 nodes have finished successfully
```
**Result**: Data in **Snowflake GOLD tables** (ready for dashboard)

---

### 🟢 LAYER 3: DASHBOARD (Streamlit)
**What it does**: Reads data and shows interactive dashboard
**Command**: `streamlit run app.py`
**Where**: `streamlit/` folder
**What you see**:
```
Local URL: http://localhost:8501
```
**Result**: Open browser → See dashboard! 🎉

---

## The Flow Visualized

```
┌─────────────────┐
│  FDA API        │  ← Real adverse event data from FDA
│  (External)     │
└────────┬────────┘
         │
         │ LAYER 1: Ingestion (Python)
         │ Command: python src/main.py
         ↓
┌─────────────────────────────────┐
│  Snowflake BRONZE              │  ← Raw data stored here
│  (RAW_FDA_ADVERSE_EVENTS)       │
└────────┬────────────────────────┘
         │
         │ LAYER 2: Transformation (dbt)
         │ Command: dbt run
         ↓
┌─────────────────────────────────┐
│  Snowflake SILVER & GOLD        │  ← Cleaned & aggregated data
│  (Analytics tables)              │
└────────┬────────────────────────┘
         │
         │ LAYER 3: Dashboard (Streamlit)
         │ Command: streamlit run app.py
         ↓
┌─────────────────────────────────┐
│  http://localhost:8501           │  ← Interactive dashboard
│  (Interactive charts, metrics)   │
└─────────────────────────────────┘
         ↑
      YOU SEE THIS!
```

---

## How to Run It (30 seconds explanation)

### **Choice 1: All-in-One (Easiest)**
```bash
docker-compose up
# Wait... then open: http://localhost:8501
```

### **Choice 2: Manual (See what's happening)**
Open **3 different terminals** and run:

```
Terminal 1 (Ingestion):    cd ingestion && python src/main.py
Terminal 2 (Transform):    cd dbt && dbt run
Terminal 3 (Dashboard):    cd streamlit && streamlit run app.py
```

Then open: http://localhost:8501

---

## Step-by-Step Walkthrough

### Step 1: Setup (5 min)
Create `.env` file with your credentials:
```
SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
FDA_API_KEY=your_fda_api_key
```

### Step 2: Run Layer 1 (2 min)
```bash
cd ingestion
python src/main.py
```
Wait for: `✅ DONE!`

### Step 3: Run Layer 2 (2 min)
```bash
cd dbt
dbt run
```
Wait for: `6 nodes have finished successfully`

### Step 4: Run Layer 3 (1 min)
```bash
cd streamlit
streamlit run app.py
```
Wait for: `Local URL: http://localhost:8501`

### Step 5: View Dashboard
Open browser: **http://localhost:8501**

Select a drug from dropdown → See charts! 🎉

---

## Where to See Results

### **Verify Layer 1** (After ingestion)
In Snowflake SQL editor:
```sql
SELECT COUNT(*) FROM PHARMA_DB.BRONZE.RAW_FDA_ADVERSE_EVENTS;
-- Should show: 3,450 rows
```

### **Verify Layer 2** (After dbt)
In Snowflake SQL editor:
```sql
SELECT * FROM PHARMA_DB.GOLD.AGG_DRUG_SAFETY_PROFILE LIMIT 5;
-- Should show: Drug profiles with safety metrics
```

### **Verify Layer 3** (After Streamlit)
Open browser: **http://localhost:8501**
Should show: Dashboard with metrics and charts

---

## What Gets Created

| Layer | Creates | Where | How Many |
|-------|---------|-------|----------|
| **1** | Raw data table | Snowflake BRONZE | 3,450 rows |
| **2** | 5 analysis tables | Snowflake GOLD | 1000s of rows |
| **3** | Interactive dashboard | Browser (8501) | 4 pages |

---

## The Magic (What Makes It Work)

Each layer **depends on the previous layer**:

- Layer 1 **→ creates** data in BRONZE
- Layer 2 **→ reads** BRONZE, **creates** GOLD
- Layer 3 **→ reads** GOLD, **displays** results

So you **must run them in order**! (Layer 1 first, then 2, then 3)

---

## Common Confusion (Explained)

**Q: "Why can't I just run all 3 at the same time?"**  
A: Because Layer 2 needs Layer 1 to finish first. If Layer 2 runs before Layer 1 finishes, there's no data to process!

**Q: "Why are there so many files?"**  
A: Because this is a REAL data platform:
- Layer 1 (Ingestion): Connects to FDA, handles errors, logs everything
- Layer 2 (Transformation): SQL queries, data quality checks, documentation
- Layer 3 (Dashboard): Multiple pages, multiple charts, caching for speed

**Q: "Can I modify the code?"**  
A: Yes! Edit the Python files or SQL queries as needed. Just understand:
- Python files run the ingestion
- SQL files transform the data
- Streamlit files create the dashboard

---

## Success Checklist

After running all 3 layers, you should see:

- [ ] Layer 1: "✅ DONE!" message
- [ ] Layer 2: "6 nodes have finished successfully" 
- [ ] Layer 3: "Local URL: http://localhost:8501"
- [ ] Browser: Dashboard appears with drug selector
- [ ] Dashboard: Can select drugs and see charts
- [ ] Dashboard: All 4 pages load without error

If all ✓, you're done! The project is working!

---

## Key Takeaways

✅ This is **NOT just a Streamlit app** - it's a complete **data platform**

✅ It has **3 layers** that must run in order

✅ Data flows: **FDA API → Snowflake → Dashboard**

✅ Run: **python (ingestion) → dbt (transform) → streamlit (display)**

✅ View results: **Snowflake for data, browser for dashboard**

---

## You're Ready!

1. Create `.env` with credentials
2. Run Layer 1, Layer 2, Layer 3 in order (or use `docker-compose up`)
3. Open browser
4. 🎉 See your pharmaceutical safety dashboard!

Any questions? Check the logs - they tell you exactly what's happening!
