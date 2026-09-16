"""
Verified Findings Generator

Queries the dbt marts and generates a structured Markdown document
with descriptive, observational findings. All findings are templated
from actual query results — no hard-coded claims.

Critical rules:
- All findings are labeled as descriptive/observational
- No causal language
- No invented monetary impacts
- If a query returns no rows, the finding says so explicitly

Usage:
    python -m src.analysis.generate_verified_findings
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from src.config import BQ_DATASET, FULLY_QUALIFIED_DATASET
from src.bigquery_client import query_to_dataframe, table_exists


def _section(title: str) -> str:
    return f"\n## {title}\n"


def _finding_kpis() -> str:
    """Summary KPIs from mart_product_kpis_daily."""
    if not table_exists(BQ_DATASET, "mart_product_kpis_daily"):
        return "⚠️ mart_product_kpis_daily not found. Run `dbt build` first.\n"

    sql = f"""
    select
        min(report_date) as start_date,
        max(report_date) as end_date,
        sum(daily_active_users) as total_user_days,
        sum(total_sessions) as total_sessions,
        sum(total_orders) as total_orders,
        sum(total_revenue_usd) as total_revenue_usd,
        safe_divide(sum(total_orders), sum(total_sessions)) as overall_session_conversion,
        safe_divide(sum(total_revenue_usd), nullif(sum(total_orders), 0)) as overall_aov
    from `{FULLY_QUALIFIED_DATASET}.mart_product_kpis_daily`
    """
    df = query_to_dataframe(sql)
    if df.empty:
        return "⚠️ No KPI data available.\n"

    r = df.iloc[0]
    return (
        f"**Observation period:** {r['start_date']} to {r['end_date']}\n\n"
        f"| Metric | Observed Value |\n"
        f"|--------|----------------|\n"
        f"| Total user-days (sum of daily active users) | {r['total_user_days']:,.0f} |\n"
        f"| Total sessions | {r['total_sessions']:,.0f} |\n"
        f"| Total orders | {r['total_orders']:,.0f} |\n"
        f"| Total revenue (USD) | ${r['total_revenue_usd']:,.2f} |\n"
        f"| Overall session conversion rate | {r['overall_session_conversion']:.2%} |\n"
        f"| Overall AOV (USD) | ${r['overall_aov']:,.2f} |\n\n"
        f"*These are descriptive statistics for the observation period. "
        f"They should not be extrapolated without accounting for seasonality, "
        f"data completeness, and sample representativeness.*\n"
    )


def _finding_funnel() -> str:
    """Aggregate sequential funnel from mart_funnel_performance."""
    if not table_exists(BQ_DATASET, "mart_funnel_performance"):
        return "⚠️ mart_funnel_performance not found. Run `dbt build` first.\n"

    sql = f"""
    select
        sum(sessions_entered) as sessions_entered,
        sum(sessions_product_view) as sessions_product_view,
        sum(sessions_add_to_cart) as sessions_add_to_cart,
        sum(sessions_begin_checkout) as sessions_begin_checkout,
        sum(sessions_purchase) as sessions_purchase
    from `{FULLY_QUALIFIED_DATASET}.mart_funnel_performance`
    """
    df = query_to_dataframe(sql)
    if df.empty:
        return "⚠️ No funnel data available.\n"

    r = df.iloc[0]
    entered = r["sessions_entered"]
    steps = [
        ("Sessions entered", r["sessions_entered"]),
        ("Product view", r["sessions_product_view"]),
        ("Add to cart", r["sessions_add_to_cart"]),
        ("Begin checkout", r["sessions_begin_checkout"]),
        ("Purchase", r["sessions_purchase"]),
    ]

    lines = [
        "**Sequential funnel (strict temporal ordering):**\n",
        "| Step | Sessions | % of Entered |",
        "|------|----------|-------------|",
    ]
    for name, count in steps:
        pct = count / entered if entered > 0 else 0
        lines.append(f"| {name} | {count:,.0f} | {pct:.2%} |")

    lines.append(
        "\n*This is a strict sequential funnel: each step requires the previous step "
        "to have occurred first within the same session. See docs/metric_definitions.md.*"
    )
    return "\n".join(lines) + "\n"


def _finding_segments() -> str:
    """Device and search segment comparison."""
    if not table_exists(BQ_DATASET, "mart_segment_performance"):
        return "⚠️ mart_segment_performance not found. Run `dbt build` first.\n"

    sql = f"""
    select
        segment_type,
        segment_value,
        unique_users,
        total_sessions,
        total_revenue_usd,
        session_conversion_rate,
        avg_order_value_usd
    from `{FULLY_QUALIFIED_DATASET}.mart_segment_performance`
    where segment_type in ('device_category', 'search_adoption')
    order by segment_type, total_sessions desc
    """
    df = query_to_dataframe(sql)
    if df.empty:
        return "⚠️ No segment data available.\n"

    lines = [
        "| Segment | Value | Users | Sessions | Revenue (USD) | Session CVR | AOV (USD) |",
        "|---------|-------|-------|----------|--------------|-------------|-----------|",
    ]
    for _, r in df.iterrows():
        revenue = r["total_revenue_usd"] if r["total_revenue_usd"] else 0
        cvr = r["session_conversion_rate"] if r["session_conversion_rate"] else 0
        aov = r["avg_order_value_usd"] if r["avg_order_value_usd"] else 0
        lines.append(
            f"| {r['segment_type']} | {r['segment_value']} | "
            f"{r['unique_users']:,.0f} | {r['total_sessions']:,.0f} | "
            f"${revenue:,.2f} | {cvr:.2%} | ${aov:,.2f} |"
        )
    lines.append(
        "\n> **Note on search adoption:** The difference in conversion rates between "
        "search and non-search sessions is an *observed association*. Users who search "
        "may have higher purchase intent to begin with. This does NOT establish that "
        "search *causes* higher conversion. See docs/experiment_design.md for a rigorous "
        "test proposal."
    )
    return "\n".join(lines) + "\n"


def _finding_rfm() -> str:
    """RFM segment distribution."""
    if not table_exists(BQ_DATASET, "mart_customer_rfm"):
        return "⚠️ mart_customer_rfm not found. Run `dbt build` first.\n"

    sql = f"""
    select
        rfm_segment,
        count(*) as customer_count,
        sum(monetary_value_usd) as total_revenue_usd,
        avg(frequency) as avg_frequency,
        avg(recency_days) as avg_recency_days
    from `{FULLY_QUALIFIED_DATASET}.mart_customer_rfm`
    group by rfm_segment
    order by total_revenue_usd desc
    """
    df = query_to_dataframe(sql)
    if df.empty:
        return "⚠️ No RFM data available.\n"

    lines = [
        "| Segment | Customers | Revenue (USD) | Avg Frequency | Avg Recency (days) |",
        "|---------|-----------|--------------|---------------|-------------------|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['rfm_segment']} | {r['customer_count']:,.0f} | "
            f"${r['total_revenue_usd']:,.2f} | {r['avg_frequency']:.1f} | "
            f"{r['avg_recency_days']:.0f} |"
        )
    lines.append(
        "\n*RFM segments are based on NTILE(5) quintile scoring within the observation period. "
        "Segment definitions are in docs/metric_definitions.md.*"
    )
    return "\n".join(lines) + "\n"


def _finding_retention() -> str:
    """Retention summary for the earliest cohorts."""
    if not table_exists(BQ_DATASET, "mart_retention_cohorts"):
        return "⚠️ mart_retention_cohorts not found. Run `dbt build` first.\n"

    sql = f"""
    select
        activity_week_index,
        sum(retained_users) as total_retained,
        sum(cohort_size) as total_cohort_size,
        safe_divide(sum(retained_users), sum(cohort_size)) as avg_retention_rate
    from `{FULLY_QUALIFIED_DATASET}.mart_retention_cohorts`
    where activity_week_index <= 8
    group by activity_week_index
    order by activity_week_index
    """
    df = query_to_dataframe(sql)
    if df.empty:
        return "⚠️ No retention data available.\n"

    lines = [
        "**Aggregate weekly retention (all cohorts combined):**\n",
        "| Week | Retained Users | Cohort Size | Retention Rate |",
        "|------|---------------|-------------|---------------|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| Week {r['activity_week_index']:.0f} | "
            f"{r['total_retained']:,.0f} | {r['total_cohort_size']:,.0f} | "
            f"{r['avg_retention_rate']:.2%} |"
        )
    lines.append(
        "\n*This is observed activity retention within the data window. "
        "Users may return outside this window. See docs/limitations.md.*"
    )
    return "\n".join(lines) + "\n"


def generate_findings() -> None:
    """Generate the verified findings document."""
    output_path = Path(__file__).resolve().parent.parent.parent / "docs" / "verified_findings_generated.md"

    print("🔍 Generating verified findings...")

    sections = [
        "# Verified Findings (Generated)\n",
        f"> Auto-generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        "> All findings below are **descriptive and observational**. They describe "
        "patterns in the data but do not establish causal relationships.\n",
        "> Source: Google's public, obfuscated GA4 Google Merchandise Store sample dataset.\n",
        _section("1. Summary KPIs"),
        _finding_kpis(),
        _section("2. Sequential Funnel Analysis"),
        _finding_funnel(),
        _section("3. Segment Comparison"),
        _finding_segments(),
        _section("4. Customer Segmentation (RFM)"),
        _finding_rfm(),
        _section("5. Weekly Activity Retention"),
        _finding_retention(),
        _section("6. Next Steps"),
        "Based on the above findings:\n\n"
        "1. Review the funnel drop-off points to identify the largest friction areas\n"
        "2. Investigate device-specific conversion differences\n"
        "3. Evaluate whether the search-adoption association warrants an experiment "
        "(see docs/experiment_design.md)\n"
        "4. Examine at-risk RFM segments for re-engagement opportunities\n"
        "5. All recommendations should be validated with additional qualitative research "
        "before implementation\n",
    ]

    report = "\n".join(sections)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"✅ Findings saved to {output_path}")


if __name__ == "__main__":
    try:
        generate_findings()
    except Exception as e:
        print(f"❌ Failed to generate findings: {e}", file=sys.stderr)
        sys.exit(1)
