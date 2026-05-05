# Trajectory audit — 001-replication-lag

- Captured: 2026-05-05T15:10:49+00:00
- Scenario difficulty: 1
- Failure mode: replication_lag
- Status: PASS

## Alert

- Title: [synthetic-rds] Replication Lag On payments-prod
- Severity: critical

## Trajectory

### Expected (from `answer.yml:optimal_trajectory`)

1. `query_grafana_metrics`
2. `query_grafana_logs`
3. `query_grafana_alert_rules`

### Actual (flattened across investigation loops)

1. `query_grafana_logs` ✓
2. `query_grafana_alert_rules` ✓
3. `query_grafana_metrics` ✓
4. `query_grafana_traces`
5. `get_sre_guidance`
6. `query_grafana_service_names`

### Per investigation loop

#### Loop 1

**Planning rationale:** The critical alert is about replication lag on the 'payments-prod' RDS Postgres instance. Leading hypotheses include: (1) slow or blocking queries on the replica causing lag, (2) resource bottlenecks like CPU, IO, or connections, and (3) issues in background processes such as WAL shipping or vacuum. Querying Grafana Loki logs for the 'rds-postgres-synthetic' service will help detect slow queries, blocking queries, errors related to replication, or other anomalies in the database logs correlated with the alert time. Logs provide high information gain in discriminating between query/resource causes versus replication infrastructure issues and can highlight direct errors or warnings linked to the replication lag.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** The key hypotheses for replication lag on payments-prod are: (1) queuing or backlog in the replication system caused by sudden traffic spikes or query latency; (2) resource exhaustion or contention on the database instance or replica, causing slow processing; (3) long-running or blocking queries affecting replication application; (4) misconfiguration or thresholds in alerting rules giving false positives. Querying the Grafana alert rules will clarify exactly what metrics and thresholds triggered the alert, confirming the alert's sensitivity and monitored dimensions. Querying Grafana metrics for relevant RDS and replication lag metrics over time will show whether there are traffic spikes, resource saturation patterns, or correlating query latencies and throughput drops that cause the lag. This approach most efficiently separates root causes related to genuine replication processing delays vs. alert anomalies and resource bottlenecks, without redundant exploration of logs which is blocked.

**Actions:** `query_grafana_alert_rules`, `query_grafana_metrics`

#### Loop 3

**Planning rationale:** We have a critical replication lag alert on the payments-prod RDS Postgres instance. Plausible root causes include blocking/slow queries on the replica, resource contention on the replica (CPU or IO), or pipeline-induced load causing delays. Since log and metric queries are blocked, tracing the pipeline service rds-postgres-synthetic with Grafana Tempo traces targeting the replication lag period can reveal slow queries, blocking patterns, or pipeline traffic anomalies that directly cause or correlate with the lag. This action can discriminate between slow queries causing lag versus downstream pipeline or traffic issues creating backpressure or resource contention. It is the highest information gain single step to differentiate query-level root causes from pipeline or downstream influences.

**Actions:** `query_grafana_traces`

#### Loop 4

**Planning rationale:** The critical replication lag on the payments-prod RDS Postgres instance could stem from various root causes such as resource contention (CPU, IO), long-running or blocking queries, or issues with replication setup/configuration. Since direct logs, metrics, and alert rules querying are blocked, the best next step is to retrieve SRE best practices specifically for data pipeline incidents involving replication lag and delays. This can shed light on common causes, remediation steps, and diagnostics that guide the next investigation direction. It helps rule out hypotheses around pipeline correctness, resource hotspots, or delayed processing patterns and focuses on the replication lag mechanism itself.

**Actions:** `get_sre_guidance`

#### Loop 5

**Planning rationale:** Controller fallback: planner selected only unavailable or already-executed actions. Forcing next available action.

**Actions:** `query_grafana_service_names`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_logs`: 11 entries
- `grafana_error_logs`: 0 entries
- `grafana_logs_query`: 0 entries
- `grafana_logs_service`: 22 entries
- `grafana_alert_rules`: 0 entries
- `grafana_alert_rules_count`: ? entries
- `grafana_metrics`: 20 entries
- `grafana_metric_name`: 19 entries
- `grafana_metrics_service`: 22 entries
- `grafana_traces`: 0 entries
- `grafana_pipeline_spans`: 0 entries
- `grafana_traces_service`: 22 entries
- `grafana_service_names`: 0 entries

## Validated claims

- The read replica exceeded 600 seconds of replication lag. [evidence: Grafana Logs]
- High IO:WALWrite waits and transaction logs generation are observed on the primary database. [evidence: Grafana Logs, Grafana Metrics]

## Non-validated claims

- The specific write-heavy workload causing the excessive WAL generation might be the "UPDATE orders SET status" query, but additional query performance insights or logs would confirm this.
- The role of the "INSERT INTO audit_log" query in contributing to the WAL generation is possible but not verified; further query analysis would clarify its impact.

## Diagnosis

- Predicted root cause: The root cause is most likely a write-heavy workload on the primary database causing excessive WAL generation, which the read replica could not keep up with, resulting in replication lag. However, the specific workload driving this is not identified in the evidence.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     replication lag, write-heavy workload, replica, wal

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 6, after metrics were already queried at step 3. The agent queried metrics on instances it had not yet discovered.
- The agent reached the correct diagnosis category but recorded no causal chain steps. The conclusion appears to be based on pattern-matching rather than traced reasoning.

### Reviewer notes

_(Add manual observations here.)_
