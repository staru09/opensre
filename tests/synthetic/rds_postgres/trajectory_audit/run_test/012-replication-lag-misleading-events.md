# Trajectory audit — 012-replication-lag-misleading-events

- Captured: 2026-05-05T15:23:53+00:00
- Scenario difficulty: 3
- Failure mode: replication_lag
- Status: FAIL
- Failure reason: `wrong category: got 'infrastructure', expected 'resource_exhaustion'`

## Alert

- Title: [synthetic-rds] Replication Lag Critical on reporting-prod
- Severity: critical

## Trajectory

### Expected (from `answer.yml:optimal_trajectory`)

1. `query_grafana_logs`
2. `query_grafana_metrics`
3. `query_grafana_alert_rules`

### Actual (flattened across investigation loops)

1. `query_grafana_alert_rules` ✓
2. `query_grafana_logs` ✓
3. `query_grafana_metrics` ✓
4. `query_grafana_traces`
5. `get_sre_guidance`
6. `query_grafana_service_names`

### Per investigation loop

#### Loop 1

**Planning rationale:** Start by querying the Grafana alert rules to understand the exact alert query and thresholds for replication lag on the reporting-prod RDS instance. This will clarify what metric or log is triggering the critical alert. Then, query the Grafana logs for the rds-postgres-synthetic service and pipeline to look for error patterns, slow queries, or replication-related messages that explain the cause of replication lag. These two actions together can discriminate between root causes such as slow or blocking queries, background process delays, or configuration/connection issues affecting replication.

**Actions:** `query_grafana_alert_rules`, `query_grafana_logs`

#### Loop 2

**Planning rationale:** The critical replication lag alert on the reporting-prod RDS instance may be caused by slow or blocking queries, connection issues, or resource bottlenecks. Querying Grafana Cloud Mimir metrics for the rds-postgres-synthetic service will provide key insights into resource utilization patterns (CPU, connections), query latency, and replication lag trends. This can help distinguish between idle connections, query-induced pressure, or secondary symptoms, ruling out or confirming hypotheses on the root cause efficiently with a single action.

**Actions:** `query_grafana_metrics`

#### Loop 3

**Planning rationale:** The critical replication lag on reporting-prod can be caused by slow or blocking queries, background processes delaying WAL shipping, or resource contention. Querying Grafana Tempo traces for the rds-postgres-synthetic service allows investigation of the pipeline execution behavior to identify slow spans, timeouts, or dependencies causing lag. This trace data can help discriminate if the lag is due to pipeline inefficiencies, blocking queries, or external bottlenecks without redundant log or metric queries that are already exhausted.

**Actions:** `query_grafana_traces`

#### Loop 4

**Planning rationale:** The alert is for replication lag on the reporting-prod RDS Postgres instance, indicating potential database performance issues. Since querying Grafana logs, traces, metrics, and alert rules is blocked and those would have been ideal for direct diagnostics, retrieving SRE guidance focused on database resource issues, pipeline recovery, and remediation offers a high-level, expert-validated knowledge base. This can help validate root cause hypotheses such as replication bottlenecks caused by slow queries, overloaded resources, or configuration/traffic patterns, and improve remediation recommendations. This step efficiently rules out uncertainty about procedural next steps, next diagnostic focus, and common failure modes given limited direct telemetry access.

**Actions:** `get_sre_guidance`

#### Loop 5

**Planning rationale:** The critical replication lag alert on reporting-prod can be caused by a few root hypotheses: (1) blocking or slow-running expensive queries on the replica delaying apply, (2) an increase in idle or long-lived connections on the replica causing resource pressure, (3) background processes like vacuums or WAL delivery backlog, or (4) genuine spikes causing load beyond replica capacity. Since all Grafana queries for logs, metrics, traces, and alerts are blocked or exhausted, the next best step is to run query_grafana_service_names to confirm the exact service_name label associated with the rds-postgres-synthetic pipeline in Grafana Loki. This can enable more targeted troubleshooting if logs become accessible later and helps verify that logging is properly configured for this DB service. This single discriminating step avoids redundant querying of logs or metrics already exhausted and sets the stage for further targeted investigations elsewhere or later.

**Actions:** `query_grafana_service_names`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_alert_rules`: 0 entries
- `grafana_alert_rules_count`: ? entries
- `grafana_logs`: 18 entries
- `grafana_error_logs`: 3 entries
- `grafana_logs_query`: 0 entries
- `grafana_logs_service`: 22 entries
- `grafana_metrics`: 11 entries
- `grafana_metric_name`: 19 entries
- `grafana_metrics_service`: 22 entries
- `grafana_traces`: 0 entries
- `grafana_pipeline_spans`: 0 entries
- `grafana_traces_service`: 22 entries
- `grafana_service_names`: 0 entries

## Validated claims

- Failover initiated, failover in progress, failover completed, instance available [evidence: Grafana Error Logs]
- ReplicaLag sustained above 900s threshold for 8 consecutive minutes [evidence: Grafana Metrics]

## Non-validated claims

- The replication lag could be additionally influenced by write-heavy workloads. To confirm this, specific query performance insights on transaction logs generation would be needed.
- Connection spike as a result of blocked writers is a plausible inference given the observed increase in database connections, but confirmation would require detailed connection usage metrics during the incident.

## Diagnosis

- Predicted root cause: Based on the RDS event timeline (primary evidence source), the root cause of the replication lag was due to a Multi-AZ failover initiated by the RDS health check failure, which temporarily paused the replication process until the instance was available again.
- Predicted category:   `infrastructure`
- Expected category:    `resource_exhaustion`
- Matched keywords:     replication lag, replica
- Missing keywords:     WAL, ETL

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 6, after metrics were already queried at step 3. The agent queried metrics on instances it had not yet discovered.

### Reviewer notes

_(Add manual observations here.)_
