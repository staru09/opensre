# Trajectory audit — 011-cpu-storage-compositional

- Captured: 2026-05-05T15:22:26+00:00
- Scenario difficulty: 4
- Failure mode: cpu_saturation
- Status: PASS

## Alert

- Title: [synthetic-rds] High CPU and Disk Pressure on analytics-prod
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

**Planning rationale:** The critical high CPU and disk pressure on the RDS instance 'analytics-prod' can stem from several root causes: (1) slow, expensive, or blocking queries consuming CPU and IO; (2) excessive or idle connections causing overhead; (3) background processes like autovacuum or WAL/logging spikes causing storage and CPU pressure. Querying Grafana Loki logs for the rds-postgres-synthetic service provides direct insight into pipeline or database-side error patterns, slow query indications, or log warnings about stalled queries or storage pressure. These logs can simultaneously reveal slow/expensive queries, connection saturation issues, and background process logs, thus best discriminating among root cause hypotheses. This single action offers high information gain about the mechanism behind resource pressure, ruling in or out major explanatory categories efficiently.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** To investigate the root cause of high CPU and disk pressure on the analytics-prod RDS instance, the primary hypotheses include: (1) a genuine spike in query load causing resource exhaustion, (2) presence of slow or expensive queries disproportionately using CPU and I/O, (3) a buildup of background processes like vacuum or audit logging causing disk pressure, or (4) a high number of idle connections contributing to resource usage. Querying Grafana Cloud Mimir metrics focused on this RDS service can reveal query throughput patterns, CPU and disk utilization trends, active connection counts (including idle vs. active if labeled), and possibly indicators of background maintenance activities. This action is expected to help differentiate between traffic spikes, expensive queries, or background overhead as the mechanism behind the resource pressure, thus eliminating multiple competing hypotheses at once with minimal overhead.

**Actions:** `query_grafana_metrics`

#### Loop 3

**Planning rationale:** The critical alert indicates high CPU and disk pressure on the analytics-prod RDS PostgreSQL instance. Plausible root causes include: (1) slow/expensive queries causing CPU and I/O pressure, (2) excessive idle or long-lived connections contributing to resource exhaustion, or (3) background processes like autovacuum or WAL activity causing storage I/O and CPU spikes. To discriminate among these, querying the Grafana alert rules will clarify exactly what metrics and thresholds triggered the alert and may highlight if connection counts or query latency are monitored. Querying Grafana traces for the rds-postgres-synthetic service can reveal slow, expensive or blocking query patterns reflected in distributed traces, helping to confirm if query workload patterns drive resource pressure versus other causes. These two actions have high information gain and directly target the mechanism creating the observed symptoms.

**Actions:** `query_grafana_alert_rules`, `query_grafana_traces`

#### Loop 4

**Planning rationale:** The alert is for high CPU and disk pressure on the RDS instance analytics-prod. Competing root-cause hypotheses include: (1) heavy/slow query load causing CPU spikes, (2) large numbers of idle or long-lived connections causing resource contention, (3) background processes such as WAL or vacuum causing disk pressure, or (4) audit/log growth causing storage issues. Since querying Grafana logs or metrics is blocked, the next best step is to confirm the exact service names in Grafana Loki to ensure correct targeting for further log or performance inquiries (if possible). This will prepare to discriminate between query-driven load and connection or background load causes once logs or performance insights can be accessed or re-attempted, avoiding redundant or miss-targeted queries later.

**Actions:** `query_grafana_service_names`

#### Loop 5

**Planning rationale:** The critical high CPU and disk pressure on the analytics-prod RDS instance can be caused by multiple factors including expensive query load, long-lived or idle connections, or background processes like vacuum or audit logging causing storage pressure. Since direct queries to Grafana logs and metrics are blocked, the next best step is to retrieve SRE best practices focused on resource planning and hotspotting specific to RDS/Postgres synthetic pipelines. This action can provide targeted guidance on common causes and remediation patterns, helping distinguish whether the issue likely stems from query patterns, connection management, or storage growth, improving the reliability of the root cause hypotheses and guiding next steps efficiently.

**Actions:** `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_logs`: 16 entries
- `grafana_error_logs`: 1 entries
- `grafana_logs_query`: 0 entries
- `grafana_logs_service`: 22 entries
- `grafana_metrics`: 15 entries
- `grafana_metric_name`: 19 entries
- `grafana_metrics_service`: 22 entries
- `grafana_alert_rules`: 0 entries
- `grafana_alert_rules_count`: ? entries
- `grafana_traces`: 0 entries
- `grafana_pipeline_spans`: 0 entries
- `grafana_traces_service`: 22 entries
- `grafana_service_names`: 0 entries

## Validated claims

- Storage space on the DB instance analytics-prod is critically low with only 8.3 GB free of 200 GB, possibly blocking writes soon. [evidence: Grafana Error Logs]
- CPU utilization is increasing, reaching high levels over time. [evidence: Grafana Metrics (aws_rds_cpu_utilization_average)]

## Non-validated claims

- Connection pool leaks as a contributor to resource exhaustion. Confirmation would require connection trend and session activity details.
- High CPU usage caused by specific queries (e.g., full table scans) not identified in the provided evidence; Performance Insights data would help confirm.

## Diagnosis

- Predicted root cause: Most likely: Storage exhaustion due to sustained audit_log insert workload, and high CPU usage driven by concurrent processes. The exact queries or operations causing high CPU are not identified; additional query analysis metrics would confirm the source of CPU pressure.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     CPU, storage, analytics, audit_log

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 5, after metrics were already queried at step 2. The agent queried metrics on instances it had not yet discovered.
- The agent reached the correct diagnosis category but recorded no causal chain steps. The conclusion appears to be based on pattern-matching rather than traced reasoning.

### Reviewer notes

_(Add manual observations here.)_
