# Trajectory audit — 014-checkpoint-storm-cpu-saturation

- Captured: 2026-05-05T15:26:00+00:00
- Scenario difficulty: 4
- Failure mode: cpu_saturation
- Status: PASS

## Alert

- Title: [synthetic-rds] High CPU on billing-prod
- Severity: critical

## Trajectory

### Expected (from `answer.yml:optimal_trajectory`)

1. `query_grafana_metrics`
2. `query_grafana_logs`
3. `query_grafana_alert_rules`

### Actual (flattened across investigation loops)

1. `query_grafana_logs` ✓
2. `query_grafana_metrics` ✓
3. `query_grafana_traces`
4. `query_grafana_alert_rules` ✓
5. `query_grafana_service_names`
6. `get_sre_guidance`

### Per investigation loop

#### Loop 1

**Planning rationale:** To investigate the critical high CPU alert on the billing-prod RDS instance, it is essential to determine the cause of CPU pressure. The leading hypotheses include slow/expensive queries, idle or long-lived connections causing resource contention, or traffic spikes. "query_grafana_logs" will help identify if there are any query slowdowns, errors, or long-running queries in the rds-postgres-synthetic pipeline logs tied to billing-prod. "query_grafana_metrics" will provide CPU utilization trends and may show concurrent connections or query-related metrics to correlate with CPU spikes. This pair of actions will clarify whether the CPU issue stems from workload patterns, query inefficiencies, or connection-related bottlenecks, enabling a focused root cause determination.

**Actions:** `query_grafana_logs`, `query_grafana_metrics`

#### Loop 2

**Planning rationale:** The high CPU on billing-prod could be caused by expensive or slow queries, blocking queries, or inefficient pipelines causing sustained load. Since query_grafana_logs and query_grafana_metrics are blocked, querying Grafana Tempo traces for the rds-postgres-synthetic service can reveal details about query execution patterns, slow spans, or timeouts that directly contribute to CPU spikes. This action will help discriminate between slow or expensive queries versus genuine traffic spikes or secondary symptoms. It also indirectly helps identify if there are any pipeline delays or retries causing load. This single action provides high information gain on the root cause without redundant data collection.

**Actions:** `query_grafana_traces`

#### Loop 3

**Planning rationale:** The incident is high CPU on the billing-prod RDS instance. Competing hypotheses include expensive/slow queries causing CPU load, idle or many connections, or background processes causing CPU spikes. Since direct logs, metrics, and traces are blocked, querying the Grafana alert rules for the pipeline 'rds-postgres-synthetic' will help understand which specific queries, metrics, or thresholds triggered this alert. This can discriminate if the alert is based on query performance (indicating slow/expensive queries) versus connection count or other metrics, and clarify the alert configuration which supports deeper diagnosis. This focused action can rule out or confirm the mechanism causing CPU load without redundant or exhausted steps.

**Actions:** `query_grafana_alert_rules`

#### Loop 4

**Planning rationale:** Fallback plan: LLM returned invalid structured output.

**Actions:** `query_grafana_service_names`, `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_logs`: 21 entries
- `grafana_error_logs`: 0 entries
- `grafana_logs_query`: 0 entries
- `grafana_logs_service`: 22 entries
- `grafana_metrics`: 14 entries
- `grafana_metric_name`: 19 entries
- `grafana_metrics_service`: 22 entries
- `grafana_traces`: 0 entries
- `grafana_pipeline_spans`: 0 entries
- `grafana_traces_service`: 22 entries
- `grafana_alert_rules`: 0 entries
- `grafana_alert_rules_count`: ? entries
- `grafana_service_names`: 0 entries

## Validated claims

- High CPU utilization coincided with high WriteIOPS, consistent with checkpoint-driven I/O storm. [evidence: grafana_metrics]
- Wait events are dominated by LWLock:BufferMapping and IO:WALWrite, typical of checkpointing workloads. [evidence: grafana_logs]
- The exact role of autovacuum operation and its direct impact on Checkpoint Storm requires confirmation, e.g., specific workload analysis.
- Whether other queries contributed to the condition, such as scan-heavy load, requires detailed Performance Insights analysis.

## Diagnosis

- Predicted root cause: Most likely: Resource exhaustion due to a checkpoint storm from VACUUM FREEZE operations causing high CPU usage. Evidence specific to CPU saturation directly being caused by long-running queries or missing index is lacking.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     vacuum, checkpoint, LWLock, WAL

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 5, after metrics were already queried at step 2. The agent queried metrics on instances it had not yet discovered.
- The agent reached the correct diagnosis category but recorded no causal chain steps. The conclusion appears to be based on pattern-matching rather than traced reasoning.

### Reviewer notes

_(Add manual observations here.)_
