# Product Case Study

## Business Context

An ecommerce business (the Google Merchandise Store) generates revenue by selling
branded hardware, apparel, and accessories through its web store. Leadership needs
evidence-based answers to prioritize product and engineering investments.

> **Data Source:** Google's public, obfuscated GA4 Google Merchandise Store sample
> ecommerce dataset. This is an independent analysis — not affiliated with Google's
> merchandise operations.

---

## Product Lifecycle Framework

```
Acquisition → Activation → Engagement → Monetization → Retention
```

### Ecommerce Journey Mapping

| Lifecycle Stage | Ecommerce Event | GA4 Event Name |
|----------------|-----------------|----------------|
| Acquisition | Session start / first visit | `session_start`, `first_visit` |
| Activation | Product view | `view_item` |
| Engagement | Add to cart / begin checkout | `add_to_cart`, `begin_checkout` |
| Monetization | Purchase | `purchase` |
| Retention | Repeat visit / repeat purchase | Cohort return activity |

---

## Analytical Questions

### 1. Funnel Friction
**Question:** Where do users drop off in the purchase journey?

**Approach:**
- Build a strict sequential funnel (view → cart → checkout → purchase)
- Identify the step with the largest absolute drop-off
- Segment by device to identify platform-specific friction

**Evidence standard:** Describe observed rates; do not claim causation.

### 2. User Segments
**Question:** What segments create the most value?

**Approach:**
- Compare conversion and revenue across device categories
- Analyze acquisition medium effectiveness
- Investigate search adoption association with conversion

**Evidence standard:** Present descriptive comparisons; flag selection bias.

### 3. Retention
**Question:** Are users returning after first activity?

**Approach:**
- Build weekly activity cohorts based on first session date
- Track retention rate over subsequent weeks
- Compare early vs. later cohorts

**Evidence standard:** Label as observed activity retention within data window.

### 4. Monetization
**Question:** Which products, devices, and channels drive revenue?

**Approach:**
- RFM segmentation of purchasers
- Top products by revenue
- Revenue per session by segment

**Evidence standard:** Based on purchase events with valid transaction IDs only.

### 5. Product Decisions
**Question:** What should the team build or test next?

**Approach:**
- Synthesize findings into prioritized opportunities
- Design rigorous experiments for top hypotheses
- Define success metrics and guardrails

**Evidence standard:** Recommendations are proposals requiring experimental validation.

---

## How to Interpret Results

1. **Run the analysis first** — All findings depend on query execution
2. **Check data quality** — Review `data_quality_report_generated.md` before drawing conclusions
3. **Read limitations** — Every finding has caveats documented in `limitations.md`
4. **Distinguish association from causation** — Observational data cannot establish cause
5. **Consider the time window** — Metrics are bounded by the configured date range

---

## Turning Findings into Decisions

```
Observation (data) → Hypothesis (theory) → Experiment (test) → Decision (action)
```

1. **Identify the largest opportunity** from funnel, segment, or retention analysis
2. **Form a testable hypothesis** using the "If..., then..., because..." format
3. **Design a rigorous experiment** with proper randomization and power analysis
4. **Define decision criteria** before running the experiment
5. **Execute, analyze, and decide** based on pre-registered criteria

See [experiment_design.md](experiment_design.md) for the full experiment template.

---

## What This Case Study Demonstrates

| Competency | Evidence |
|-----------|----------|
| Product thinking | Business questions → analytical framework |
| Data modeling | dbt staging/intermediate/marts on nested schema |
| Statistical rigor | Proper experiment design, causal disclaimers |
| Engineering quality | Tested, documented, version-controlled |
| Communication | Stakeholder-ready dashboards and memos |
