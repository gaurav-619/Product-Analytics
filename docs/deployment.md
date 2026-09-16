# Streamlit Deployment Guide

## Deployment Architecture
This dashboard is designed to be securely deployed on Streamlit Community Cloud (or similar public hosts) as a portfolio case study. 
To guarantee security and avoid large BigQuery bills, it does **not** connect to BigQuery in production.

Instead, the application reads from **static Parquet extracts** stored in `app/data/`.

### Why Static Extracts?
1. **Security:** No GCP credentials, service accounts, or API keys are exposed to the public environment.
2. **Cost:** Visitors navigating the dashboard do not trigger live BigQuery queries.
3. **Speed:** Loading local Parquet files into memory is instantly fast compared to querying a warehouse.
4. **Privacy:** The extraction script aggressively filters out any pseudo-identifiers or transaction-level rows before they ever enter the repository.

## How to Generate Extracts
Before deploying or after updating dbt models, you must generate fresh data extracts.

1. Ensure your `.env` contains `GCP_PROJECT_ID` and `BQ_DATASET`.
2. Ensure you have valid Google Cloud credentials (`gcloud auth application-default login`).
3. Run the export script:
   ```bash
   python src/export_deployment_data.py
   ```
4. This will query your BigQuery marts, drop sensitive columns, and write Parquet files to `app/data/`.
5. Review the files generated, then commit them to Git.

## How to Run Locally
By default, the local app will load data from `app/data/` if the files exist. 
If they do not exist, the app will fall back to querying BigQuery directly using your local credentials.
```bash
streamlit run app/Home.py
```

## How to Deploy to Streamlit Community Cloud
1. Push your repository to GitHub.
2. Log into [Streamlit Community Cloud](https://streamlit.io/cloud).
3. Click **New app**.
4. Select your GitHub repository.
5. Set the **Branch** to `main`.
6. Set the **Main file path** to `app/Home.py`.
7. Click **Deploy!**

*Note: You do not need to configure any Advanced Settings or Secrets. The app runs entirely off the committed `app/data/` extracts.*

## Security Checklist
- [ ] No `.env` or `secrets.toml` committed.
- [ ] No `service-account.json` or GCP keys committed.
- [ ] `export_deployment_data.py` drops all PII before writing data to disk.
- [ ] Deployment runs purely on the pre-aggregated `.parquet` files.
- [ ] `test_deployment.py` passes locally before push.

## Limitations and Disclosures
- The underlying data is from Google's public, obfuscated GA4 sample.
- It is a historical snapshot ending January 31, 2021.
- Because it is purely observational, insights are correlations, not confirmed causal findings.
