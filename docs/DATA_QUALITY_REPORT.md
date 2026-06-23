# Data-Quality Report — FDA PharmaVigilance

> Reproducible evidence for the thesis. Every number below is produced by SQL you
> can re-run against `FARMACEUTICADATA.FDA_EXPERIENCE`. Values shown are a snapshot
> (re-run the queries to refresh). Source: openFDA / FDA FAERS.

## 0. How to regenerate everything
```bash
# from the dbt project folder, with SNOWFLAKE_* env vars set
dbt build --select agg_disproportionality val_positive_controls val_data_quality \
                   positive_controls monitored_drugs --profiles-dir .