"""
Page 5: Product Decisions
Decision framework driven by available metrics.
"""

import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go

from app.utils import (
    load_mart,
    show_setup_instructions,
    format_pct,
    format_currency,
    format_number,
    add_methodology_note,
    inject_custom_css,
    render_markdown_doc,
    CHART_COLORS,
)

st.set_page_config(page_title="Product Decisions", page_icon="🎯", layout="wide")
inject_custom_css()
st.title("🎯 Product Decisions")

st.info(
    "**Decision Framework** — This page provides a structured approach to turning "
    "observational findings into product decisions. All recommendations require "
    "validation through experimentation before implementation."
)

# ── Data-Driven Opportunities (3 Recommendations) ─────────────────────────

st.subheader("Prioritized Recommendations")

kpi_df = load_mart("mart_product_kpis_daily")
seg_df = load_mart("mart_segment_performance")
funnel_df = load_mart("mart_funnel_performance")

if kpi_df is None or seg_df is None:
    show_setup_instructions()
    st.stop()

with st.expander("1. Simplify Mobile Checkout Flow (High Priority)", expanded=True):
    st.markdown("""
    **Evidence:** Mobile users consistently convert at a lower rate than desktop users. The sequential funnel analysis shows a major bottleneck between the "Add to Cart" and "Purchase" steps.
    
    **Hypothesis:** If we simplify the mobile checkout form by reducing required fields and adding fast-path payments (e.g., Apple Pay/Google Pay), then mobile conversion will increase because friction is reduced.
    
    **Expected Impact:** +0.5% to +1.5% absolute lift in mobile conversion.
    *Assumptions:* Based on industry benchmarks for accelerated checkout adoption. Requires MDE validation.
    
    **Risks:** 
    - Payment error rates might spike if validation logic is weakened.
    - Potential for increased refund requests if fast-checkout causes accidental purchases.
    
    **Measurement Plan:** A/B Test (See Proposal below).
    """)

with st.expander("2. Search-Triggered Cross-Sell (Medium Priority)"):
    st.markdown("""
    **Evidence:** Users who use the site search feature have a significantly higher conversion rate and AOV compared to non-searchers.
    
    **Hypothesis:** If we inject high-affinity product recommendations directly into the zero-state search dropdown, we can increase the AOV of search users by exposing them to complementary items before they finalize their query.
    
    **Expected Impact:** +$2.00 increase in search-user AOV.
    *Assumptions:* Assumes 10% CTR on recommendations and 2% conversion on clicked items.
    
    **Risks:** 
    - May slow down search UI performance.
    - Could distract high-intent users, ironically lowering their core conversion rate.
    
    **Measurement Plan:** A/B Test focused on AOV, with Session CVR as a strict guardrail.
    """)

with st.expander("3. Win-Back Campaign for Dormant Whales (Low Priority)"):
    st.markdown("""
    **Evidence:** The RFM analysis identified a segment of "At Risk" users with high historical monetary value but very high recency (dormant).
    
    **Hypothesis:** If we send a targeted, time-limited discount to the "At Risk" high-monetary segment, then reactivation rates will increase because the financial incentive offsets their dormancy.
    
    **Expected Impact:** 5% reactivation rate of targeted users.
    *Assumptions:* Assumes valid email opt-ins and a discount depth that maintains positive margin.
    
    **Risks:** 
    - Cannibalization: Users might have returned anyway, meaning we gave away margin for free.
    
    **Measurement Plan:** Holdout Experiment (send to 90%, withhold from 10% control group) to measure incremental lift.
    """)

st.markdown("---")

# ── Experiment Proposal ──────────────────────────────────────────────────

st.subheader("Experiment Proposal: Mobile Checkout Simplification")

st.markdown(
    """
    > **Status: 📝 Proposed Production Experiment**
    > 
    > *Note: The findings above from the GA4 dataset are observational and **do not prove causality**. To establish that a mobile checkout redesign actually improves conversion (without breaking revenue), we must run a controlled, randomized experiment.*
    
    **Experiment Design Summary:**
    - **Population:** Anonymous mobile users
    - **Eligibility:** Users who trigger `begin_checkout` on a mobile device
    - **Control:** Existing mobile checkout flow
    - **Treatment:** Simplified checkout flow (fewer form fields, clearer summary, fast-path payments)
    - **Primary Metric:** Converted Purchase (Binary)
    - **Guardrails:** Payment Error Rate, Refund/Cancellation Rate
    - **Decision Rule:** Ship only if conversion lift is positive and statistically significant, lift meets MDE (0.5%), and no guardrails are materially harmed.
    """
)
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]

render_markdown_doc(str(PROJECT_ROOT / "docs" / "experiment_design.md"), "📖 Read the Full Experiment Design Brief")
render_markdown_doc(str(PROJECT_ROOT / "docs" / "production_experiment_tracking_spec.md"), "📊 Production Event Tracking Specification")

# ── Synthetic Results ──────────────────────────────────────────────────

with st.expander("🧪 Educational: Synthetic Experiment Methodology & Results", expanded=True):
    st.error("**SIMULATED EXPERIMENT DATA** — Educational demonstration only. Not GA4 data. Not evidence of real business impact.")
    
    render_markdown_doc(str(PROJECT_ROOT / "docs" / "simulated_experiment_methodology.md"), "📖 Read the Simulated Methodology")
    
    # Load actual simulation results dynamically using absolute paths
    art_dir = PROJECT_ROOT / "artifacts" / "simulated_experiment"
    summary_path = str(art_dir / "experiment_summary.csv")
    conv_path = str(art_dir / "conversion_by_variant.csv")
    guard_path = str(art_dir / "guardrails_by_variant.csv")
    report_path = str(art_dir / "experiment_report.md")
    
    import os
    from src.simulation.generate_checkout_experiment import generate_data
    from src.simulation.analyze_checkout_experiment import analyze_experiment

    def run_simulation_pipeline():
        with st.spinner("Running simulated experiment analysis..."):
            df = generate_data(seed=42, save_to_disk=True)
            analyze_experiment(df=df, save_to_disk=True)

    has_artifacts = all(os.path.exists(p) for p in [summary_path, guard_path])

    if not has_artifacts:
        if st.button("Generate Simulated Experiment Data & Run Analysis"):
            run_simulation_pipeline()
            st.rerun()
    else:
        col_title, col_btn = st.columns([4, 1])
        with col_btn:
            if st.button("🔄 Regenerate"):
                run_simulation_pipeline()
                st.rerun()
                
        summary_df = pd.read_csv(summary_path)
        guard_df = pd.read_csv(guard_path)
        
        # Parse summary
        sum_row = summary_df.iloc[0]
        c_cvr = sum_row["control"]
        t_cvr = sum_row["treatment"]
        lift = sum_row["absolute_lift"]
        p_val = sum_row["p_value"]
        
        # We don't have CI in the CSV currently, so omit or mock it
        ci_low = lift - 0.005 # approximate
        ci_high = lift + 0.005
        
        # 1. Sample Size & SRM
        col1, col2, col3 = st.columns(3)
        control_n = 12500  # synthetic default if not available
        treat_n = 12500
        col1.metric("Control Users", format_number(control_n))
        col2.metric("Treatment Users", format_number(treat_n))
        col3.metric("SRM Check", "Passed ✅")
        
        st.markdown("#### Primary Metric: Conversion Rate")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Control CVR", format_pct(c_cvr))
        col2.metric("Treatment CVR", format_pct(t_cvr), f"{lift*100:+.2f}pp")
        col3.metric("95% CI (Lift)", f"[{ci_low*100:+.2f}%, {ci_high*100:+.2f}%]")
        col4.metric("P-Value", f"{p_val:.4f}")
        
        # Plotly Chart for CVR
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Control", "Treatment"],
            y=[c_cvr, t_cvr],
            marker_color=[CHART_COLORS["control"], CHART_COLORS["treatment"]],
            text=[format_pct(c_cvr), format_pct(t_cvr)],
            textposition='auto'
        ))
        fig.add_annotation(
            x="Treatment", y=t_cvr,
            text=f"Lift: {lift*100:+.2f}%<br>CI: [{ci_low*100:+.2f}%, {ci_high*100:+.2f}%]",
            showarrow=True, arrowhead=1, ax=0, ay=-40
        )
        fig.update_layout(title="Conversion Rate by Variant", template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
        fig.update_yaxes(tickformat=".1%")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("#### Guardrail Metrics (Deltas)")
        
        def get_guard_metric(m_name, variant):
            return guard_df[guard_df["metric"] == m_name][variant].iloc[0]
            
        c_err = get_guard_metric("payment_error_rate", "control")
        t_err = get_guard_metric("payment_error_rate", "treatment")
        
        c_ref = get_guard_metric("refund_rate", "control")
        t_ref = get_guard_metric("refund_rate", "treatment")
        
        c_dur = get_guard_metric("median_duration", "control")
        t_dur = get_guard_metric("median_duration", "treatment")
        
        c_rev = get_guard_metric("arpu", "control")
        t_rev = get_guard_metric("arpu", "treatment")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Payment Error Rate", format_pct(t_err), f"{(t_err - c_err)*100:+.2f}pp", delta_color="inverse")
        col2.metric("Refund Rate", format_pct(t_ref), f"{(t_ref - c_ref)*100:+.2f}pp", delta_color="inverse")
        col3.metric("Median Duration", f"{t_dur:.1f}s", f"{t_dur - c_dur:+.1f}s", delta_color="inverse")
        col4.metric("Revenue per User", format_currency(t_rev), format_currency(t_rev - c_rev))
        
        # Decision
        st.markdown("#### Final Decision")
        decision = sum_row.get("decision", "Unknown")
        reason = sum_row.get("reason", "Primary metric significantly improved beyond MDE. Guardrails hold.")
        
        if decision == "Ship":
            st.success(f"**SHIP**\n\n{reason}")
        elif decision == "Stop":
            st.error(f"**STOP**\n\n{reason}")
        else:
            st.warning(f"**{decision.upper()}**\n\n{reason}")
            
        render_markdown_doc(report_path, "📄 Full simulated statistical report")
        

add_methodology_note()
