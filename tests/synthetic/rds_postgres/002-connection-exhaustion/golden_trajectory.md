# Golden trajectory — 002-connection-exhaustion

> **Difficulty:** L1 — single-fault, with a CPU-shaped symptom that must be ruled out
> **Root cause category:** `resource_exhaustion`
> **Forbidden categories:** `cpu_saturation`
> **Required evidence:** `aws_cloudwatch_metrics`, `aws_performance_insights` (both served via `query_grafana_metrics`)

## Phases

### Phase 1 — Quantify the saturation and rule out CPU (must come first)
1. `query_grafana_metrics`

**Why first:** Two metrics decide this scenario, and both come from the same tool call:
- `DatabaseConnections ≈ 490 / 500` — the actual root cause
- Performance Insights showing `Client:ClientRead` as the dominant wait event — the discriminator that proves the 35–50% CPU is *secondary* to idle session accumulation, not an independent CPU saturation event

If the agent does not see the PI wait events alongside the connection count, it will misattribute the cause to CPU (this is what happens to L2 confounder scenarios when the discriminator step is skipped). The phase is single-tool because both pieces are inside one Grafana metrics response.

### Phase 2 — Contextualize and confirm (any order, both required)
- `query_grafana_logs` (parallel)
- `query_grafana_alert_rules` (parallel)

**Why parallel:** Logs provide application-side context for *why* sessions accumulated (pool leak signatures). Alert rules confirm the `max_connections` threshold rule that fired. Neither is required to reach the diagnosis but both are required to write a complete model response. Either order works.

## Forbidden orderings

- **Diagnosing on metrics alone without PI wait events.** The PI snapshot is what distinguishes "connection exhaustion with CPU as a symptom" from "CPU saturation with connections as a symptom". An agent that sees CPU at 35–50% and connections near max could reasonably conclude either category — only `Client:ClientRead` waits in PI prove the directionality. Since PI is multiplexed into the metrics tool, this is automatic *if* the agent reads the full response, but the trajectory must include the metrics call to make this evidence available.
- **Logs before metrics.** Same reasoning as 001 — the symptom is a metric.

## Allowed alternative paths

- None. The scenario is small enough that the canonical three-tool sequence is the only sensible path.

## Authoring rationale

- **Forbidden category is the design hint.** `forbidden_categories: [cpu_saturation]` in `answer.yml` tells you the scenario is *deliberately* CPU-shaped to test discrimination. The trajectory must therefore include a step that surfaces evidence ruling out CPU as the cause — which is the PI snapshot inside Phase 1.
- **No `aws_rds_events` requirement:** the `required_evidence_sources` field doesn't list events for this scenario, so logs is supportive rather than required. We keep it in Phase 2 (parallel) because the model response cites idle session signatures, but a slimmer trajectory that drops it would still be defensible.
- **Counterfactual:** Removing Phase 1 makes the scenario unsolvable. Removing either Phase 2 tool still allows correct diagnosis.

## Cross-check vs `test_run_002` actual

`test_run_002/002-connection-exhaustion.md` shows `metrics → logs → alert_rules → traces → guidance → service_names`. The strict scorer marked this `FAIL` (missing keyword `client sessions`) but the trajectory itself is correct on the first three calls. Under the new ordered scorer this would be `ordering_ok=True` with `efficiency<1.0` from the 3 redundant calls.
