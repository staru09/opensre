# Trajectory audit — 009-dual-fault-connection-cpu

- Captured: 2026-05-05T15:20:35+00:00
- Scenario difficulty: 4
- Failure mode: connection_exhaustion
- Status: PASS

## Alert

- Title: [synthetic-rds] Connection Exhaustion And CPU Saturation On search-prod
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
5. `get_sre_guidance`
6. `query_grafana_service_names`

### Per investigation loop

#### Loop 1

**Planning rationale:** The alert indicates connection exhaustion and CPU saturation on the 'search-prod' RDS instance. To diagnose the root cause, we need to determine whether the high connections are due to idle/long-lived connections or active slow/expensive queries driving CPU load. Querying Grafana logs with appropriate filters can reveal query errors, slow queries, or connection patterns indicating idle or stuck sessions. Querying metrics will show CPU usage trends, active connection counts, and possibly query latencies or throughput patterns to discriminate between genuine traffic spikes or blocking/expensive queries causing saturation. Together, logs and metrics provide the minimal, highest-information evidence to distinguish whether the issue is caused by active query load, idle connection leaks, or secondary bottlenecks.

**Actions:** `query_grafana_logs`, `query_grafana_metrics`

#### Loop 2

**Planning rationale:** The alert is for connection exhaustion and CPU saturation on the 'search-prod' RDS instance. Key hypotheses include whether the high connections are caused mainly by idle/long-lived connections, slow/expensive queries causing CPU spikes, or bursts of genuine traffic. Querying the Grafana alert rules for the rds-postgres-synthetic pipeline will reveal the exact monitored metrics, thresholds, and queries behind the alerts. This helps to confirm what is being tracked (e.g., idle connections vs active connections, CPU by query type), and guide deeper diagnosis with focused evidence later. It also eliminates uncertainty about monitoring coverage and ensures we understand what triggered the critical alert.

**Actions:** `query_grafana_alert_rules`

#### Loop 3

**Planning rationale:** To diagnose connection exhaustion and CPU saturation on the RDS database 'search-prod', we need to understand whether slow or expensive queries are causing CPU pressure and contributing to connection saturation. Querying Grafana Tempo traces for the rds-postgres-synthetic pipeline will help identify slow query spans, query patterns, or blocking issues reflected in distributed traces. This will also help assess if genuine traffic spikes or inefficient queries are driving the problem, and if idle or long-lived connections correlate with trace delays. Since alert rules, logs, and metrics have already been explored, tracing is the best remaining high information gain approach to discriminate among idle connections, query bottlenecks, blocking queries, or other secondary symptoms causing resource exhaustion.

**Actions:** `query_grafana_traces`

#### Loop 4

**Planning rationale:** The alert indicates connection exhaustion and CPU saturation on RDS Postgres 'search-prod'. The most plausible root causes include: (1) many idle or long-lived connections exhausting connection pool limits, (2) slow or expensive queries causing high CPU and connection retention, (3) genuine traffic spikes increasing load, or (4) background processes (vacuum, audit logging) contributing to CPU pressure. Since querying Grafana logs, metrics, and alert rules is blocked, the best next step is to retrieve SRE best practices focused on resource planning, hotspotting, and pipeline monitoring to align investigation heuristics and surface relevant query patterns or connection pitfalls. This can guide targeted follow-ups and help discriminate between idle connection issues vs. expensive query load vs. background process impact.

**Actions:** `get_sre_guidance`

#### Loop 5

**Planning rationale:** The critical alert indicates connection exhaustion and CPU saturation on the RDS instance 'search-prod'. To discriminate among key root cause hypotheses—such as idle connections causing exhaustion, slow or expensive queries causing CPU spikes, or a genuine traffic spike—we first need to ensure correct identification of the relevant service name(s) in Grafana Loki. This will enable subsequent targeted log queries and metrics correlation if necessary. Since querying logs, metrics, traces, and alert rules are blocked or exhausted, discovering available service names is the next high-value step for focusing diagnostics properly in the logs and tracing infrastructure.

**Actions:** `query_grafana_service_names`

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

- DB instance `search-prod` has a connection count close to the maximum of 5000, indicating potential connection exhaustion. [evidence: Grafana Logs]
- The CPU utilization is near 90%, suggesting significant load, likely a secondary symptom of resource exhaustion. [evidence: Grafana Metrics]
- Error messages indicate new connections are being refused due to resource exhaustion. [evidence: Error Message]

## Non-validated claims

- Connection pool leaks could have led to the exhaustion of connections. Data on session durations and number of active connections would confirm or refute this.
- A specific heavy query might be indirectly contributing to high CPU usage. Detailed query performance insights would be needed to confirm.

## Diagnosis

- Predicted root cause: Most likely: Connection pool exhaustion is the root cause, exacerbating CPU usage due to accumulated idle sessions holding resources. Missing detailed query analysis to confirm or refute connection pool leaks.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     connection, connection pool leak, idle, Client:ClientRead, CPU, root

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 6, after metrics were already queried at step 2. The agent queried metrics on instances it had not yet discovered.
- The agent reached the correct diagnosis category but recorded no causal chain steps. The conclusion appears to be based on pattern-matching rather than traced reasoning.

### Reviewer notes

_(Add manual observations here.)_
