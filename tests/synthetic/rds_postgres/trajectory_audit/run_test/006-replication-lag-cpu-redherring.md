# Trajectory audit — 006-replication-lag-cpu-redherring

- Captured: 2026-05-05T15:17:10+00:00
- Scenario difficulty: 2
- Failure mode: replication_lag
- Status: FAIL
- Failure reason: `missing required keywords: ['causally independent']`

## Alert

- Title: [synthetic-rds] Replication Lag And High CPU On analytics-prod
- Severity: critical

## Trajectory

### Expected (from `answer.yml:optimal_trajectory`)

1. `query_grafana_metrics`
2. `query_grafana_logs`
3. `query_grafana_alert_rules`

### Actual (flattened across investigation loops)

1. `query_grafana_logs` ✓
2. `query_grafana_metrics` ✓
3. `query_grafana_alert_rules` ✓
4. `query_grafana_traces`
5. `query_grafana_service_names`
6. `get_sre_guidance`

### Per investigation loop

#### Loop 1

**Planning rationale:** To diagnose replication lag and high CPU on the RDS instance, the top hypotheses are: (1) slow or expensive queries causing CPU and lag, (2) high idle or long-lived connections creating resource contention, or (3) background processes like vacuum or replication overhead causing CPU spikes. Querying pipeline logs from Grafana Loki with the service name 'rds-postgres-synthetic' and the pipeline 'rds-postgres-synthetic' will help identify slow queries, errors, or patterns of connection behavior. This will discriminate between slow query load versus connection issues or background overhead, enabling focused next steps. Other actions like alert rules or metrics are less direct and less discriminating at this moment.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** The alert indicates replication lag and high CPU on the RDS instance 'analytics-prod'. The key hypotheses are: (1) replication lag caused by slow or blocking queries (e.g. expensive analytics queries or vacuum), (2) idle or excessive connections causing CPU pressure, or (3) genuine traffic spikes driving CPU usage and replication delay. Querying Grafana metrics for CPU, query latency, connection counts, and replication lag over recent time — specifically for the 'rds-postgres-synthetic' service and analytics-prod instance — will help clarify if high CPU correlates with query latency or connections, and whether replication lag stems from workload or other background tasks. This single action can discriminate between slow queries, connection issues, and background process overload, thereby guiding the next diagnostic step effectively.

**Actions:** `query_grafana_metrics`

#### Loop 3

**Planning rationale:** To investigate the critical alert for replication lag and high CPU on analytics-prod RDS, plausible root causes include: (1) slow or expensive queries causing CPU spikes and lag; (2) excessive or idle connection counts contributing to resource contention; (3) background maintenance or replication/wal issues; and (4) genuine traffic spikes. Since logs and metrics querying is blocked, inspecting the configured Grafana alert rules will reveal what specific metrics and thresholds are monitored, potentially highlighting the exact queries or resource metrics triggering the alert. This can help discriminate between slow queries, connection issues, or other causes by understanding the alert conditions and monitored signals, thus advancing diagnosis with minimal overhead.

**Actions:** `query_grafana_alert_rules`

#### Loop 4

**Planning rationale:** The incident involves high CPU and replication lag on the analytics-prod PostgreSQL RDS instance. Key hypotheses include heavy and slow queries causing CPU pressure and lag, idle or blocking connections contributing to resource exhaustion, or background database processes (like vacuum or replication tasks) being stalled or overwhelmed. Since logs and metrics are not available, querying Grafana Tempo traces is the best next step to identify specific slow or expensive query spans, verify if distributed pipeline requests are timing out or retried excessively, and correlate trace data with resource usage. This can directly distinguish between expensive query loads, blocking issues, or genuine spikes in pipeline traffic driving resource consumption, helping to clarify the mechanism behind the replication lag and high CPU.

**Actions:** `query_grafana_traces`

#### Loop 5

**Planning rationale:** Primary hypotheses include: (1) replication lag caused by CPU saturation on analytics-prod overloaded by slow or expensive queries; (2) an abnormal increase in idle or long-lived connections contributing to resource exhaustion; (3) background processes such as WAL or vacuum causing CPU spikes and lag; (4) possible genuine traffic spikes causing resource contention. Since logs, metrics, alert rules, and traces are blocked or exhausted, querying available Grafana service names may clarify relevant logging sources if we missed the correct service and thus identify slow queries or connection patterns. Retrieving SRE guidance on resource planning and pipeline monitoring can inform effective diagnostic focus on top hypotheses about query inefficiency, connection issues, or background tasks. This minimal set can help disambiguate whether analytics-prod latency is due to query load, idle connections, or maintenance activity as main root cause.

**Actions:** `query_grafana_service_names`, `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_logs`: 7 entries
- `grafana_error_logs`: 0 entries
- `grafana_logs_query`: 0 entries
- `grafana_logs_service`: 22 entries
- `grafana_metrics`: 20 entries
- `grafana_metric_name`: 19 entries
- `grafana_metrics_service`: 22 entries
- `grafana_alert_rules`: 0 entries
- `grafana_alert_rules_count`: ? entries
- `grafana_traces`: 0 entries
- `grafana_pipeline_spans`: 0 entries
- `grafana_traces_service`: 22 entries
- `grafana_service_names`: 0 entries

## Validated claims

- The write-heavy workload led to increased `transaction_logs_generation`, peaking at 104,857,600 bytes. [evidence: Grafana Metrics]
- Replication lag exceeded 900 seconds due to delayed WAL processing on the replica. [evidence: Grafana Logs]

## Non-validated claims

- CPU utilization spike on the primary might be influenced by contention from the update-heavy `event_stream` query. This could be further validated by inspecting detailed query execution plans and contention logs.

## Diagnosis

- Predicted root cause: Replication lag was caused by a write-heavy workload on the primary database, leading to a backlog in WAL processing. This is supported by high `transaction_logs_generation` and significant wait events related to WAL locks.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     replication, replication lag, WAL, replica, UPDATE, SELECT
- Missing keywords:     causally independent

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 5, after metrics were already queried at step 2. The agent queried metrics on instances it had not yet discovered.

### Reviewer notes

_(Add manual observations here.)_
