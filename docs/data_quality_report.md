# Data Quality Report (Curated Template)

> This is the curated quality checklist. For auto-generated results, run:
> ```bash
> python -m src.data_quality.generate_quality_report
> ```
> This will create `docs/data_quality_report_generated.md` without overwriting this file.

---

## 1. Source Coverage

| Check | Status | Notes |
|-------|--------|-------|
| Event data present for configured date range | ⬜ | Run quality report |
| Total event count reasonable | ⬜ | |
| Distinct users > 0 | ⬜ | |
| No gaps in daily tables | ⬜ | Check distinct_dates vs expected |

## 2. Event Inventory

| Check | Status | Notes |
|-------|--------|-------|
| `page_view` events present | ⬜ | |
| `view_item` events present | ⬜ | |
| `add_to_cart` events present | ⬜ | |
| `begin_checkout` events present | ⬜ | |
| `purchase` events present | ⬜ | |
| `view_search_results` events present | ⬜ | Required for search analysis |

## 3. Identifier Completeness

| Check | Status | Notes |
|-------|--------|-------|
| `user_pseudo_id` null rate < 0.1% | ⬜ | |
| `ga_session_id` null rate acceptable | ⬜ | Some events may lack session ID |
| `session_key` constructed for majority of events | ⬜ | |

## 4. Session Validity

| Check | Status | Notes |
|-------|--------|-------|
| int_sessions row count > 0 | ⬜ | |
| session_key is unique in int_sessions | ⬜ | dbt test |
| Sessions without events excluded | ⬜ | Null session_key filtered |

## 5. Transaction Validity

| Check | Status | Notes |
|-------|--------|-------|
| int_orders row count > 0 | ⬜ | |
| order_transaction_key is unique | ⬜ | dbt test |
| Null transaction IDs excluded | ⬜ | By design |
| Duplicate purchase events deduplicated | ⬜ | row_number() |
| No negative revenue | ⬜ | dbt custom test |

## 6. Revenue Reconciliation

| Check | Status | Notes |
|-------|--------|-------|
| int_orders total ≈ source purchase total | ⬜ | Within 1% tolerance |
| Difference explained by deduplication | ⬜ | |

## 7. Known Caveats

- [ ] Some `ecommerce_purchase_revenue_in_usd` values may be NULL → defaulted to 0
- [ ] `traffic_source` represents first-touch only
- [ ] Obfuscated dataset may have reduced event coverage
- [ ] Date range is configurable — ensure it covers enough data for meaningful analysis
