# Golden trajectory — 005-failover

> **Difficulty:** L1 — but the only L1 scenario where logs come first
> **Root cause category:** `infrastructure`
> **Required evidence:** `aws_rds_events` (served via `query_grafana_logs`)

## Phases

### Phase 1 — Read the RDS event sequence (must come first)
1. `query_grafana_logs`

**Why first — this scenario inverts the L1 default:** unlike 001-004 where the symptom is a metric, the symptom *and* the diagnosis here are an RDS event sequence:

```
failover initiated      08:04:18Z
failover in progress    08:04:21Z
failover completed      08:04:58Z
instance available      08:05:04Z
```

These four events answer "what happened" completely. Calling metrics first means staring at `DatabaseConnections` dropping to zero and `CPUUtilization` collapsing — patterns consistent with several different incidents (instance crash, network partition, network ACL change, this failover) — and forming a hypothesis that you then have to undo when you read the events. The agent in `test_run_002` correctly read logs first; that should be encoded as required, not accidental.

The scenario's `required_keywords` list explicitly contains `primary evidence source` — a phrase used in the model response as `"Based on the RDS event timeline (primary evidence source)..."` That is the answer key telling you which tool to read first.

### Phase 2 — Confirm impact and recovery (must come after Phase 1)
2. `query_grafana_metrics`

**Why second and required:** Once the event sequence is known, metrics are used to *confirm* the failover narrative:
- `DatabaseConnections` to 0 at 08:05Z → recovered by 08:07Z (matches the event timestamps)
- `CPUUtilization` and `WriteIOPS` both at near-zero during the same window (proves the instance was unavailable, not just slow)
- PI showing no anomalous queries before or after (rules out a query-driven cause coincident with the failover)

The required keyword `workload resumed normally` is grounded in the post-failover metrics — not in the events themselves. Skipping Phase 2 leaves that claim unsupported.

This phase is sequential, not parallel with logs, because the metric reading is *interpreted* against the event timestamps. Reading metrics without the timeline of events makes the same numbers look like an outage of unknown cause.

### Phase 3 — Confirm threshold (single-element parallel block)
- `query_grafana_alert_rules` (parallel)

**Why last:** Confirms which alert rule fired. By Phase 3 the diagnosis is already complete; this closes out the model response. Allowed in any order with itself.

## Forbidden orderings

- **Metrics before logs.** This is the canonical mistake for this scenario. The agent reads connections-to-zero and CPU-to-zero, anchors on "outage" or "connection exhaustion", and then has to undo when it sees the failover events. The scenario's `forbidden_categories` is not set, but the required keyword `primary evidence source` is the design hint that logs is supposed to be primary.
- **Skipping logs.** `aws_rds_events` is in `required_evidence_sources`. A diagnosis from metrics alone would call this `infrastructure outage` and fail to ground the failover sequence.

## Allowed alternative paths

- If `query_grafana_logs` returns no RDS events for the investigation window, the agent should fall back to `query_grafana_metrics` to look for a connection cliff and then re-attempt logs with a wider window. In this fixture the events are always present, so this branch should not trigger for scenario 005.

## Authoring rationale

- **Why this scenario is the order-mattering case in the L1 batch:** 001-004 all have a metric as the symptom and metrics tools as the natural first step. 005 is the only L1 scenario where the *kind* of evidence (event vs. measurement) flips. The current placeholder `optimal_trajectory` happens to list `query_grafana_logs` first for this scenario only — that detail is correct, but it's the only correct ordering hint in any of the 15 placeholder lists.
- **Why three serial phases instead of metrics + parallel:** the logs → metrics dependency is real (Phase 2 interprets timestamps from Phase 1). Treating them as a parallel pair would let an agent diagnose on metrics alone and still pass `ordering_ok` — wrong outcome.
- **Counterfactual:** Removing Phase 1 makes `aws_rds_events` evidence missing — strict failure, plus the diagnosis has no narrative anchor. Removing Phase 2 leaves the recovery claims unsupported. Removing Phase 3 still produces a correct diagnosis.

## Cross-check vs `test_run_002` actual

`test_run_002/005-failover.md` shows `logs → metrics → alert_rules → traces → guidance → service_names`. First three match this golden trajectory exactly. The agent passed strictly and would pass under the new ordered scorer. **This is the scenario where the agent's natural ordering already matches the golden** — useful as a baseline that the prompt is doing something right when the alert is event-shaped.
