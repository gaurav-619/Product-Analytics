import pandas as pd
import numpy as np
import json
import os
import uuid
from datetime import datetime, timedelta

# Configuration
SEED = 42
NUM_USERS = 25000
EXPERIMENT_ID = "mobile_checkout_simplification_v1"
DISCLAIMER_TEXT = "# SIMULATED EXPERIMENT DATA - Educational demonstration of experimentation analysis. This is not GA4 data and is not evidence of real business impact.\n"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "simulated")
CSV_PATH = os.path.join(DATA_DIR, "checkout_experiment_simulated.csv")
META_PATH = os.path.join(DATA_DIR, "checkout_experiment_metadata.json")

import random

def generate_data(seed=SEED, num_users=NUM_USERS, save_to_disk=False) -> pd.DataFrame:
    print(f"Generating deterministic synthetic data for {EXPERIMENT_ID}...")
    np.random.seed(seed)
    random.seed(seed)

    # 1. User IDs and base features
    user_ids = [str(uuid.UUID(int=random.getrandbits(128))) for _ in range(num_users)]
    
    # Random timestamps over a 4 week period
    start_time = datetime(2023, 10, 1)
    assignment_timestamps = [start_time + timedelta(seconds=int(s)) for s in np.random.randint(0, 86400 * 28, num_users)]
    
    # 50/50 Random allocation
    variants = np.random.choice(["control", "treatment"], size=num_users, p=[0.5, 0.5])

    df = pd.DataFrame({
        "user_id": user_ids,
        "experiment_id": EXPERIMENT_ID,
        "variant": variants,
        "assignment_timestamp": assignment_timestamps,
        "is_eligible": True,
        "device_category": "mobile"
    })

    # 2. Conversion Outcomes
    control_mask = df["variant"] == "control"
    treatment_mask = df["variant"] == "treatment"

    conversions = np.zeros(num_users, dtype=int)
    conversions[control_mask] = np.random.binomial(1, 0.050, size=control_mask.sum())
    conversions[treatment_mask] = np.random.binomial(1, 0.057, size=treatment_mask.sum())
    df["converted_purchase"] = conversions

    # 3. Revenue
    revenue = np.zeros(num_users)
    mu, sigma = 3.8, 0.8 
    
    converter_mask = df["converted_purchase"] == 1
    num_converters = converter_mask.sum()
    revenue[converter_mask] = np.random.lognormal(mean=mu, sigma=sigma, size=num_converters)
    df["revenue_usd"] = np.round(revenue, 2)

    # 4. Guardrails: Payment Error
    payment_errors = np.zeros(num_users, dtype=int)
    payment_errors[control_mask] = np.random.binomial(1, 0.010, size=control_mask.sum())
    payment_errors[treatment_mask] = np.random.binomial(1, 0.012, size=treatment_mask.sum())
    df["payment_error"] = payment_errors

    # 5. Guardrails: Refund or Cancelled
    refunds = np.zeros(num_users, dtype=int)
    refunds[control_mask] = np.random.binomial(1, 0.008, size=control_mask.sum())
    refunds[treatment_mask] = np.random.binomial(1, 0.008, size=treatment_mask.sum())
    df["refund_or_cancelled"] = refunds

    # 6. Checkout Duration
    durations = np.zeros(num_users)
    durations[control_mask] = np.random.normal(loc=120, scale=30, size=control_mask.sum())
    durations[treatment_mask] = np.random.normal(loc=100, scale=25, size=treatment_mask.sum())
    durations = np.maximum(durations, 20.0 + np.random.exponential(10, size=num_users))
    df["checkout_duration_seconds"] = np.round(durations, 1)

    if save_to_disk:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CSV_PATH, "w", encoding="utf-8") as f:
            f.write(DISCLAIMER_TEXT)
        df.to_csv(CSV_PATH, index=False, mode="a")

        metadata = {
            "experiment_name": EXPERIMENT_ID,
            "seed": seed,
            "population_size": num_users,
            "assumptions": {
                "allocation": "50/50 random assignment",
                "control_conversion_rate": 0.050,
                "treatment_conversion_rate": 0.057,
                "revenue_distribution": "lognormal(mu=3.8, sigma=0.8) for converters only",
                "control_payment_error_rate": 0.010,
                "treatment_payment_error_rate": 0.012,
                "control_checkout_duration_mean_sec": 120,
                "treatment_checkout_duration_mean_sec": 100
            },
            "disclaimer": DISCLAIMER_TEXT.strip()
        }
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
        
        print(f"Generated {num_users} users and saved to {CSV_PATH}")
        print(f"Saved metadata to {META_PATH}")
        
    return df

if __name__ == "__main__":
    generate_data(save_to_disk=True)
