"""
Page 2: Funnel Analysis
Sequential funnel visualization and device-level comparison.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.utils import (
    load_mart,
    show_setup_instructions,
    format_pct,
    format_number,
    add_methodology_note,
    inject_custom_css,
    apply_global_filters,
)

st.set_page_config(page_title="Funnel Analysis", page_icon="🔽", layout="wide")
inject_custom_css()
st.title("🔽 Funnel Analysis")

st.info(
    "**Strict sequential funnel:** Each step requires the previous step to have "
    "occurred first within the same session. This is more conservative than "
    "simple presence-based funnel counts."
)

# Load data
df = load_mart("mart_funnel_performance")

if df is None or df.empty:
    show_setup_instructions()
    st.stop()

# Apply Global Filters
df = apply_global_filters(df, "report_date")

if df.empty:
    st.warning("No data found for this segment combination.")
    st.stop()

# ── Aggregate Funnel ─────────────────────────────────────────────────────

st.subheader("Aggregate Sequential Funnel")

agg = df.groupby(level=0).agg({
    "sessions_entered": "sum",
    "sessions_product_view": "sum",
    "sessions_add_to_cart": "sum",
    "sessions_begin_checkout": "sum",
    "sessions_purchase": "sum",
}).sum()

funnel_steps = ["Sessions Entered", "Product View", "Add to Cart", "Begin Checkout", "Purchase"]
funnel_values = [
    agg["sessions_entered"],
    agg["sessions_product_view"],
    agg["sessions_add_to_cart"],
    agg["sessions_begin_checkout"],
    agg["sessions_purchase"],
]

fig = go.Figure(go.Funnel(
    y=funnel_steps,
    x=funnel_values,
    textinfo="value+percent initial+percent previous",
    marker=dict(color=["#00F0FF", "#00C3FF", "#0096FF", "#0069FF", "#003CFF"]),
    connector={"line": {"color": "rgba(255,255,255,0.1)", "dash": "dot", "width": 2}}
))
fig.update_layout(
    title="Purchase Funnel (Sequential)", 
    height=500,
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)

# Find biggest drop-off
drop_offs = []
for i in range(1, len(funnel_values)):
    if funnel_values[i-1] > 0:
        drop_rate = 1 - (funnel_values[i] / funnel_values[i-1])
        drop_offs.append((funnel_steps[i-1], funnel_steps[i], drop_rate, funnel_values[i], i))

worst_step_name = ""
worst_drop_rate = 0.0

if drop_offs:
    worst_drop = max(drop_offs, key=lambda x: x[2])
    worst_drop_rate = worst_drop[2]
    worst_step_name = f"{worst_drop[0]} → {worst_drop[1]}"
    
    # Add annotation to chart
    fig.add_annotation(
        x=worst_drop[3], 
        y=worst_drop[4], # Use y index
        text=f"Largest Drop-off: {format_pct(worst_drop_rate)}",
        showarrow=True,
        arrowhead=1,
        arrowcolor="#E74C3C",
        font=dict(color="#E74C3C", size=12),
        ax=40,
        ay=0
    )

st.plotly_chart(fig, use_container_width=True)

# Step-to-step rates
entered = agg["sessions_entered"]
if entered > 0:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Session → View",
        format_pct(agg["sessions_product_view"] / entered),
    )
    col2.metric(
        "View → Cart",
        format_pct(
            agg["sessions_add_to_cart"] / agg["sessions_product_view"]
            if agg["sessions_product_view"] > 0 else 0
        ),
    )
    col3.metric(
        "Cart → Checkout",
        format_pct(
            agg["sessions_begin_checkout"] / agg["sessions_add_to_cart"]
            if agg["sessions_add_to_cart"] > 0 else 0
        ),
    )
    col4.metric(
        "Checkout → Purchase",
        format_pct(
            agg["sessions_purchase"] / agg["sessions_begin_checkout"]
            if agg["sessions_begin_checkout"] > 0 else 0
        ),
    )

st.markdown("---")

# ── By Device ────────────────────────────────────────────────────────────

st.subheader("Funnel by Device Category")

device_agg = df.groupby("device_category").agg({
    "sessions_entered": "sum",
    "sessions_product_view": "sum",
    "sessions_add_to_cart": "sum",
    "sessions_begin_checkout": "sum",
    "sessions_purchase": "sum",
}).reset_index()

# Melt for grouped bar chart
device_melted = device_agg.melt(
    id_vars="device_category",
    value_vars=[
        "sessions_entered", "sessions_product_view",
        "sessions_add_to_cart", "sessions_begin_checkout", "sessions_purchase",
    ],
    var_name="funnel_step",
    value_name="sessions",
)

step_labels = {
    "sessions_entered": "Entered",
    "sessions_product_view": "Product View",
    "sessions_add_to_cart": "Add to Cart",
    "sessions_begin_checkout": "Checkout",
    "sessions_purchase": "Purchase",
}
device_melted["funnel_step"] = device_melted["funnel_step"].map(step_labels)

fig = px.bar(
    device_melted,
    x="funnel_step", y="sessions", color="device_category",
    barmode="group",
    title="Funnel Steps by Device",
    labels={"sessions": "Sessions", "funnel_step": "Funnel Step"},
    category_orders={"funnel_step": list(step_labels.values())},
    color_discrete_sequence=["#00F0FF", "#B388FF", "#FF4081", "#00E676"]
)
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(gridcolor="rgba(255,255,255,0.1)")
)
st.plotly_chart(fig, use_container_width=True)

# ── So What? ─────────────────────────────────────────────────────────────

st.subheader("Key Observations")

total_entered = int(agg["sessions_entered"])
total_purchased = int(agg["sessions_purchase"])
overall_rate = total_purchased / total_entered if total_entered > 0 else 0

st.markdown(
    f"Of **{format_number(total_entered)}** sessions that entered the funnel, "
    f"**{format_number(total_purchased)}** completed a purchase "
    f"(**{format_pct(overall_rate)}** overall sequential conversion). "
)

if worst_step_name:
    st.markdown(
        f"**Critical Bottleneck:** The largest sequential drop-off occurs at **{worst_step_name}**, "
        f"where **{format_pct(worst_drop_rate)}** of users abandon their journey. "
        f"This indicates a high-priority area for UX investigation and potential A/B testing."
    )

st.caption(
    "This is a strict sequential funnel — each step requires the previous step. "
    "Non-sequential behavior (e.g., direct add-to-cart without product view) is excluded. "
    "See docs/metric_definitions.md for full methodology."
)

add_methodology_note()
