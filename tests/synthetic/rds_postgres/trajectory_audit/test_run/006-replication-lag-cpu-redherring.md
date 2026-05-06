# Trajectory audit — 006-replication-lag-cpu-redherring

- Captured: 2026-05-06T06:25:59+00:00
- Scenario difficulty: 2
- Failure mode: replication_lag
- Status: FAIL
- Failure reason: `missing required keywords: ['causally independent']`

## Statistics

| Metric | Value |
|--------|-------|
| Tool calls | 6 total (6 successful, 0 failed) |
| Loops used | 4 / 4 max |
| Unique tools | 6 |

**Sequence:** `query_grafana_logs` → `query_grafana_metrics` → `query_grafana_alert_rules` → `query_grafana_traces` → `query_grafana_service_names` → `get_sre_guidance`

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

**Planning rationale:** The primary hypothesis is that high CPU and replication lag are due to slow or expensive queries or connection issues on the 'analytics-prod' database. Querying Grafana logs from the 'rds-postgres-synthetic' service for recent pipeline execution runs will help identify slow, blocking, or long-running queries, long-lived or idle connections, and any database-specific errors or warnings. This action best discriminates between query-induced CPU load, connection saturation, and secondary symptoms without redundant metrics or traces at this stage.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** The incident indicates replication lag and high CPU on the analytics-prod RDS. The main hypotheses are: (1) slow or expensive queries causing high CPU and replication lag, (2) too many idle or long-lived connections causing resource contention, and (3) background processes or WAL-related I/O causing the bottleneck. Querying Grafana metrics for relevant RDS and pipeline metrics can reveal CPU utilization patterns, query latency/throughput, connection counts (including idle), and throughput to clarify whether the load is due to query load, connection issues, or background system activity. This single action has high information gain by discriminating among these hypotheses and points to next detailed steps.

**Actions:** `query_grafana_metrics`

#### Loop 3

**Planning rationale:** The main hypotheses for replication lag and high CPU on analytics-prod are: 1) slow or expensive queries causing CPU load and replication lag; 2) excessive or idle connections causing resource pressure; 3) background processes like vacuum or WAL related causing load; 4) external traffic spikes or pipeline failures impacting DB. query_grafana_alert_rules will clarify what exact metrics and thresholds are being monitored, offering insight into what the alert is specifically keyed on and helping to target diagnostics (e.g., query duration, connection counts, CPU thresholds). query_grafana_traces will provide distributed traces of the pipeline to identify if slow or expensive queries or bottlenecks in the pipeline contribute to the symptoms, helping confirm query-related vs external bottlenecks. These two actions provide high-discrimination evidence on root cause mechanisms and help prioritize remediation.

**Actions:** `query_grafana_alert_rules`, `query_grafana_traces`

#### Loop 4

**Planning rationale:** We have a critical alert for replication lag and high CPU on the RDS postgres instance analytics-prod. Leading hypotheses include: (1) slow or expensive queries causing CPU pressure and delaying replication apply; (2) a backlog of idle or long-lived connections creating resource contention; (3) background processes (like vacuum or WAL shipping) causing CPU spikes or replication delay; and (4) genuine traffic spikes leading to CPU and replication stress. Since log and alert rules queries are blocked, querying available service names in Grafana Loki might uncover relevant service labels or new logs to identify query or connection patterns without unnecessarily repeating the blocked actions. Additionally, retrieving SRE best practices for resource planning and hotspotting will help validate if current symptoms align with known pipeline failures from CPU and replication lag, and guide remediation. This minimal set can sharply differentiate between connection-based, query-based, or background workload causes for CPU and lag issues.

**Actions:** `query_grafana_service_names`, `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence trace

| # | Tool | Result |
|---|------|--------|
| 1 | `query_grafana_logs` | 7 logs, 0 error logs |
| 2 | `query_grafana_metrics` | 20 metrics |
| 3 | `query_grafana_alert_rules` | 0 alert rules |
| 4 | `query_grafana_traces` | 0 traces |
| 5 | `query_grafana_service_names` | 0 service names |
| 6 | `get_sre_guidance` | — |

## Validated claims

- The write-heavy workload on the primary database led to high Write IOPS. [evidence: {"metric": {"__name__": "aws_rds_write_iops_average", "dbinstanceidentifier": "analytics-prod"}, "values": [[1774605660.0, "12840.0"], [1774605720.0, "17210.0"]]]
- There was significant replication lag exceeding 900 seconds on the read replica. [evidence: Grafana Logs (7 events): Read replica analytics-prod-replica-1 replication lag has exceeded 900 seconds.]

## Non-validated claims

- The CPU usage increase is primarily due to WAL:Lock wait events and a large transaction log generation, not directly causing the replication lag. Confirmation would require telemetry showing the transaction log impact on WAL locking.
- The SELECT query from `Top SQL Activity` may be contributing to CPU load but is not the root cause of replication lag. Confirmation would require additional evidence separating CPU spikes due to read operations from write-heavy logs impact.

## Diagnosis

- Predicted root cause: Most likely: The root cause is a heavy write workload on the primary database causing high Write IOPS and WAL generation, which leads to replication lag on the read replica. The CPU spike on the primary is a red herring as it correlates with the workload but is not causing the lag. The specific evidence missing is a direct correlation of the `UPDATE` query with the replication lag, as well as metrics confirming no additional root causes contributing to the CPU load.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     replication, replication lag, WAL, replica, UPDATE, SELECT
- Missing keywords:     causally independent

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 5, after metrics were already queried at step 2. The agent queried metrics on instances it had not yet discovered.

### Reviewer notes

_(Add manual observations here.)_
