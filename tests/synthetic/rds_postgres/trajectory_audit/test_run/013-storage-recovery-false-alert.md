# Trajectory audit — 013-storage-recovery-false-alert

- Captured: 2026-05-06T06:28:28+00:00
- Scenario difficulty: 3
- Failure mode: healthy
- Status: FAIL
- Failure reason: `wrong category: got 'resource_exhaustion', expected 'healthy'`

## Statistics

| Metric | Value |
|--------|-------|
| Tool calls | 6 total (6 successful, 0 failed) |
| Loops used | 4 / 4 max |
| Unique tools | 6 |

**Sequence:** `query_grafana_logs` → `query_grafana_metrics` → `query_grafana_alert_rules` → `query_grafana_traces` → `query_grafana_service_names` → `get_sre_guidance`

## Alert

- Title: [synthetic-rds] Low FreeStorageSpace on orders-prod
- Severity: warning

## Trajectory

### Expected (from `answer.yml:optimal_trajectory`)

1. `query_grafana_logs`
2. `query_grafana_metrics`
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

**Planning rationale:** The alert indicates low free storage on the RDS instance 'orders-prod', which could be caused by storage growth from audit logs, long-running transactions, or other background processes. Querying Grafana Loki logs for the 'rds-postgres-synthetic' service and pipeline logs around the alert timeframe can help reveal errors, warnings, or specific storage-related issues such as bloat, long-running queries, or increased logging activity. This will help discriminate between potential root causes like heavy audit logging, vacuum delays, or query patterns causing storage pressure.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** The alert is for Low FreeStorageSpace on the RDS instance 'orders-prod'. Plausible hypotheses include: (1) storage consumption caused by increased size of audit or general logs, (2) storage consumed by bloated or inactive database segments due to lack of vacuum or cleanup, or (3) storage pressure from unusually large or slow queries generating temp files. Querying Grafana metrics for RDS storage-related and performance metrics can help reveal patterns of storage growth, disk I/O, and any associated query or resource pressure spikes. This can distinguish if the free storage space drop results from workload (e.g., queries/audit logs) or background maintenance issues, ruling out or confirming log growth or query-caused pressure. This single knowledge-rich query is optimal to discriminate between these root causes before digging deeper into event logs or traces.

**Actions:** `query_grafana_metrics`

#### Loop 3

**Planning rationale:** The alert is for Low FreeStorageSpace on the RDS instance 'orders-prod'. To root cause storage pressure effectively, we need to understand the exact alert query and thresholds triggering the warning; this helps confirm whether it is a real persistent issue or a transient condition. Since logs and metrics queries are blocked, starting with inspecting the alert rule will clarify the monitored metric and help refine hypotheses about storage consumption sources (e.g., whether any specific database tablespace or audit logging is considered). It also aids in deciding if further steps like examining traces or other diagnostics are needed.

**Actions:** `query_grafana_alert_rules`

#### Loop 4

**Planning rationale:** The alert pertains to low FreeStorageSpace on the orders-prod RDS instance. Possible root causes include excessive storage usage from slow or expensive queries, accumulating long-lived idle connections causing performance degradation, or background processes such as WAL or audit logs growing rapidly. Since query and connection logs are blocked, querying Grafana Tempo traces for the rds-postgres-synthetic service offers the best path to identify slow or resource-intensive queries, background process impacts, or pipeline-related database workload changes that can cause storage pressure. This action can distinguish whether the storage issue is driven by query patterns or other workload mechanisms, enabling targeted next steps.

**Actions:** `query_grafana_traces`

#### Loop 5

**Planning rationale:** The core alert is Low FreeStorageSpace on the RDS instance orders-prod. Plausible root causes include: (1) storage consumption growth possibly due to audit or general logging; (2) long-lived or idle connections causing indirect issues with storage growth or retention; (3) slow or blocking queries causing write amplification or bloat; (4) background processes like WAL or vacuum generating unexpected storage use. Since logs and alert rules queries are blocked, discovering the correct service_name via query_grafana_service_names could help prepare future log queries if needed and ensure correctness of telemetry. Additionally, fetching SRE guidance on resource planning or monitoring of pipelines can help rule in or out storage growth causes linked with audit or logging or expected resource pressure patterns. This minimal plan focuses on gathering discriminative evidence on mechanisms behind storage growth and potential pipeline-specific factors in synthetic workloads while positioning further queries correctly.

**Actions:** `query_grafana_service_names`, `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence trace

| # | Tool | Result |
|---|------|--------|
| 1 | `query_grafana_logs` | 10 logs, 0 error logs |
| 2 | `query_grafana_metrics` | 12 metrics |
| 3 | `query_grafana_alert_rules` | 0 alert rules |
| 4 | `query_grafana_traces` | 0 traces |
| 5 | `query_grafana_service_names` | 0 service names |
| 6 | `get_sre_guidance` | — |

## Validated claims

- FreeStorageSpace dropped to 3.6 GB, triggering a warning and autoscaling event. [evidence: grafana_logs]
- Storage autoscaling expanded the storage from 100 GB to 200 GB, resolving the storage space issue. [evidence: grafana_logs]
- WriteIOPS was high, suggesting significant write activity. [evidence: grafana_metrics]
- The high write activity could have been due to a specific increase in transaction volume. Log data or application-level metrics could confirm specific queries or workloads.
- It is possible there were large data imports or other bulk operations. Detailed logs or operational reports would confirm this.

## Diagnosis

- Predicted root cause: Most likely: Storage exhaustion due to high write activity on the orders table. Storage autoscaling resolved the issue by increasing the allocated storage. Specific evidence confirming if the write workload was unsustainable beyond normal operations is missing.
- Predicted category:   `resource_exhaustion`
- Expected category:    `healthy`
- Matched keywords:     autoscal
- Missing keywords:     recovered, no active

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 5, after metrics were already queried at step 2. The agent queried metrics on instances it had not yet discovered.

### Reviewer notes

_(Add manual observations here.)_
