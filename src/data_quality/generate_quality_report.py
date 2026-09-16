"""
Data Quality Report Generator

Queries BigQuery to inspect the GA4 source data and dbt-built marts,
then writes a structured Markdown report to docs/data_quality_report_generated.md.

This does NOT overwrite the curated docs/data_quality_report.md template.

Usage:
    python -m src.data_quality.generate_quality_report
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from src.config import (
    BQ_DATASET,
    FULLY_QUALIFIED_DATASET,
    GA4_SOURCE_TABLE,
    GA4_START_DATE,
    GA4_END_DATE,
)
from src.bigquery_client import query_to_dataframe, table_exists


def _section(title: str) -> str:
    return f"\n## {title}\n"


def _check_source_coverage() -> str:
    """Profile the GA4 source data within the configured date range."""
    sql = f"""
    select
        count(*) as total_events,
        min(event_date) as earliest_date,
        max(event_date) as latest_date,
        count(distinct event_date) as distinct_dates,
        count(distinct user_pseudo_id) as distinct_users
    from `{GA4_SOURCE_TABLE}`
    where _table_suffix between '{GA4_START_DATE}' and '{GA4_END_DATE}'
    """
    df = query_to_dataframe(sql)
    if df.empty:
        return "⚠️ No data returned from source query.\n"

    row = df.iloc[0]
    return (
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Total events | {row['total_events']:,} |\n"
        f"| Date range | {row['earliest_date']} — {row['latest_date']} |\n"
        f"| Distinct dates | {row['distinct_dates']} |\n"
        f"| Distinct users | {row['distinct_users']:,} |\n"
    )


def _check_event_inventory() -> str:
    """List all event names with counts."""
    sql = f"""
    select
        event_name,
        count(*) as event_count
    from `{GA4_SOURCE_TABLE}`
    where _table_suffix between '{GA4_START_DATE}' and '{GA4_END_DATE}'
    group by event_name
    order by event_count desc
    """
    df = query_to_dataframe(sql)
    if df.empty:
        return "⚠️ No events found.\n"

    lines = ["| Event Name | Count |", "|-----------|-------|"]
    for _, row in df.iterrows():
        lines.append(f"| {row['event_name']} | {row['event_count']:,} |")
    return "\n".join(lines) + "\n"


def _check_null_rates() -> str:
    """Check null rates for critical fields in the source."""
    sql = f"""
    select
        count(*) as total,
        countif(user_pseudo_id is null) as null_user_id,
        countif(event_name is null) as null_event_name,
        countif(event_timestamp is null) as null_timestamp,
        countif(
            (select ep.value.int_value from unnest(event_params) ep
             where ep.key = 'ga_session_id' limit 1) is null
        ) as null_session_id,
        countif(ecommerce.transaction_id is null) as null_ecom_txn_id
    from `{GA4_SOURCE_TABLE}`
    where _table_suffix between '{GA4_START_DATE}' and '{GA4_END_DATE}'
    """
    df = query_to_dataframe(sql)
    if df.empty:
        return "⚠️ Could not check null rates.\n"

    row = df.iloc[0]
    total = row["total"]
    lines = ["| Field | Null Count | Null Rate |", "|-------|-----------|-----------|"]
    for col in ["null_user_id", "null_event_name", "null_timestamp", "null_session_id", "null_ecom_txn_id"]:
        label = col.replace("null_", "")
        count = row[col]
        rate = count / total if total > 0 else 0
        lines.append(f"| {label} | {count:,} | {rate:.2%} |")
    return "\n".join(lines) + "\n"


def _check_duplicate_transactions() -> str:
    """Check for duplicate transaction IDs in source purchase events."""
    sql = f"""
    select
        ecommerce.transaction_id as txn_id,
        count(*) as event_count
    from `{GA4_SOURCE_TABLE}`
    where _table_suffix between '{GA4_START_DATE}' and '{GA4_END_DATE}'
      and event_name = 'purchase'
      and ecommerce.transaction_id is not null
    group by ecommerce.transaction_id
    having count(*) > 1
    order by event_count desc
    limit 10
    """
    df = query_to_dataframe(sql)
    if df.empty:
        return "✅ No duplicate transaction IDs found in source purchase events.\n"

    lines = [
        f"⚠️ Found {len(df)} transaction IDs with duplicate purchase events (showing top 10):\n",
        "| Transaction ID | Event Count |",
        "|---------------|-------------|",
    ]
    for _, row in df.iterrows():
        lines.append(f"| {row['txn_id']} | {row['event_count']} |")
    lines.append("\nNote: int_orders deduplicates by keeping the earliest purchase event per transaction.")
    return "\n".join(lines) + "\n"


def _check_mart_row_counts() -> str:
    """Check row counts in dbt mart tables."""
    marts = [
        "mart_product_kpis_daily",
        "mart_funnel_performance",
        "mart_retention_cohorts",
        "mart_customer_rfm",
        "mart_segment_performance",
        "mart_product_performance",
    ]

    lines = ["| Mart | Row Count |", "|------|-----------|"]
    for mart in marts:
        if not table_exists(BQ_DATASET, mart):
            lines.append(f"| {mart} | ❌ Table not found |")
            continue
        sql = f"select count(*) as cnt from `{FULLY_QUALIFIED_DATASET}.{mart}`"
        df = query_to_dataframe(sql)
        if df.empty:
            lines.append(f"| {mart} | ⚠️ Query failed |")
        else:
            lines.append(f"| {mart} | {df.iloc[0]['cnt']:,} |")
    return "\n".join(lines) + "\n"


def _check_revenue_totals() -> str:
    """Compare revenue totals between source and int_orders."""
    if not table_exists(BQ_DATASET, "int_orders"):
        return "⚠️ int_orders table not found. Run dbt build first.\n"

    sql = f"""
    with orders_total as (
        select sum(order_revenue_usd) as total
        from `{FULLY_QUALIFIED_DATASET}.int_orders`
    ),
    source_total as (
        select sum(coalesce(ecommerce.purchase_revenue_in_usd, ecommerce.purchase_revenue, 0)) as total
        from `{GA4_SOURCE_TABLE}`
        where _table_suffix between '{GA4_START_DATE}' and '{GA4_END_DATE}'
          and event_name = 'purchase'
          and coalesce(ecommerce.transaction_id,
              (select ep.value.string_value from unnest(event_params) ep where ep.key = 'transaction_id' limit 1)
          ) is not null
    )
    select
        o.total as orders_revenue,
        s.total as source_revenue,
        abs(o.total - s.total) as absolute_diff,
        safe_divide(abs(o.total - s.total), nullif(s.total, 0)) as relative_diff
    from orders_total o
    cross join source_total s
    """
    df = query_to_dataframe(sql)
    if df.empty:
        return "⚠️ Revenue comparison query returned no results.\n"

    row = df.iloc[0]
    return (
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| int_orders total revenue (USD) | ${row['orders_revenue']:,.2f} |\n"
        f"| Source purchase revenue (USD) | ${row['source_revenue']:,.2f} |\n"
        f"| Absolute difference | ${row['absolute_diff']:,.2f} |\n"
        f"| Relative difference | {row['relative_diff']:.4%} |\n"
    )


def generate_report() -> None:
    """Generate the complete data quality report."""
    output_path = Path(__file__).resolve().parent.parent.parent / "docs" / "data_quality_report_generated.md"

    print("📊 Generating data quality report...")
    print(f"   Source date range: {GA4_START_DATE} — {GA4_END_DATE}")

    sections = [
        f"# Data Quality Report (Generated)\n",
        f"> Auto-generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"> Date range: {GA4_START_DATE} — {GA4_END_DATE}\n",
        "> **This is an auto-generated report. See docs/data_quality_report.md for the curated checklist.**\n",
        _section("1. Source Coverage"),
        _check_source_coverage(),
        _section("2. Event Inventory"),
        _check_event_inventory(),
        _section("3. Null Rates (Critical Fields)"),
        _check_null_rates(),
        _section("4. Duplicate Transaction IDs"),
        _check_duplicate_transactions(),
        _section("5. Mart Row Counts"),
        _check_mart_row_counts(),
        _section("6. Revenue Reconciliation"),
        _check_revenue_totals(),
    ]

    report = "\n".join(sections)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ Report saved to {output_path}")


if __name__ == "__main__":
    try:
        generate_report()
    except Exception as e:
        print(f"❌ Failed to generate quality report: {e}", file=sys.stderr)
        sys.exit(1)
