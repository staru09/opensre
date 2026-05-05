# Trajectory audit — 004-cpu-saturation-bad-query

- Captured: 2026-05-05T15:14:48+00:00
- Scenario difficulty: 1
- Failure mode: cpu_saturation
- Status: PASS

## Alert

- Title: [synthetic-rds] CPU Saturation On catalog-prod
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

**Planning rationale:** To diagnose the CPU saturation on the RDS instance catalog-prod, the most critical distinction is whether the CPU pressure is caused by slow or expensive queries, background processes (such as vacuuming), or connection-related issues (idle or long-lived connections). Querying Grafana Loki logs for the rds-postgres-synthetic service and pipeline rds-postgres-synthetic can reveal SQL query errors, slow queries, or related RDS events. This action can also hint if audit logs or background processes are contributing to CPU spikes. Other actions like querying alert rules or metrics add less discrimination at this stage compared to examining logs that contain direct evidence of problematic SQL or database events.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** The alert is CPU saturation on the RDS instance catalog-prod. Plausible root causes include: (1) slow or expensive queries causing CPU spikes, (2) idle or excessive connections causing resource pressure, (3) a genuine traffic spike, or (4) background processes like vacuum or logging overhead. Querying Grafana metrics for this service and instance will help distinguish if the CPU spikes correlate with query latency, connection count spikes, or other pipeline throughput changes, thereby ruling out or confirming expensive query or traffic spike causes. This gives high information gain for narrowing down the CPU pressure mechanism without redundant background context or unavailable logs.

**Actions:** `query_grafana_metrics`

#### Loop 3

**Planning rationale:** To diagnose the cause of CPU saturation on the RDS instance catalog-prod, we need to understand the alerting configuration, including the specific metrics and thresholds monitored. This helps clarify if the CPU spike is due to query load, connection issues, or background processes. Since query_grafana_logs and metrics are blocked, inspecting the alert rules can give clues on what performance aspects are monitored and guide further investigation with available tools.

**Actions:** `query_grafana_alert_rules`

#### Loop 4

**Planning rationale:** The CPU saturation on the RDS instance catalog-prod may stem from high-impact slow or expensive queries, connection management issues including idle or long-lived connections, or analyzing downstream pipeline impacts that correlate with database pressure. Since logs and alert rules are exhausted, querying Grafana Tempo traces for the 'rds-postgres-synthetic' service can reveal slow spans, timeout patterns, or blocking queries causing high CPU usage. This action can efficiently differentiate between expensive queries versus unrelated pipeline or secondary bottlenecks, clarifying the root cause mechanism behind CPU saturation.

**Actions:** `query_grafana_traces`

#### Loop 5

**Planning rationale:** CPU saturation on the RDS instance catalog-prod can be caused by slow/expensive queries, excessive connections, or background system processes. Direct logs and metrics actions are blocked, so first, query_grafana_service_names will check correct service names in Loki to understand if any related log data for query or connection patterns exists but is currently unidentified. Concurrently, get_sre_guidance on hotspotting and resource_planning can provide best practices and hypotheses on expected resource bottlenecks for RDS Postgres pipelines, improving discrimination between traffic spikes, query inefficiency, or connection idleness. This minimal plan efficiently targets root causes related to query and connection load and their handling in pipeline contexts.

**Actions:** `query_grafana_service_names`, `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_logs`: 4 entries
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

- The CPU utilization for `catalog-prod` exceeded 85% for 20 consecutive minutes, peaking at 93.7%. [evidence: grafana_metrics]
- The SQL query `SELECT * FROM orders WHERE status = $1` has a high average active session load of 7.2 and waits predominantly on CPU:user. [evidence: grafana_logs]

## Non-validated claims

- A potential missing index could be causing full table scans, leading to CPU saturation. Confirmation requires analysis of the database indexing strategy and query execution plan.
- The database connection pool exhaustion is unlikely as connections were at 164, and confirmation would require knowing the max connection limit or seeing idle or blocked sessions during the incident.

## Diagnosis

- Predicted root cause: Most likely: The root cause of CPU saturation is a resource exhaustion due to a single SQL query (`SELECT * FROM orders WHERE status = $1`) that has high average active sessions and significant CPU and I/O wait times. No evidence of connection pool leaks or storage exhaustion was found. Missing exact database connection limits would confirm.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     CPU, query, Performance Insights

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 5, after metrics were already queried at step 2. The agent queried metrics on instances it had not yet discovered.
- The agent reached the correct diagnosis category but recorded no causal chain steps. The conclusion appears to be based on pattern-matching rather than traced reasoning.

### Reviewer notes

_(Add manual observations here.)_
