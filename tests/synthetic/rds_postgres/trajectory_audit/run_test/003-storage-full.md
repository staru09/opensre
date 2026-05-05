# Trajectory audit — 003-storage-full

- Captured: 2026-05-05T15:13:37+00:00
- Scenario difficulty: 1
- Failure mode: storage_full
- Status: FAIL
- Failure reason: `missing required keywords: ['FreeStorageSpace']`

## Alert

- Title: [synthetic-rds] Storage Space Critical On orders-prod
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

**Planning rationale:** Given the critical storage space alert on the RDS PostgreSQL instance 'orders-prod', the leading hypotheses are: (1) storage is growing due to accumulation of audit or general logs, (2) long-running or expensive queries causing bloated temporary or log files, or (3) unusual background processes or large data bloat. Querying Grafana Loki logs for the 'rds-postgres-synthetic' service targeting the pipeline 'rds-postgres-synthetic' will help to surface any recent errors, warnings, or log patterns related to transactions, vacuum/autovacuum activity, or high log volumes. This can effectively discriminate between storage growth caused by excessive logging or query activity vs other less common causes without redundant metric or alert configuration queries.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** The alert indicates critical storage space usage on the RDS instance 'orders-prod'. Key root-cause hypotheses include: 1) Storage growth caused by accumulating data such as audit logs or large table bloat; 2) Long-running or blocking queries causing resource pressure and potentially increasing storage usage indirectly; 3) Background processes like WAL or vacuum accumulating storage; or 4) Idle or long-lived connections causing performance degradation that results in storage issues downstream.

To discriminate among these causes efficiently without redundant context, querying Grafana metrics focused on storage growth patterns, database disk usage trends, query latencies, or related resource utilization will help identify whether the storage increase is sudden or gradual, related to workload spikes, or background activity. This action will directly inform if the storage pressure is primarily from data growth, query inefficiency, or system processes.

Blocked actions prevent querying logs, so metrics is the highest yield action to differentiate these potential mechanisms.

**Actions:** `query_grafana_metrics`

#### Loop 3

**Planning rationale:** The alert indicates critical storage space on the orders-prod RDS Postgres instance. Plausible root cause hypotheses include (1) excessive storage usage due to large or growing data, (2) heavy audit or logging activity causing storage bloat, or (3) misconfigured alert thresholds or monitoring gaps. Querying the Grafana alert rules for the rds-postgres-synthetic pipeline will clarify the exact metrics and thresholds being monitored for storage, helping to understand whether the alert corresponds to actual storage metrics or if it's a result of threshold tuning. This also helps eliminate confusion about monitoring coverage for audit logs or VACUUM-related growth. This single action provides high discrimination to confirm the monitoring focus and may guide next steps such as querying logs or traces if slow queries or background processes are suspected. Other actions like tracing or service discovery don't directly target storage growth causes, and logs/metrics queries are blocked, so inspecting alert rules is the most efficient next step.

**Actions:** `query_grafana_alert_rules`

#### Loop 4

**Planning rationale:** The alert indicates critical storage pressure on the orders-prod RDS Postgres instance. Root cause hypotheses include: (1) Storage growth due to extensive audit or general logging increasing disk usage; (2) Long-running or slow queries causing resource contention and possibly blocking cleanup; (3) Idle or long-lived connections not releasing resources; (4) Increased background processes usage (e.g., vacuum, WAL segments) leading to storage buildup. Since query_loki_logs and query_grafana_metrics are blocked, querying Grafana Cloud Tempo traces for the rds-postgres-synthetic service pipeline can help identify slow or blocking queries, long spans, or behavior patterns causing or worsening storage pressure. This can help discriminate between query-related issues vs general background process or connection idling causes, thus providing the best information gain for next diagnosis.

**Actions:** `query_grafana_traces`

#### Loop 5

**Planning rationale:** The alert is about storage space critical for the RDS instance orders-prod. Possible root causes include: (1) storage growth due to background processes like WAL or vacuum bloat, (2) audit or logging mechanisms filling storage, or (3) an abnormal increase in data size caused by workload or long-lived queries. Since we cannot query logs or alert rules directly, first querying available service names in Grafana Loki might reveal relevant related services (e.g., audit logs or background job logs) that can be further investigated later. Retrieving SRE guidance targeted on resource planning and storage growth for pipelines using PostgreSQL RDS will help identify known patterns and remediation approaches, including audit logging impact. This set efficiently rules in/out logging related causes and provides best practices for pipeline resilience under storage pressure.

**Actions:** `query_grafana_service_names`, `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_logs`: 9 entries
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

- DB instance storage is critically low with only 2.5 GB remaining, and eventually, it ran out of storage space. [evidence: grafana_logs]
- Write IOPS were high, indicating ongoing write activity, which likely contributed to storage exhaustion. [evidence: grafana_metrics]

## Non-validated claims

- A connection pool leak leading to excessive idle sessions is not indicated here. Confirmation would require maxed-out connection counts nearing the threshold, which is not provided in the evidence.
- A single bad query driving CPU near 100% is not a supported inference. CPU utilization is moderate and does not approach saturation.

## Diagnosis

- Predicted root cause: Most likely: resource exhaustion due to storage limits being reached on the RDS instance. Writes could not be performed once storage ran out. Evidence shows critically low storage space, and the subsequent state of the DB instance supports this conclusion.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     storage
- Missing keywords:     FreeStorageSpace

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 5, after metrics were already queried at step 2. The agent queried metrics on instances it had not yet discovered.

### Reviewer notes

_(Add manual observations here.)_
