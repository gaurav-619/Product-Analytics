import pandas as pd
import numpy as np
import scipy.stats as stats
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
import os

# Configuration Constants
ALPHA = 0.05
MIN_PRACTICAL_LIFT = 0.005
MAX_PAYMENT_ERROR_INC = 0.002
MAX_REFUND_INC = 0.002

DISCLAIMER_TEXT = "SIMULATED EXPERIMENT DATA - Educational demonstration of experimentation analysis. This is not GA4 data and is not evidence of real business impact."
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_PATH = os.path.join(ROOT_DIR, "data", "simulated", "checkout_experiment_simulated.csv")
ARTIFACTS_DIR = os.path.join(ROOT_DIR, "artifacts", "simulated_experiment")

def load_data():
    # Read the file, skip the first row (the disclaimer comment)
    df = pd.read_csv(DATA_PATH, skiprows=1)
    return df

def run_validations(df):
    checks = []
    
    # 1. Verify every user has exactly one variant assignment
    multi_variant_users = df.groupby('user_id')['variant'].nunique()
    passed_1 = (multi_variant_users == 1).all()
    checks.append(f"1. Single variant per user: {'✅ Passed' if passed_1 else '❌ Failed'}")

    # 2. Verify variant contains only control or treatment
    valid_variants = set(df['variant'].unique()) == {'control', 'treatment'}
    checks.append(f"2. Valid variants only: {'✅ Passed' if valid_variants else '❌ Failed'}")

    # 3. Verify all users are eligible and mobile
    eligible_mobile = (df['is_eligible'] == True).all() and (df['device_category'] == 'mobile').all()
    checks.append(f"3. All users eligible & mobile: {'✅ Passed' if eligible_mobile else '❌ Failed'}")

    # 4. Verify revenue is non-negative
    non_neg_revenue = (df['revenue_usd'] >= 0).all()
    checks.append(f"4. Non-negative revenue: {'✅ Passed' if non_neg_revenue else '❌ Failed'}")

    # 5. Verify non-converters have zero revenue
    non_conv = df[df['converted_purchase'] == 0]
    zero_rev = (non_conv['revenue_usd'] == 0).all()
    checks.append(f"5. Non-converters have 0 revenue: {'✅ Passed' if zero_rev else '❌ Failed'}")

    # 6. Check allocation balance (SRM Check)
    n_total = len(df)
    n_control = len(df[df['variant'] == 'control'])
    n_treatment = len(df[df['variant'] == 'treatment'])
    
    # Chi-square test against 50/50 expected split
    _, p_srm = stats.chisquare([n_control, n_treatment], f_exp=[n_total/2, n_total/2])
    passed_srm = p_srm > 0.001
    checks.append(f"6. SRM Check (p={p_srm:.4f}): {'✅ Passed' if passed_srm else '❌ SRM Detected'}")

    return checks

def calculate_sample_size_guidance(baseline_cvr, mde, alpha=0.05, power=0.80):
    """
    Valid sample-size calculation for a two-proportion experiment.
    Note: This is planning guidance, not proof that the simulation has sufficient power.
    """
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    p1 = baseline_cvr
    p2 = baseline_cvr + mde
    
    # Formula: n = (Z_a/2 + Z_b)^2 * (p1(1-p1) + p2(1-p2)) / (p2 - p1)^2
    n = ((z_alpha + z_beta)**2 * (p1 * (1 - p1) + p2 * (1 - p2))) / (mde**2)
    return int(np.ceil(n))

def analyze_experiment(df=None, save_to_disk=False) -> dict:
    print("Running Experiment Analysis...")
    if df is None:
        df = load_data()
    
    validations = run_validations(df)
    
    control = df[df['variant'] == 'control']
    treat = df[df['variant'] == 'treatment']
    
    n_c = len(control)
    n_t = len(treat)
    total_users = n_c + n_t
    
    conv_c = control['converted_purchase'].sum()
    conv_t = treat['converted_purchase'].sum()
    
    cvr_c = conv_c / n_c
    cvr_t = conv_t / n_t
    
    abs_lift = cvr_t - cvr_c
    rel_lift = (cvr_t - cvr_c) / cvr_c if cvr_c > 0 else 0
    
    # 2-proportion z-test and CI
    count = np.array([conv_t, conv_c])
    nobs = np.array([n_t, n_c])
    
    stat, p_val = proportions_ztest(count, nobs)
    (ci_low_t, ci_low_c), (ci_upp_t, ci_upp_c) = proportion_confint(count, nobs, alpha=ALPHA, method='normal')
    
    diff_ci_low = ci_low_t - ci_upp_c
    diff_ci_upp = ci_upp_t - ci_low_c
    
    # Guardrails
    arpu_c = control['revenue_usd'].sum() / n_c
    arpu_t = treat['revenue_usd'].sum() / n_t
    
    err_c = control['payment_error'].mean()
    err_t = treat['payment_error'].mean()
    err_inc = err_t - err_c
    
    ref_c = control['refund_or_cancelled'].mean()
    ref_t = treat['refund_or_cancelled'].mean()
    ref_inc = ref_t - ref_c
    
    dur_c = control['checkout_duration_seconds'].median()
    dur_t = treat['checkout_duration_seconds'].median()
    
    # Sample Size Calculation Guidance
    required_n = calculate_sample_size_guidance(cvr_c, MIN_PRACTICAL_LIFT, ALPHA, 0.80)
    
    # Decision Logic
    is_lift_positive = abs_lift > 0
    is_stat_sig_positive = diff_ci_low > 0
    is_stat_sig_negative = diff_ci_upp < 0
    meets_mde = abs_lift >= MIN_PRACTICAL_LIFT
    safe_errors = err_inc <= MAX_PAYMENT_ERROR_INC
    safe_refunds = ref_inc <= MAX_REFUND_INC
    
    if is_lift_positive and is_stat_sig_positive and meets_mde and safe_errors and safe_refunds:
        decision = "Ship"
        reason = "Primary metric significantly improved beyond MDE. Guardrails hold."
    elif is_lift_positive and (not safe_errors or not safe_refunds):
        decision = "Iterate"
        reason = "Conversion improved, but guardrails were harmed. Iterate on the design."
    elif is_stat_sig_negative:
        decision = "Stop"
        reason = "Treatment significantly harmed conversion."
    else:
        decision = "Inconclusive"
        reason = "Insufficient evidence to ship. Consider running longer if business case warrants."

    # Generate Report
    report_md = f"""# Experiment Report: mobile_checkout_simplification_v1

## 1. Summary
* **Recommendation:** {decision}
* **Reason:** {reason}
* **Users Analyzed:** {total_users:,}

## 2. Validations & SRM
"""
    for v in validations:
        report_md += f"* {v}\n"
        
    report_md += f"""
## 3. Primary Metric: Session Conversion Rate
| Metric | Control | Treatment | Lift | P-Value |
|--------|---------|-----------|------|---------|
| Conversion Rate | {cvr_c:.2%} | {cvr_t:.2%} | {abs_lift*100:+.2f} pp | {p_val:.4f} |
| 95% CI (Lift) | - | - | [{diff_ci_low*100:+.2f}%, {diff_ci_upp*100:+.2f}%] | - |

## 4. Guardrails & Secondary Metrics
| Metric | Control | Treatment | Absolute Diff |
|--------|---------|-----------|---------------|
| Revenue per User | ${arpu_c:.2f} | ${arpu_t:.2f} | ${(arpu_t - arpu_c):.2f} |
| Payment Error Rate | {err_c:.2%} | {err_t:.2%} | {(err_inc)*100:.2f} pp |
| Refund/Cancel Rate | {ref_c:.2%} | {ref_t:.2%} | {(ref_inc)*100:.2f} pp |
| Median Checkout Duration | {dur_c:.1f}s | {dur_t:.1f}s | {(dur_t - dur_c):.1f}s |

## 5. Sample Size Guidance
To detect a minimum practical lift of {MIN_PRACTICAL_LIFT*100:.2f}pp off a baseline of {cvr_c:.2%} 
(with 80% power and alpha={ALPHA}), the required sample size is **{required_n:,} users per variant**.
*(Note: This is planning guidance, not proof that this simulation has sufficient power).*
"""

    summary_df = pd.DataFrame([{
        "metric": "conversion_rate",
        "control": cvr_c,
        "treatment": cvr_t,
        "absolute_lift": abs_lift,
        "p_value": p_val,
        "decision": decision,
        "reason": reason
    }])
    
    guardrails_df = pd.DataFrame([
        {"metric": "arpu", "control": arpu_c, "treatment": arpu_t},
        {"metric": "payment_error_rate", "control": err_c, "treatment": err_t},
        {"metric": "refund_rate", "control": ref_c, "treatment": ref_t},
        {"metric": "median_duration", "control": dur_c, "treatment": dur_t},
    ])

    import plotly.express as px
    import plotly.graph_objects as go
    
    # 1. Conversion Comparison Chart
    fig_conv = px.bar(
        summary_df, 
        x="metric", 
        y=["control", "treatment"], 
        barmode="group",
        title="Conversion Rate by Variant",
        labels={"value": "Conversion Rate", "variable": "Variant"}
    )
    fig_conv.update_yaxes(tickformat=".2%")
    
    # 2. Revenue Distribution (Converters Only)
    converters = df[df['converted_purchase'] == 1]
    fig_rev = px.histogram(
        converters, 
        x="revenue_usd", 
        color="variant", 
        barmode="overlay",
        title="Revenue Distribution (Converters Only)",
        nbins=50
    )

    if save_to_disk:
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        with open(os.path.join(ARTIFACTS_DIR, "experiment_report.md"), "w", encoding="utf-8") as f:
            f.write(report_md)
        summary_df.to_csv(os.path.join(ARTIFACTS_DIR, "experiment_summary.csv"), index=False)
        guardrails_df.to_csv(os.path.join(ARTIFACTS_DIR, "guardrails_by_variant.csv"), index=False)
        fig_conv.write_html(os.path.join(ARTIFACTS_DIR, "conversion_comparison.html"))
        fig_rev.write_html(os.path.join(ARTIFACTS_DIR, "revenue_distribution.html"))
        print("Analysis complete. Artifacts saved to artifacts/simulated_experiment/")
        
    return {
        "summary_df": summary_df,
        "guardrails_df": guardrails_df,
        "report_md": report_md,
        "fig_conv": fig_conv,
        "fig_rev": fig_rev,
        "validations": validations
    }

if __name__ == "__main__":
    analyze_experiment(save_to_disk=True)
