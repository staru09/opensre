# Golden trajectory — 001-replication-lag

> **Difficulty:** L1 — single-fault, no confounders
> **Root cause category:** `resource_exhaustion`
> **Required evidence:** `aws_cloudwatch_metrics`, `aws_performance_insights` (both served via `query_grafana_metrics` in this fixture)

## Phases

### Phase 1 — Quantify the lag (must come first)
1. `query_grafana_metrics`

**Why first:** The symptom *is* a metric — `ReplicaLag > 900s` on `payments-prod-replica-1`. The same call surfaces `WriteIOPS`, `TransactionLogsGeneration`, and the Performance Insights snapshot showing bulk `UPDATE` statements with `WAL:Lock` waits. All four pieces of `VALIDATED_CLAIMS` come from this one tool. You cannot diagnose replication lag without first observing the lag, the write rate that produced it, and the wait events that confirm WAL replay as the bottleneck.

### Phase 2 — Contextualize and confirm (any order, both required)
- `query_grafana_logs` (parallel)
- `query_grafana_alert_rules` (parallel)

**Why parallel:** Neither carries primary evidence for replication lag. Logs add timeline context (when the write burst started) and rule out a parallel infrastructure event. Alert rules confirm the threshold that fired and that no other replication-related rules are silenced. Either order works because neither blocks reasoning that the other one provides.

## Forbidden orderings

- **Logs or alert_rules before metrics.** The model response is grounded entirely in metric evidence. If the agent reads logs first, it has no quantitative anchor and is liable to anchor on whatever event happens to be in the log window — which is exactly the failure pattern we observed in `006-replication-lag-cpu-redherring` (agent diagnosed via CPU because metrics happened to show a CPU spike alongside).

## Allowed alternative paths

- If `query_grafana_metrics` returns no replication metrics, the agent may fall back to `query_grafana_logs` first to look for replication-related events in the RDS event stream. In this fixture the metrics are always present, so this branch should not trigger for scenario 001.

## Authoring rationale

- **Why three tools and not more:** `aws_cloudwatch_metrics` + `aws_performance_insights` covers `required_evidence_sources` entirely. The other three available tools (`traces`, `service_names`, `sre_guidance`) add no information for an L1 replication lag — using them is the universal 2× overspend pattern documented in `trajectory_audit/test_run_002/SUMMARY.md`.
- **Why metrics carries PI evidence:** `_EVIDENCE_KEY_MAP` in `run_suite.py` routes `aws_performance_insights` to `grafana_metrics`. A reviewer reading this trajectory should not expect a separate PI tool call; it does not exist in `--mock-grafana` mode.
- **Counterfactual check:** Removing `query_grafana_metrics` makes the scenario unsolvable. Removing either Phase 2 tool still allows the diagnosis (the scenario can be solved on metrics alone) — they are kept in the trajectory because they confirm the absence of competing root causes, not because they carry primary evidence.

## Cross-check vs `test_run_002` actual

The agent in `test_run_002` called `metrics → logs → alert_rules → traces → guidance → service_names`. The first three match this golden trajectory exactly. The last three are redundant. Under the new ordered scorer this scenario would receive `ordering_ok=True` but `efficiency<1.0` (3 extra calls).
