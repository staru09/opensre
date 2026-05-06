# Trajectory audit — 002-connection-exhaustion

- Captured: 2026-05-06T06:38:32+00:00
- Scenario difficulty: 1
- Failure mode: connection_exhaustion
- Status: FAIL
- Failure reason: `missing required keywords: ['client sessions']`

## Statistics

| Metric | Value |
|--------|-------|
| Tool calls | 5 total (5 successful, 0 failed) |
| Loops used | 4 / 4 max |
| Unique tools | 5 |

**Sequence:** `query_grafana_metrics` → `query_grafana_logs` → `query_grafana_alert_rules` → `query_grafana_traces` → `get_sre_guidance`

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

### Per investigation loop

#### Loop 1

**Planning rationale:** The alert indicates connection exhaustion on the payments-prod RDS instance. To discriminate among key root-cause hypotheses—whether caused by idle connections not being closed, slow or expensive queries holding connections, or a genuine traffic spike causing increased connection demand—querying Grafana metrics for connection counts, their state (active vs idle), and related query performance metrics is the most direct and high-information action. This will help identify if connection usage is driven by traffic (active connections), blocked/long queries holding connections, or accumulation of idle connections. It avoids redundant log or trace queries at this stage by targeting the database metrics that directly reflect connection states and resource usage patterns, thus improving final root cause reliability with minimal effort.

**Actions:** `query_grafana_metrics`

#### Loop 2

**Planning rationale:** The alert indicates a critical connection exhaustion issue on the 'payments-prod' RDS instance. To discriminate among potential causes—such as idle long-lived connections, traffic spikes resulting in many active connections, or slow/blocked queries holding connections—we need detailed logs correlating to connection usage and query activity. Querying Grafana logs (Loki) for the 'rds-postgres-synthetic' service on the affected pipeline allows us to directly check error patterns, connection states, and query delays that cause connection exhaustion, thus ruling out or confirming idle connections versus slow queries or a genuine traffic spike. This single targeted action provides high information gain to distinguish root causes efficiently without redundant context or configuration data.

**Actions:** `query_grafana_logs`

#### Loop 3

**Planning rationale:** The alert indicates 'Connection Exhaustion' on the payments-prod RDS instance. To discriminate the root cause, the key hypotheses are: (1) idle connections causing exhaustion, (2) slow or expensive queries holding connections too long, (3) genuine traffic spike increasing connection demand, or (4) a secondary bottleneck manifesting as connection saturation. Since querying logs and metrics is blocked, inspecting the configured Grafana alert rules for rds-postgres-synthetic will reveal the exact metrics and thresholds monitored for connections and related database health. This helps us understand if the alert is triggered due to total connection counts, idle connection counts, or query performance indicators, thus narrowing which mechanism is dominant without redundant data collection.

**Actions:** `query_grafana_alert_rules`

#### Loop 4

**Planning rationale:** Hypotheses for connection exhaustion include: (1) many idle or long-lived connections causing exhaustion, (2) slow/expensive queries holding connections longer than usual, (3) genuine traffic spikes increasing connection demand suddenly, or (4) secondary symptoms from another bottleneck increasing connection usage. Querying Grafana traces for the rds-postgres-synthetic pipeline will help identify if the pipeline queries are slow, timing out, or have blocked spans, which can clarify whether slow/expensive queries or backpressure from other bottlenecks are causing connection exhaustion. This discriminates between idle vs active connection pressure mechanisms and rules out underlying query or trace-based issues without redundant log or alert rule queries, which are blocked.

**Actions:** `query_grafana_traces`

#### Loop 5

**Planning rationale:** The alert indicates connection exhaustion on the 'payments-prod' RDS Postgres instance. Plausible causes include idle connections not closing, slow or expensive queries causing connections to pile up, or a genuine spike in legitimate traffic. Since other data queries and alerts investigation paths (logs, traces, alert rules, metrics) are blocked, the best next step is to retrieve SRE best practices guiding investigation and remediation of connection exhaustion and resource pressure. This will help differentiate between idle connections, query performance issues, and other pipeline bottlenecks without redundant or unavailable data sources. This action has the highest information gain to guide targeted next steps and improve RCA quality under limited tooling.

**Actions:** `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Diagnostic trace

### Step 1 — `query_grafana_metrics`

**Output:**
```
{"source": "grafana_mimir", "available": true, "metrics": [{"metric": {"__name__": "aws_rds_database_connections_maximum", "dbinstanceidentifier": "payments-prod"}, "values": [[1774525800.0, "312.0"], [1774525860.0, "341.0"], [1774525920.0, "368.0"], [1774525980.0, "392.0"], [1774526040.0, "411.0"], [1774526100.0, "429.0"], [1774526160.0, "444.0"], [1774526220.0, "458.0"], [1774526280.0, "469.0"], [1774526340.0, "477.0"], [1774526400.0, "484.0"], [1774526460.0, "489.0"], [1774526520.0, "492.0"], [1774526580.0, "493.0"], [1774526640.0, "494.0"]]}, {"metric": {"__name__": "aws_rds_cpu_utilization_average", "dbinstanceidentifier": "payments-prod"}, "values": [[1774525800.0, "18.24"], [1774525860.0, "17.85"], [1774525920.0, "19.5"], [1774525980.0, "16.42"], [1774526040.0, "46.3"], [1774526100.0, "47.9"], [1774526160.0, "48.5"], [1774526220.0, "49.1"], [1774526280.0, "49.6"], [1774526340.0, "49.8"], [1774526400.0, "50.1"], [1774526460.0, "49.9"], [1774526520.0, "50.2"], [1774526580.0, "49.7"], [1774526640.0, "50.0"]]}, {"metric": {"__name__": "aws_rds_replica_lag_maximum", "dbinstanceidentifier": "payments-prod-replica-1"}, "values": [[1774525800.0, "1.2"], [1774525860.0, "1.4"], [1774525920.0, "1.1"], [1774525980.0, "1.3"], [1774526040.0, "1.5"], [1774526100.0, "1.2"], [1774526160.0, "1.4"], [1774526220.0, "1.3"], [1774526280.0, "1.2"], [1774526340.0, "1.4"], [1774526400.0, "1.3"], [1774526460.0, "1.5"], [1774526520.0, "1.2"], [1774526580.0, "1.4"], [1774526640.0, "1.3"]]}, {"metric": {"__name__": "aws_rds_free_storage_space_minimum", "dbinstanceidentifier": "payments-prod"}, "values": [[1774525800.0, "193273528320.0"], [1774525860.0, "193273528320.0"], [1774525920.0, "193273528320.0"], [1774525980.0, "193273528320.0"], [1774526040.0, "193273528320.0"], [1774526100.0, "193273528320.0"], [1774526160.0, "193273528320.0"], [1774526220.0, "193273528320.0"], [1774526280.0, "193273528320.0"], [1774526340.0, "193273528320.0"], [1774526400.0, "193273528320.0"], [1774526460.0, "... [truncated]
```

### Step 2 — `query_grafana_logs`

**Output:**
```
{"source": "grafana_loki", "available": true, "logs": [{"message": "Top SQL Activity: BEGIN; SELECT * FROM invoices WHERE account_id = $1 | Avg Load: 6.2 AAS | Waits: Client:ClientRead(5.8), CPU(0.4)", "log_level": "", "count": 1, "first_seen": "1774525800000000000", "last_seen": "1774525800000000000"}, {"message": "Top SQL Activity: SELECT id, status, total FROM orders WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2 | Avg Load: 0.6 AAS | Waits: IO:DataFileRead(0.4), CPU(0.2)", "log_level": "", "count": 1, "first_seen": "1774525800000000000", "last_seen": "1774525800000000000"}, {"message": "Top SQL Activity: UPDATE user_sessions SET last_seen_at = $1 WHERE session_id = $2 | Avg Load: 0.3 AAS | Waits: IO:WALWrite(0.2), CPU(0.1)", "log_level": "", "count": 1, "first_seen": "1774525800000000000", "last_seen": "1774525800000000000"}, {"message": "Top Wait Event: Client:ClientRead | db_load_avg: 5.8 AAS", "log_level": "", "count": 1, "first_seen": "1774525800000000000", "last_seen": "1774525800000000000"}, {"message": "Top Wait Event: CPU | db_load_avg: 0.7 AAS", "log_level": "", "count": 1, "first_seen": "1774525800000000000", "last_seen": "1774525800000000000"}, {"message": "Top Wait Event: IO:DataFileRead | db_load_avg: 0.4 AAS", "log_level": "", "count": 1, "first_seen": "1774525800000000000", "last_seen": "1774525800000000000"}, {"message": "Top Wait Event: IO:WALWrite | db_load_avg: 0.2 AAS", "log_level": "", "count": 1, "first_seen": "1774525800000000000", "last_seen": "1774525800000000000"}, {"message": "Top Wait Event: Lock:relation | db_load_avg: 0.1 AAS", "log_level": "", "count": 1, "first_seen": "1774525800000000000", "last_seen": "1774525800000000000"}, {"message": "DB instance payments-prod is approaching max_connections limit. Current connections: 469 of 500.", "log_level": "", "count": 1, "first_seen": "1774526280000000000", "last_seen": "1774526280000000000"}, {"message": "Application clients reported 'remaining connection slots are reserved for n... [truncated]
```

### Step 3 — `query_grafana_alert_rules`

**Output:**
```
{"source": "grafana_alerts", "available": true, "raw": {"groups": [{"name": "rds-postgres-synthetic", "rules": [{"state": "firing", "name": "RDSDatabaseConnectionsHigh", "labels": {"alertname": "RDSDatabaseConnectionsHigh", "severity": "critical", "pipeline_name": "rds-postgres-synthetic", "service": "rds", "engine": "postgres"}, "annotations": {"summary": "DatabaseConnections reached 98% of max_connections and application traffic started receiving too many clients errors.", "error": "remaining connection slots are reserved for non-replication superuser connections", "suspected_symptom": "API requests intermittently fail because the pool cannot obtain new sessions.", "db_instance_identifier": "payments-prod", "db_instance": "payments-prod", "db_cluster": "payments-cluster", "cloudwatch_region": "us-east-1", "rds_failure_mode": "connection_exhaustion", "context_sources": "cloudwatch"}}]}]}}
```

### Step 4 — `query_grafana_traces`

**Output:**
```
{"source": "grafana_tempo", "available": true, "traces": [], "pipeline_spans": [], "total_traces": 0, "service_name": "rds-postgres-synthetic", "execution_run_id": null}
```

### Step 5 — `get_sre_guidance`

**Output:**
```
{"success": false, "topics": [], "guidance": [], "sources": [], "message": "No matching SRE guidance found for provided keywords"}
```

## Evidence trace

| # | Tool | Result |
|---|------|--------|
| 1 | `query_grafana_metrics` | 20 metrics |
| 2 | `query_grafana_logs` | 10 logs, 0 error logs |
| 3 | `query_grafana_alert_rules` | 0 alert rules |
| 4 | `query_grafana_traces` | 0 traces |
| 5 | `get_sre_guidance` | — |

## Validated claims

- The payment-prod database instance is approaching its maximum connection limit, with 469 out of 500 connections in use [evidence: Grafana Logs].
- Application clients are receiving error messages indicating reserved connection slots for non-replication superuser connections [evidence: Grafana Logs, Error Message].

## Non-validated claims

- A connection pool leak may exist, causing connections not to be released properly and contributing to the exhaustion. This could be confirmed by examining application connection pool settings and the duration of idle connections [evidence missing: detailed connection duration or pool configuration data].
- If select statement logs were reviewed, it might reveal that specific queries or operations are being executed unnecessarily frequently, leading to excessive connections being maintained [evidence missing: detailed log of specific query executions over time].

## Diagnosis

- Predicted root cause: Most likely: Connection pool exhaustion due to a high number of active connections approaching the maximum allowed, causing new connection attempts to be rejected [evidence missing: specific details on which processes or applications are responsible for the majority of connections].
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     connection, max_connections, idle
- Missing keywords:     client sessions

## Observations

_No issues auto-detected. Reviewer: read the per-loop rationale above and add notes below._

### Reviewer notes

_(Add manual observations here.)_
