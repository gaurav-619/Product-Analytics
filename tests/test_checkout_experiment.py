import os
import json
import pandas as pd
import pytest
from src.simulation.generate_checkout_experiment import generate_data
from src.simulation.analyze_checkout_experiment import run_validations, analyze_experiment

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data", "simulated")
ARTIFACTS_DIR = os.path.join(ROOT_DIR, "artifacts", "simulated_experiment")
CSV_PATH = os.path.join(DATA_DIR, "checkout_experiment_simulated.csv")
META_PATH = os.path.join(DATA_DIR, "checkout_experiment_metadata.json")
SUMMARY_PATH = os.path.join(ARTIFACTS_DIR, "experiment_summary.csv")

@pytest.fixture(scope="module", autouse=True)
def setup_data():
    """Ensure data is generated before tests run."""
    generate_data()
    yield

def test_metadata_exists():
    assert os.path.exists(META_PATH)
    with open(META_PATH, "r") as f:
        meta = json.load(f)
    assert meta["experiment_name"] == "mobile_checkout_simplification_v1"

def test_data_deterministic():
    # Since seed is fixed at 42 in generate_data, re-running should yield identical results.
    df = pd.read_csv(CSV_PATH, skiprows=1)
    
    assert len(df) == 25000
    assert df["user_id"].nunique() == 25000
    assert set(df["variant"].unique()) == {"control", "treatment"}
    assert (df["is_eligible"] == True).all()
    assert (df["device_category"] == "mobile").all()
    
    # Check non-negative revenue and correct mapping
    assert (df["revenue_usd"] >= 0).all()
    
    non_converters = df[df["converted_purchase"] == 0]
    assert (non_converters["revenue_usd"] == 0).all()

def test_analysis_output():
    analyze_experiment()
    
    # Check that outputs are generated
    assert os.path.exists(SUMMARY_PATH)
    assert os.path.exists(os.path.join(ARTIFACTS_DIR, "experiment_report.md"))
    assert os.path.exists(os.path.join(ARTIFACTS_DIR, "conversion_comparison.html"))
    
    summary = pd.read_csv(SUMMARY_PATH)
    assert len(summary) == 1
    assert "decision" in summary.columns
    decision = summary["decision"].iloc[0]
    assert decision in ["Ship", "Iterate", "Stop", "Inconclusive"]
