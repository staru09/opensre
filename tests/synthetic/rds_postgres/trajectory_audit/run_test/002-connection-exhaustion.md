# Trajectory audit — 002-connection-exhaustion

- Captured: 2026-05-05T15:12:16+00:00
- Scenario difficulty: 1
- Failure mode: connection_exhaustion
- Status: FAIL
- Failure reason: `missing required keywords: ['client sessions']`

## Alert

- Title: [synthetic-rds] Connection Exhaustion On payments-prod
- Severity: critical

## Trajectory

### Expected (from `answer.yml:optimal_trajectory`)

1. `query_grafana_metrics`
2. `query_grafana_logs`
3. `query_grafana_alert_rules`

### Actual (flattened across investigation loops)

1. `query_grafana_metrics` ✓
2. `query_grafana_logs` ✓
3. `query_grafana_alert_rules` ✓
4. `query_grafana_traces`
5. `get_sre_guidance`
6. `query_grafana_service_names`

### Per investigation loop

#### Loop 1

**Planning rationale:** Connection exhaustion on payments-prod could be caused by idle/long-lived connections, slow or expensive queries, or genuine traffic spikes. Querying Grafana metrics focused on connection count, active vs idle connections, and query performance will clarify whether idle connections or slow queries are the main driver of connection exhaustion. Simultaneously, querying Grafana logs for error patterns or connection-related warnings during the alert timeframe can reveal slow queries, timeouts, or connection reuse issues. Together, these two actions efficiently distinguish among idle connection buildup, query slowness, and traffic spikes without redundant or low-signal data.

**Actions:** `query_grafana_metrics`, `query_grafana_logs`

#### Loop 2

**Planning rationale:** Start by querying the Grafana alert rules for the rds-postgres-synthetic pipeline and payments-prod database to understand what exact metrics or log queries are monitored and what thresholds trigger the connection exhaustion alert. This helps clarify if the alert is monitoring idle connections, active slow queries, or spikes in genuine traffic, enabling us to discriminate between idle connection buildup, slow query load, or traffic spike causes without redundant metrics or logs queries that are blocked.

**Actions:** `query_grafana_alert_rules`

#### Loop 3

**Planning rationale:** The alert indicates connection exhaustion on the payments-prod RDS instance. Plausible root-cause hypotheses include: (1) many idle connections not being reused or cleaned up, (2) slow or expensive queries causing connections to hold, (3) a genuine spike in traffic, or (4) secondary symptoms caused by another bottleneck such as blocking queries or background tasks. Since query_grafana_logs and metrics have been blocked or exhausted, the next best step is to query distributed traces from the rds-postgres-synthetic pipeline to identify request-level latencies, slow or blocking spans, and timeout patterns. This will help discriminate between idle connections and slow queries, as well as reveal potential query bottlenecks or downstream blockers. Tracing data typically gives high information gain about the connection usage mechanism and can rule out or confirm the dominant cause of connection exhaustion more effectively than other options.

**Actions:** `query_grafana_traces`

#### Loop 4

**Planning rationale:** The critical alert for connection exhaustion on the payments-prod RDS PostgreSQL instance suggests multiple plausible root causes: many idle connections causing connection pool exhaustion, slow or blocking queries leading to connection buildup, or a genuine traffic spike causing resource resource pressure. Since querying logs, metrics, traces, and alert rules is blocked or exhausted, the best next step is to get SRE best practice guidance focused on resource planning and known failure patterns for connection exhaustion. This guidance can help differentiate between idle connections versus query-related resource issues and recommend remediation approaches, optimizing further investigation and resolution steps.

**Actions:** `get_sre_guidance`

#### Loop 5

**Planning rationale:** The critical alert indicates connection exhaustion on the 'payments-prod' RDS instance. Key hypotheses include: 1) high number of idle or long-lived connections exhausting connection slots, 2) traffic spike causing genuine increase in active connections, 3) slow or blocking queries holding connections open. Logs or metrics to distinguish these routes are currently unavailable (blocked). Querying available Grafana service names helps identify correct service_name labels for targeted log or trace queries later, enabling discrimination between idle vs active connection issues and potentially identifying query delays or spikes in request volume. This single step maximizes information gain by enabling more focused investigation within the existing constraints.

**Actions:** `query_grafana_service_names`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_metrics`: 20 entries
- `grafana_metric_name`: 19 entries
- `grafana_metrics_service`: 22 entries
- `grafana_logs`: 10 entries
- `grafana_error_logs`: 0 entries
- `grafana_logs_query`: 0 entries
- `grafana_logs_service`: 22 entries
- `grafana_alert_rules`: 0 entries
- `grafana_alert_rules_count`: ? entries
- `grafana_traces`: 0 entries
- `grafana_pipeline_spans`: 0 entries
- `grafana_traces_service`: 22 entries
- `grafana_service_names`: 0 entries

## Validated claims

- The database instance "payments-prod" is approaching the max_connections limit with 469 connections out of 500. [evidence: grafana_logs]
- Application clients reported the error message 'remaining connection slots are reserved for non-replication superuser connections'. [evidence: grafana_logs]

## Non-validated claims

- Connection pool leak may have led to connections being held open longer than necessary. Confirmation would require more detailed connection duration metrics and application logs.
- The high Avg Load on the invoice query (6.2 AAS) might contribute to increased connection usage. This could be confirmed with query performance analysis.

## Diagnosis

- Predicted root cause: The incident was caused by connection exhaustion due to a high number of active database connections nearing the `max_connections` limit, as indicated by 469 out of 500 connections being used. This likely prevented new connections, triggering the error message experienced by the application clients.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     connection, max_connections, idle
- Missing keywords:     client sessions

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 6, after metrics were already queried at step 1. The agent queried metrics on instances it had not yet discovered.

### Reviewer notes

_(Add manual observations here.)_
