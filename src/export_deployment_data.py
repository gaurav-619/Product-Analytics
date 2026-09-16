import os
import json
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd

# Load environment variables
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = os.getenv("BQ_DATASET")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")

DATA_DIR = _project_root / "app" / "data"

TABLES_TO_EXPORT = [
    "mart_product_kpis_daily",
    "mart_funnel_performance",
    "mart_retention_cohorts",
    "mart_customer_rfm",
    "mart_segment_performance",
    "mart_product_performance"
]

FORBIDDEN_COLS = {
    "user_pseudo_id", "user_id", "transaction_id", "email", "phone", "ip_address",
    "credential", "token", "key"
}

def export_data():
    if not GCP_PROJECT_ID or not BQ_DATASET:
        print("ERROR: Missing environment variables. Set GCP_PROJECT_ID and BQ_DATASET.")
        return

    client = bigquery.Client(project=GCP_PROJECT_ID, location=BQ_LOCATION)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Exporting validated marts from {GCP_PROJECT_ID}.{BQ_DATASET} to {DATA_DIR}...")
    
    for table in TABLES_TO_EXPORT:
        query = f"SELECT * FROM `{GCP_PROJECT_ID}.{BQ_DATASET}.{table}`"
        print(f"  -> Exporting {table}...")
        try:
            df = client.query(query).to_dataframe()
            
            # Security check: Drop forbidden columns
            cols_to_drop = [c for c in df.columns if c.lower() in FORBIDDEN_COLS]
            if cols_to_drop:
                print(f"     Dropping sensitive columns: {cols_to_drop}")
                df = df.drop(columns=cols_to_drop)
                
            # Clean up raw GA4 obfuscated values (same logic as utils.py for consistency)
            clean_map = {
                "(none)": "Direct",
                "(data deleted)": "Unknown",
                "<Other>": "Other",
                "(not set)": "Unknown",
            }
            for col in df.select_dtypes(include=['object', 'string']).columns:
                df[col] = df[col].replace(clean_map)
                
            # Cast 'dbdate' extension types to standard datetime64[ns]
            for col in df.columns:
                if str(df[col].dtype) == 'dbdate':
                    df[col] = pd.to_datetime(df[col])
                
            out_path = DATA_DIR / f"{table}.parquet"
            df.to_parquet(out_path, index=False)
            print(f"     Saved {len(df)} rows to {out_path.name}")
        except Exception as e:
            print(f"     ERROR: Failed to export {table}: {e}")

    # Create metadata.json
    metadata = {
        "export_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_dataset": f"{GCP_PROJECT_ID}.{BQ_DATASET}",
        "dataset_disclosure": "SIMULATED EXPERIMENT DATA — Educational demonstration only. This is not GA4 data and is not evidence of real business impact. Base observational data is Google's public, obfuscated GA4 Google Merchandise Store sample.",
        "tables_exported": TABLES_TO_EXPORT
    }
    with open(DATA_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
        
    # Create README.md
    readme_content = """# Streamlit Deployment Data Extracts

These static Parquet files power the public portfolio Streamlit deployment. 
They are highly aggregated, non-sensitive extracts from the dbt models, allowing the dashboard to run without BigQuery credentials.

**Source Dataset:** Google's public, obfuscated GA4 sample dataset.
**Security:** No raw event data, user IDs, or transaction IDs are included.
"""
    with open(DATA_DIR / "README.md", "w") as f:
        f.write(readme_content)
        
    print("SUCCESS: Export complete!")

if __name__ == "__main__":
    export_data()
