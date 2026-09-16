# Production Experiment Tracking Specification

This document defines the event instrumentation required to run the `mobile_checkout_simplification_v1` experiment in a real production environment.

## 1. Tracking Principles
- **Exposure Before Outcome:** An exposure event must be recorded *before* any outcome events (like purchase) can be attributed to the experiment.
- **Persistent Assignment:** A user must receive one and only one variant assignment, which must persist across sessions.
- **Telemetry Propagation:** The `experiment_id` and `variant` must be attached to downstream outcome and guardrail events to ensure accurate attribution.

## 2. Event: Experiment Exposure
This event fires when the user is randomized and exposed to the experiment.

```text
event_name: experiment_impression

Required Fields:
- experiment_id: "mobile_checkout_simplification_v1"
- variant_id: "control" | "treatment"
- user_pseudo_id: <uuid>
- event_timestamp: <timestamp>
- assignment_timestamp: <timestamp>
- eligibility_reason: "mobile_begin_checkout"
- device_category: "mobile"
```
*Validation:* Must fire exactly once per eligible user.

## 3. Event: Purchase (Primary Outcome)
This event fires on the order confirmation page.

```text
event_name: purchase

Required Fields:
- experiment_id: "mobile_checkout_simplification_v1"
- variant: "control" | "treatment"
- user_pseudo_id: <uuid>
- transaction_id: <string>
- revenue_usd: <float>
- event_timestamp: <timestamp>
```

## 4. Guardrail Events

### Payment Error
Fires when the payment gateway returns an error or a form validation fails on the payment step.
```text
event_name: payment_error

Required Fields:
- experiment_id: "mobile_checkout_simplification_v1"
- variant: "control" | "treatment"
- user_pseudo_id: <uuid>
- error_type: <string>
- event_timestamp: <timestamp>
```

### Refund or Cancelled
Fires via a backend webhook or administrative action when an order is voided.
```text
event_name: refund_or_cancelled

Required Fields:
- experiment_id: "mobile_checkout_simplification_v1"
- variant: "control" | "treatment"
- user_pseudo_id: <uuid>
- transaction_id: <string>
- event_timestamp: <timestamp>
```

### Checkout Completed Duration
Calculated event representing the time between `begin_checkout` and `purchase`.
```text
event_name: checkout_completed

Required Fields:
- experiment_id: "mobile_checkout_simplification_v1"
- variant: "control" | "treatment"
- user_pseudo_id: <uuid>
- checkout_duration_seconds: <float>
- event_timestamp: <timestamp>
```

## 5. QA & Validation
Before launching to production, analysts and QA engineers must verify:
1. **Sample Ratio Mismatch (SRM):** Ensure exposure events hit a 50/50 split on a 1% ramp.
2. **Missing Exposures:** Ensure no users have a `purchase` event with the `experiment_id` but lack an upstream `experiment_exposure` event.
3. **Treatment Contamination:** Ensure no `user_pseudo_id` logs both a "control" and "treatment" exposure event.
