# Golden trajectory — 004-cpu-saturation-bad-query

> **Difficulty:** L1 — single-fault, but PI is the only way to identify the offending query
> **Root cause category:** `resource_exhaustion`
> **Forbidden categories:** `connection_exhaustion`
> **Required evidence:** `aws_performance_insights` (served via `query_grafana_metrics`)

## Phases

### Phase 1 — Confirm CPU saturation and identify the query (must come first)
1. `query_grafana_metrics`

**Why first:** Three things that decide this scenario all live in one metrics response:
- `CPUUtilization` sustained at 88–97% — the symptom
- `ReadIOPS` peaking at 18,100 — confirms full table scans (rules out a CPU loop with no I/O)
- `DatabaseConnections` stable at ~160 — rules out the forbidden `connection_exhaustion` category
- Performance Insights snapshot showing `SELECT * FROM orders WHERE status = $1` at 7.2 AAS with `CPU:user` as dominant wait — the discriminator that names the offending query

Without PI evidence in this phase the agent has CPU at 90%+ but no idea *what* is consuming it. This is the discriminator step for L1 CPU scenarios: you cannot distinguish "bad query" from "infrastructure CPU pressure" from "vacuum storm" (the trap in 014) without the wait-event breakdown.

### Phase 2 — Rule out infrastructure events and confirm threshold (any order, both required)
- `query_grafana_logs` (parallel)
- `query_grafana_alert_rules` (parallel)

**Why parallel:** The model response cites `[evidence: aws_rds_events]` for the line *"No RDS infrastructure events occurred during the window"* — i.e., logs is used to *negate* an alternative cause, not to *establish* the diagnosis. Same for alert rules. Either order is fine because neither result depends on the other.

## Forbidden orderings

- **Diagnosing on `CPUUtilization` alone without PI.** This is the critical failure mode. CPU at 90% can come from a bad query (this scenario), an autovacuum storm (014), idle session lightweight queries (002), or a kernel I/O wait pattern. Only PI wait events distinguish them. A trajectory that gets to a category answer before reading PI evidence has not done the discrimination the scenario tests.
- **Logs before metrics.** Same reasoning as 001/002 — the symptom is a metric, not an event.

## Allowed alternative paths

- None. The scenario's discriminator question is "what kind of CPU saturation?" and the only tool that answers it is `query_grafana_metrics` (with PI multiplexed in). Every defensible trajectory for 004 starts with that call.

## Authoring rationale

- **Why `aws_performance_insights` is the *only* required evidence source:** the scenario explicitly tests whether the agent reads PI to name the query. CloudWatch metrics give the symptom; PI gives the cause. Reading the `required_evidence_sources` field as a design hint, the author wants discrimination, not just symptom recognition.
- **Why logs and alert_rules are kept despite not being required evidence:** they support the negation claims in the model response (no infra events, threshold rule fired). A trajectory without them produces a thinner answer that risks hitting `forbidden_categories` checks if the agent gets confused about whether connections were involved.
- **Counterfactual:** Removing Phase 1 makes the scenario unsolvable. Removing Phase 2 still allows the diagnosis but leaves the negation claims unsupported.

## Cross-check vs `test_run_002` actual

`test_run_002/004-cpu-saturation-bad-query.md` shows `metrics → logs → alert_rules → traces → guidance → service_names`. The first three match this golden trajectory exactly. The agent passed strictly and would pass under the new ordered scorer; the last three calls are redundant.
