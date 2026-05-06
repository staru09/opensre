# Trajectory audit — 012-replication-lag-misleading-events

- Captured: 2026-05-06T06:27:11+00:00
- Scenario difficulty: 3
- Failure mode: replication_lag
- Status: FAIL
- Failure reason: `wrong category: got 'infrastructure', expected 'resource_exhaustion'`

## Statistics

| Metric | Value |
|--------|-------|
| Tool calls | 6 total (6 successful, 0 failed) |
| Loops used | 4 / 4 max |
| Unique tools | 6 |

**Sequence:** `query_grafana_logs` → `query_grafana_alert_rules` → `query_grafana_metrics` → `query_grafana_traces` → `query_grafana_service_names` → `get_sre_guidance`

## Alert

- Title: [synthetic-rds] Replication Lag Critical on reporting-prod
- Severity: critical

## Trajectory

### Expected (from `answer.yml:optimal_trajectory`)

1. `query_grafana_logs`
2. `query_grafana_metrics`
3. `query_grafana_alert_rules`

### Actual (flattened across investigation loops)

1. `query_grafana_logs` ✓
2. `query_grafana_alert_rules` ✓
3. `query_grafana_metrics` ✓
4. `query_grafana_traces`
5. `query_grafana_service_names`
6. `get_sre_guidance`

### Per investigation loop

#### Loop 1

**Planning rationale:** The critical replication lag alert could be due to slow or blocking queries, resource saturation, or replication-specific errors on the reporting-prod RDS instance. Querying Grafana logs for the rds-postgres-synthetic service and pipeline will help uncover specific error or warning patterns, replication-related messages, slow query logs, or other anomalies that explain replication lag. This action will discriminate among root causes such as query slowness, blocking, or replication issues, and help rule out unrelated factors before deeper metrics or traces are explored.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** The 'Replication Lag Critical' alert suggests delays in data replication potentially caused by slow queries, resource bottlenecks, or connection issues. Querying Grafana alert rules will clarify the exact thresholds and monitored metrics, refining hypothesis about replication lag causes. Querying Grafana metrics for the 'rds-postgres-synthetic' service will provide insight into CPU, query latency, throughput, and connection metrics, helping to distinguish between slow or blocking queries, resource saturation, or traffic spikes. These two actions target evidence that discriminates root causes such as high query load, resource pressure, or idle connection buildup, without redundancy or reliance on logs, which are blocked.

**Actions:** `query_grafana_alert_rules`, `query_grafana_metrics`

#### Loop 3

**Planning rationale:** Replication lag issues are often caused by slow or blocking queries, resource contention, or unusual transaction patterns on the replica. Since logs and alert rules investigation paths are blocked, querying distributed traces for the 'rds-postgres-synthetic' pipeline can reveal slow spans or timeouts correlated with the replication lag. This will help identify if the lag is due to query performance or pipeline processing delays, thus discriminating between database-side load, traffic spikes, or pipeline-level bottlenecks efficiently.

**Actions:** `query_grafana_traces`

#### Loop 4

**Planning rationale:** The critical replication lag on the PostgreSQL RDS instance 'reporting-prod' could stem from several causes: workload spikes causing slow or blocking queries, idle or long-lived connections affecting resources, background replication or I/O delays, or potential pipeline misconfigurations. Given that querying logs and metrics has already been exhausted or blocked, querying Grafana Loki service names may identify if the log data is labeled under unexpected service names, allowing for more targeted future investigations if needed. Retrieving SRE guidance specifically for pipeline failure patterns including resource contention, delayed data, and recovery remediation aligns well with understanding and addressing replication lag in synthetic pipelines. This minimal set avoids retracing already blocked paths and better prioritizes discriminating root-cause hypotheses by enabling identification of log sources and best practices for dealing with replication or pipeline lag.

**Actions:** `query_grafana_service_names`, `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence trace

| # | Tool | Result |
|---|------|--------|
| 1 | `query_grafana_logs` | 18 logs, 3 error logs |
| 2 | `query_grafana_alert_rules` | 0 alert rules |
| 3 | `query_grafana_metrics` | 11 metrics |
| 4 | `query_grafana_traces` | 0 traces |
| 5 | `query_grafana_service_names` | 0 service names |
| 6 | `get_sre_guidance` | — |

## Validated claims

- Failover initiated -> failover in progress -> failover completed -> instance available [evidence: Grafana Error Logs]
- The system recovered and workload resumed normally as the instance became available at a new endpoint [evidence: Grafana Error Logs]

## Non-validated claims

- An underlying resource constraint might have triggered the failover; confirming this would require historical health check logs or RDS event details before the failover initiation.
- Potential configuration issues could have delayed replication resumption; confirmation would need access to detailed replication and configuration logs post-failover.

## Diagnosis

- Predicted root cause: The incident was caused by a Multi-AZ failover event in the RDS instance `reporting-prod`, which temporarily disrupted replication and led to a ReplicaLag exceeding 900 seconds. Based on the RDS event timeline (primary evidence source), this was a controlled failover process with no indication of underlying resource exhaustion or configuration issues.
- Predicted category:   `infrastructure`
- Expected category:    `resource_exhaustion`
- Matched keywords:     replica
- Missing keywords:     replication lag, WAL, ETL

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 5, after metrics were already queried at step 3. The agent queried metrics on instances it had not yet discovered.

### Reviewer notes

_(Add manual observations here.)_
