# Data Dictionary

Complete reference for all tables, columns, and data types in the FDA PharmaVigilance platform.

## Bronze Layer (Raw Data)

### RAW_FDA_ADVERSE_EVENTS

Raw adverse event data exactly as received from FDA API.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `safetyreportid` | VARCHAR | NO | Unique FDA adverse event report identifier (PK) |
| `report_type` | VARCHAR | YES | Report type: EXP (Expedited), INITIAL, FOLLOW-UP |
| `serious` | INTEGER | YES | 1=Serious, 0=Non-serious |
| `seriousness_death` | INTEGER | YES | 1=Death reported, 0=No death |
| `seriousness_hospitalization` | INTEGER | YES | 1=Hospitalization, 0=No hospitalization |
| `seriousness_hospitalizationinitiating` | INTEGER | YES | Hospitalization was initiated |
| `seriousness_lifethreatening` | INTEGER | YES | 1=Life threatening, 0=No |
| `seriousness_disability` | INTEGER | YES | 1=Disability, 0=No |
| `seriousness_congenitalanomaly` | INTEGER | YES | 1=Congenital anomaly, 0=No |
| `patient_onsetage` | INTEGER | YES | Patient age at symptom onset (years) |
| `patient_onsetsageunit` | VARCHAR | YES | Age unit: YRS (years), MOS (months), WKS (weeks), DYS (days) |
| `patient_weight` | DECIMAL | YES | Patient weight in kg |
| `patient_sex` | INTEGER | YES | 1=Male, 2=Female, U/Null=Unknown |
| `patient_date_of_birth` | VARCHAR | YES | Patient birth date (format varies) |
| `drug_name` | VARCHAR | YES | Name of suspect drug |
| `drug_dose_value` | DECIMAL | YES | Dose quantity |
| `drug_dose_unit` | VARCHAR | YES | Dose unit: MG, ML, G, MMOL, etc. |
| `drug_route` | VARCHAR | YES | Route of administration: ORAL, IV, IM, TOPICAL, etc. |
| `drug_indication` | VARCHAR | YES | Medical indication for drug use |
| `drug_reaction_reactionmeddrapt` | VARCHAR | YES | Reaction term (MedDRA preferred term) |
| `drug_reaction_reactionmeddrallt` | VARCHAR | YES | Reaction low-level term |
| `drug_reaction_reactionmeddraversion` | VARCHAR | YES | MedDRA version used |
| `drug_reaction_reactionoutcome` | INTEGER | YES | 1=Fatal, 2=Serious, 3=Hospitalized, 4=Disability, 5=Congenital anomaly, 6=Other |
| `drug_reaction_reactionversiondate` | VARCHAR | YES | MedDRA version date |
| `drug_reaction_reactiondatelastupdated` | VARCHAR | YES | Last update date |
| `report_date` | VARCHAR | YES | Report submission date |
| `event_date` | VARCHAR | YES | Adverse event date |
| `received_date` | VARCHAR | YES | FDA receipt date |
| `original_receive_date` | VARCHAR | YES | Original receive date |
| `receiver_organization` | VARCHAR | YES | Receiving organization |
| `receiver_type` | VARCHAR | YES | Type of receiver: FC (Foreign), FD (FDA), LS (Local State), MR (Manufacturer), OT (Other) |
| `source_type` | VARCHAR | YES | Report source type |
| `sender_organization` | VARCHAR | YES | Sending organization |
| `sender_type` | VARCHAR | YES | Type of sender |
| `loaded_at` | TIMESTAMP | NO | Timestamp when loaded to Snowflake |
| `source_drug` | VARCHAR | NO | Drug that was being queried (ingestion source) |
| `ingestion_batch_id` | VARCHAR | NO | Batch identifier for this load |
| `fda_response_id` | VARCHAR | YES | FDA API response identifier |

**Primary Key**: `safetyreportid`

**Indexes**:
- Clustering: `(loaded_at, source_drug)`
- Secondary: `(report_date)`, `(event_date)`

**Row Count**: ~1-5M (scales with ingestion)

**Last Updated**: Daily

---

## Silver Layer (Cleaned & Standardized)

### STG_FDA_ADVERSE_EVENTS

Cleaned, deduplicated, and standardized adverse events.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `event_id` | VARCHAR | NO | Unique event identifier (PK, combines safetyreportid + drug + reaction) |
| `report_id` | VARCHAR | NO | FDA safetyreportid |
| `report_type` | VARCHAR | YES | EXPEDITED, INITIAL, FOLLOW_UP |
| `serious` | BOOLEAN | YES | TRUE=Serious adverse event |
| `is_fatal` | BOOLEAN | YES | TRUE=Fatality reported |
| `is_hospitalized` | BOOLEAN | YES | TRUE=Hospitalization |
| `is_life_threatening` | BOOLEAN | YES | TRUE=Life threatening |
| `is_disability` | BOOLEAN | YES | TRUE=Disability outcome |
| `patient_age` | INTEGER | YES | Patient age (years, 0-150) |
| `patient_age_group` | VARCHAR | YES | Age group: 0-18, 19-40, 41-60, 60+ |
| `patient_sex` | VARCHAR | YES | Male, Female, Unknown |
| `patient_weight_kg` | DECIMAL | YES | Patient weight in kg |
| `reaction_name` | VARCHAR | YES | Standardized reaction name (MedDRA PT) |
| `reaction_meddra_pt` | VARCHAR | YES | MedDRA Preferred Term |
| `reaction_meddra_llt` | VARCHAR | YES | MedDRA Low-Level Term |
| `reaction_outcome` | VARCHAR | YES | Fatal, Serious, Hospitalized, Disability, Congenital Anomaly, Other |
| `drug_name` | VARCHAR | YES | Standardized drug name (uppercase) |
| `drug_route` | VARCHAR | YES | ORAL, INTRAVENOUS, INTRAMUSCULAR, TOPICAL, etc. |
| `drug_dosage_value` | DECIMAL | YES | Dose quantity |
| `drug_dosage_unit` | VARCHAR | YES | MG, ML, G, MMOL, etc. |
| `drug_indication` | VARCHAR | YES | Medical reason for drug use |
| `event_date` | DATE | YES | Date adverse event occurred |
| `report_date` | DATE | YES | Date report was submitted |
| `received_date` | DATE | YES | Date FDA received report |
| `days_to_event` | INTEGER | YES | Days between report and event (NULL if event after report) |
| `loaded_at` | TIMESTAMP | NO | Timestamp loaded to Snowflake |
| `source_drug` | VARCHAR | NO | Drug being queried during ingestion |
| `dbt_loaded_at` | TIMESTAMP | NO | Timestamp of dbt load |
| `dbt_updated_at` | TIMESTAMP | YES | Timestamp of last dbt update |

**Primary Key**: `event_id`

**Unique Key**: `(report_id, drug_name, reaction_name)`

**Indexes**:
- Clustering: `(drug_name, event_date)`
- Secondary: `(patient_age_group)`, `(patient_sex)`, `(reaction_outcome)`

**Row Count**: Typically 20-30% larger than Bronze (one row per drug-reaction combo)

**Last Updated**: Daily post-ingestion

---

## Gold Layer (Aggregated & Business-Ready)

### FCT_ADVERSE_EVENTS (Fact Table)

Central fact table for adverse events.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `fact_id` | VARCHAR | NO | Unique fact identifier (PK) |
| `event_id` | VARCHAR | NO | Reference to Silver event |
| `drug_name` | VARCHAR | NO | Drug name (FK to dim_drug) |
| `reaction_name` | VARCHAR | YES | Reaction name (FK to dim_reaction) |
| `patient_age_group` | VARCHAR | YES | Age group (FK to dim_patient_age) |
| `patient_sex` | VARCHAR | YES | Sex (FK to dim_patient_sex) |
| `reaction_outcome` | VARCHAR | YES | Outcome (FK to dim_outcome) |
| `event_date_key` | INTEGER | YES | Date key (FK to dim_date) |
| `is_serious` | BOOLEAN | YES | Seriousness flag |
| `is_fatal` | BOOLEAN | YES | Fatality flag |
| `event_count` | INTEGER | YES | Always 1 (grain is one event) |
| `loaded_at` | TIMESTAMP | NO | Load timestamp |

**Primary Key**: `fact_id`

**Foreign Keys**:
- `drug_name` → `dim_drug(drug_name)`
- `event_date_key` → `dim_date(date_key)`

**Indexes**: Clustering on `(drug_name, event_date_key)`

**Row Count**: Same as Silver

---

### AGG_REACTION_FREQUENCY

Top reactions per drug.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `drug_name` | VARCHAR | NO | Drug name (PK) |
| `reaction_name` | VARCHAR | NO | Reaction name (PK) |
| `reaction_count` | INTEGER | NO | Number of reports |
| `total_drug_events` | INTEGER | NO | Total events for this drug |
| `reaction_frequency_pct` | DECIMAL(5,2) | NO | Percentage of drug events (0-100) |
| `rank` | INTEGER | NO | Rank within drug (1=most common) |
| `last_observed_date` | DATE | YES | Most recent occurrence |
| `serious_reaction_count` | INTEGER | YES | Count where reaction was serious |
| `fatal_reaction_count` | INTEGER | YES | Count where reaction was fatal |
| `updated_at` | TIMESTAMP | NO | Last update timestamp |

**Primary Key**: `(drug_name, reaction_name)`

**Used By**: Streamlit dashboard reaction frequency charts

**Refresh**: Daily

---

### AGG_DRUG_SAFETY_PROFILE

Safety metrics per drug.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `drug_name` | VARCHAR | NO | Drug name (PK) |
| `total_events` | INTEGER | NO | Total adverse events reported |
| `serious_events` | INTEGER | NO | Count of serious events |
| `serious_rate_pct` | DECIMAL(5,2) | NO | Serious / Total (0-100) |
| `fatal_events` | INTEGER | NO | Count of fatal events |
| `fatal_rate_pct` | DECIMAL(5,2) | NO | Fatal / Total (0-100) |
| `hospitalized_events` | INTEGER | NO | Count of hospitalizations |
| `hospitalization_rate_pct` | DECIMAL(5,2) | NO | Hospitalized / Total (0-100) |
| `life_threatening_events` | INTEGER | NO | Life threatening events |
| `life_threatening_rate_pct` | DECIMAL(5,2) | NO | Life threatening / Total (0-100) |
| `disability_events` | INTEGER | NO | Disability outcome events |
| `disability_rate_pct` | DECIMAL(5,2) | NO | Disability / Total (0-100) |
| `congenital_anomaly_events` | INTEGER | NO | Congenital anomaly events |
| `congenital_anomaly_rate_pct` | DECIMAL(5,2) | NO | Congenital anomaly / Total (0-100) |
| `unique_patients_approx` | INTEGER | YES | Approximate count of affected patients |
| `date_first_event` | DATE | YES | Earliest event date |
| `date_last_event` | DATE | YES | Most recent event date |
| `event_date_range_days` | INTEGER | YES | Days between first and last event |
| `updated_at` | TIMESTAMP | NO | Last update timestamp |

**Primary Key**: `drug_name`

**Used By**: Safety profile page, drug comparison, main dashboard

**Refresh**: Daily

---

### AGG_PATIENT_DEMOGRAPHICS

Patient characteristics per drug.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `drug_name` | VARCHAR | NO | Drug name (PK) |
| `patient_age_group` | VARCHAR | NO | Age group: 0-18, 19-40, 41-60, 60+ (PK) |
| `patient_sex` | VARCHAR | NO | Male, Female, Unknown (PK) |
| `patient_count` | INTEGER | NO | Approximate distinct patients |
| `event_count` | INTEGER | NO | Number of adverse events in this segment |
| `avg_age` | DECIMAL(5,1) | YES | Average age of affected patients |
| `serious_event_count` | INTEGER | NO | Serious events in segment |
| `serious_rate_pct` | DECIMAL(5,2) | NO | Serious events / Total in segment (0-100) |
| `fatal_event_count` | INTEGER | NO | Fatal events in segment |
| `fatal_rate_pct` | DECIMAL(5,2) | NO | Fatal events / Total in segment (0-100) |
| `updated_at` | TIMESTAMP | NO | Last update timestamp |

**Primary Key**: `(drug_name, patient_age_group, patient_sex)`

**Used By**: Demographics page, patient characteristics analysis

**Refresh**: Daily

---

### AGG_POLYPHARMACY_SIGNALS

Multi-drug adverse event patterns.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `drug_1_name` | VARCHAR | NO | First drug (PK, alphabetically first) |
| `drug_2_name` | VARCHAR | NO | Second drug (PK, alphabetically second) |
| `co_occurrence_count` | INTEGER | NO | Events with both drugs reported |
| `total_drug_1_events` | INTEGER | YES | Total events for drug 1 |
| `total_drug_2_events` | INTEGER | YES | Total events for drug 2 |
| `co_occurrence_rate_pct` | DECIMAL(5,2) | YES | Co-occurrence / combined events |
| `combined_serious_count` | INTEGER | NO | Serious events with both drugs |
| `combined_serious_rate_pct` | DECIMAL(5,2) | NO | Serious / co-occurrence (0-100) |
| `combined_fatal_count` | INTEGER | NO | Fatal events with both drugs |
| `combined_fatal_rate_pct` | DECIMAL(5,2) | NO | Fatal / co-occurrence (0-100) |
| `most_common_reaction` | VARCHAR | YES | Most frequently co-reported reaction |
| `most_common_reaction_count` | INTEGER | YES | Count of most common reaction |
| `unique_combinations_reactions` | INTEGER | YES | Number of different reaction combinations |
| `updated_at` | TIMESTAMP | NO | Last update timestamp |

**Primary Key**: `(drug_1_name, drug_2_name)`

**Used By**: Polypharmacy page, drug interaction analysis

**Refresh**: Daily

---

## Dimension Tables (Optional)

If implementing full star schema:

### DIM_DRUG

| Column | Type | Description |
|--------|------|-------------|
| `drug_id` | VARCHAR | PK |
| `drug_name` | VARCHAR | Standardized name |
| `drug_category` | VARCHAR | Therapeutic class |
| `is_active` | BOOLEAN | Currently monitored |

### DIM_PATIENT_AGE

| Column | Type | Description |
|--------|------|-------------|
| `age_group_id` | INTEGER | PK |
| `age_group_name` | VARCHAR | 0-18, 19-40, 41-60, 60+ |
| `min_age` | INTEGER | Minimum age |
| `max_age` | INTEGER | Maximum age |

### DIM_OUTCOME

| Column | Type | Description |
|--------|------|-------------|
| `outcome_id` | INTEGER | PK |
| `outcome_name` | VARCHAR | Fatal, Serious, etc. |
| `severity_level` | INTEGER | 1=Fatal, 2=Serious, etc. |

### DIM_DATE

| Column | Type | Description |
|--------|------|-------------|
| `date_key` | INTEGER | YYYYMMDD format (PK) |
| `date_actual` | DATE | Actual date |
| `year` | INTEGER | Year |
| `quarter` | INTEGER | Quarter (1-4) |
| `month` | INTEGER | Month (1-12) |
| `day_of_month` | INTEGER | Day (1-31) |

---

## Data Quality Rules

### Validation Rules

| Field | Rule | Severity |
|-------|------|----------|
| `patient_age` | 0-150 years OR NULL | Error |
| `patient_sex` | M, F, U, or NULL | Error |
| `serious` | 0 or 1 | Error |
| `drug_name` | NOT NULL and NOT '' | Error |
| `reaction_name` | NOT NULL and NOT '' | Error |
| `event_date` | Not in future | Warning |
| `reaction_frequency_pct` | 0-100 | Error |
| `serious_rate_pct` | 0-100 | Error |

### Freshness Guarantees

| Table | Maximum Age | SLA |
|-------|-------------|-----|
| RAW_FDA_ADVERSE_EVENTS | 24 hours | P0 |
| STG_FDA_ADVERSE_EVENTS | 25 hours | P0 |
| fct_adverse_events | 25 hours | P0 |
| agg_* tables | 26 hours | P1 |

---

## Coding Values Reference

### Patient Sex

| Code | Value |
|------|-------|
| 1 | Male |
| 2 | Female |
| U | Unknown |
| NULL | Unknown |

### Reaction Outcome

| Code | Value |
|------|-------|
| 1 | Fatal |
| 2 | Serious |
| 3 | Hospitalized |
| 4 | Disability |
| 5 | Congenital Anomaly |
| 6 | Other |
| NULL | Unknown |

### Report Type

| Value | Description |
|-------|-------------|
| EXP | Expedited |
| INITIAL | Initial report |
| FOLLOW-UP | Follow-up to previous report |

---

## Common Queries

### Find most serious drugs

```sql
SELECT drug_name, serious_rate_pct, fatal_rate_pct
FROM agg_drug_safety_profile
ORDER BY fatal_rate_pct DESC
LIMIT 10;
```

### Find top reactions for a drug

```sql
SELECT reaction_name, reaction_count, reaction_frequency_pct
FROM agg_reaction_frequency
WHERE drug_name = 'ASPIRIN'
ORDER BY reaction_count DESC
LIMIT 10;
```

### Find concerning drug combinations

```sql
SELECT drug_1_name, drug_2_name, co_occurrence_count, combined_fatal_rate_pct
FROM agg_polypharmacy_signals
WHERE combined_fatal_rate_pct > 5
ORDER BY co_occurrence_count DESC;
```

### Find demographic groups most affected

```sql
SELECT patient_age_group, patient_sex, event_count, serious_rate_pct
FROM agg_patient_demographics
WHERE drug_name = 'IBUPROFEN'
ORDER BY event_count DESC;
```

---

**Last Updated**: June 3, 2026
**Version**: 1.0
