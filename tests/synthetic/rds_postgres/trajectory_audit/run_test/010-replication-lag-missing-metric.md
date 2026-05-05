# Trajectory audit — 010-replication-lag-missing-metric

- Captured: 2026-05-05T15:21:40+00:00
- Scenario difficulty: 3
- Failure mode: replication_lag
- Status: PASS

## Alert

- Title: [synthetic-rds] Replica Stale Reads On reporting-prod
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

**Planning rationale:** The alert is for stale replica reads on the RDS reporting-prod instance, indicating possible replication lag or query slowness on the read replica. To distinguish root causes, first query_grafana_alert_rules to understand exactly what metrics and thresholds triggered the alert (e.g., replication lag, stale reads, or errors). Then query_grafana_logs on the rds-postgres-synthetic pipeline to find pipeline or database errors or warnings that indicate replication lag, long running queries, blocking, or connection issues. These two actions should efficiently narrow down whether the issue is replication delay, query slowness, or pipeline errors causing stale reads.

**Actions:** `query_grafana_alert_rules`, `query_grafana_logs`

#### Loop 2

**Planning rationale:** The critical alert concerns stale reads on the replica 'reporting-prod'. Key hypotheses include: (1) replication lag causing stale reads; (2) blocking or slow queries causing delayed replica updates; (3) resource pressure (CPU, connections) delaying replication apply; (4) background processes like vacuum or WAL shipping issues causing stale data. Querying Grafana Cloud Mimir for relevant RDS and pipeline metrics (replication lag, CPU, connections, IO, query latency) will discriminate among these hypotheses by revealing whether replication lag or resource bottlenecks are dominant drivers. This single action has high information gain to isolate the mechanism underlying the stale reads without redundant log or trace exploration.

**Actions:** `query_grafana_metrics`

#### Loop 3

**Planning rationale:** The critical alert on '[synthetic-rds] Replica Stale Reads On reporting-prod' suggests replication lag or query delay issues on the reporting-prod RDS replica. Key competing hypotheses include replication lag causing stale reads, slow or blocking queries delaying replica catch-up, or synthetic pipeline related application delays. Since querying logs and alert rules are blocked, querying Grafana Tempo traces for the 'rds-postgres-synthetic' service is the best next step to correlate trace timings, identify slow spans or timeouts in the data pipeline accessing the DB, and help distinguish if the stale reads are due to query slowness, bottlenecks in the pipeline, or replication lag impacting the freshness of reads. This single action provides high discriminating evidence between application pipeline delays vs. database-side replication or query performance issues.

**Actions:** `query_grafana_traces`

#### Loop 4

**Planning rationale:** The issue is Replica Stale Reads on RDS Postgres reporting-prod, which suggests replication lag or stale replica reads. The plausible root causes include replication lag causing stale reads, heavy query load or blocking causing lag, or a background process like vacuum or WAL delay causing replication delays. Since querying logs and alerts is blocked and direct database metrics are unavailable, the most discriminating next step is to retrieve SRE best practices for pipeline incidents involving delayed or stale data. This can provide targeted diagnostic and remediation guidance relevant to replication lag and stale reads, helping to prioritize follow-up internal diagnostics or AWS CloudWatch checks. It also efficiently rules out unrelated pipeline failure modes and informs focused next steps.

**Actions:** `get_sre_guidance`

#### Loop 5

**Planning rationale:** The alert is from rds-postgres-synthetic, but no logs queries have been run or returned data yet. To diagnose replica stale reads, key hypotheses include (1) replication lag due to load or internal replication issues, (2) query patterns causing stale reads, or (3) potential synthetic test misconfiguration or absence of data. Since queries to logs or metrics are blocked, the next best step is to confirm the exact Grafana service name to use with queries. This can eliminate confusion about data availability and enable targeted log or metric queries next, thus discriminating between replication issues or synthetic test failures efficiently.

**Actions:** `query_grafana_service_names`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_alert_rules`: 0 entries
- `grafana_alert_rules_count`: ? entries
- `grafana_logs`: 8 entries
- `grafana_error_logs`: 0 entries
- `grafana_logs_query`: 0 entries
- `grafana_logs_service`: 22 entries
- `grafana_metrics`: 19 entries
- `grafana_metric_name`: 19 entries
- `grafana_metrics_service`: 22 entries
- `grafana_traces`: 0 entries
- `grafana_pipeline_spans`: 0 entries
- `grafana_traces_service`: 22 entries
- `grafana_service_names`: 0 entries

## Validated claims

- High primary write throughput is indicated by increased WriteIOPS and transaction log generation on the reporting-prod database. [evidence: Grafana Metrics]
- Replication lag exceeded 900 and then 1800 seconds, indicating the replica was falling significantly behind due to high write activity on the primary. [evidence: Grafana Logs]

## Non-validated claims

- The primary database may lack adequate resources or configurations to handle the write load efficiently. To confirm, resource utilization metrics like memory, disk IOPS on the primary, or any blocking events are needed.

## Diagnosis

- Predicted root cause: Replication lag on the read replica reporting-prod-replica-1 is caused by high primary write throughput on the reporting-prod database. The replication lag is driven by the significant generation of Write-Ahead Logs (WAL) from INSERT operations on the primary database, overwhelming the read replica's ability to replay logs in a timely manner.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     replication, WAL, replica

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 6, after metrics were already queried at step 3. The agent queried metrics on instances it had not yet discovered.
- The agent reached the correct diagnosis category but recorded no causal chain steps. The conclusion appears to be based on pattern-matching rather than traced reasoning.

### Reviewer notes

_(Add manual observations here.)_
