import os
import json
from pathlib import Path
import pandas as pd

def test_deployment_extracts_exist_and_safe():
    """Verify deployment static extracts exist and contain no forbidden PII fields."""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "app" / "data"
    
    assert data_dir.exists(), "app/data directory must exist for deployment"
    
    expected_files = [
        "mart_daily_kpis.parquet",
        "mart_session_funnel.parquet",
        "mart_retention_cohorts.parquet",
        "mart_rfm_segments.parquet",
        "mart_session_monetization.parquet",
        "metadata.json",
        "README.md"
    ]
    
    for f in expected_files:
        assert (data_dir / f).exists(), f"Deployment missing required file: {f}"
        
    forbidden_cols = {
        "user_pseudo_id", "user_id", "transaction_id", "email", "phone", 
        "ip_address", "credential", "token", "key"
    }
    
    for f in expected_files:
        if f.endswith(".parquet"):
            df = pd.read_parquet(data_dir / f)
            for col in df.columns:
                assert col.lower() not in forbidden_cols, f"Forbidden column {col} found in {f}"

def test_metadata_contains_disclosure():
    project_root = Path(__file__).resolve().parent.parent
    meta_path = project_root / "app" / "data" / "metadata.json"
    
    with open(meta_path, "r") as f:
        meta = json.load(f)
        
    assert "export_timestamp_utc" in meta
    assert "dataset_disclosure" in meta
    assert "Educational demonstration only" in meta["dataset_disclosure"]
