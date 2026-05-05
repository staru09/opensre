# Trajectory audit — 013-storage-recovery-false-alert

- Captured: 2026-05-05T15:24:45+00:00
- Scenario difficulty: 3
- Failure mode: healthy
- Status: FAIL
- Failure reason: `wrong category: got 'resource_exhaustion', expected 'healthy'`

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
2. `query_grafana_alert_rules` ✓
3. `query_grafana_metrics` ✓
4. `query_grafana_traces`
5. `query_grafana_service_names`
6. `get_sre_guidance`

### Per investigation loop

#### Loop 1

**Planning rationale:** The alert indicates low free storage space on the Postgres RDS instance 'orders-prod'. To understand the root cause, we need to check for recent activity that could cause a sudden or continuous growth in storage usage. This includes heavy or long-running queries, bulk inserts, vacuuming/logging issues, or audit log growth. Querying Grafana logs for the 'rds-postgres-synthetic' pipeline will help reveal any errors, warnings, or activity patterns correlating with storage pressure. This can differentiate between causes like slow/blocking queries generating storage bloat, background process issues, or audit/log growth, without redundant data gathering.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** The alert is for low FreeStorageSpace on the RDS instance 'orders-prod', which can be caused by factors such as increased storage usage due to audit logs or heavy query activity, or configuration issues in alert thresholds. To discriminate root causes, first querying the alert rules will clarify the exact conditions and thresholds for the warning, useful for interpreting current alerts properly. Then querying Grafana metrics focused on relevant storage and database resource metrics (e.g., storage usage trends, database throughput or query rate) will help identify if storage growth corresponds to increased audit log activity, query load, or other pressure driving storage exhaustion. This combination provides direct evidence to confirm or refute hypotheses on storage pressure sources without redundant log or trace queries.

**Actions:** `query_grafana_alert_rules`, `query_grafana_metrics`

#### Loop 3

**Planning rationale:** The alert indicates Low FreeStorageSpace on the RDS instance orders-prod, which can be caused by factors such as storage growth from audit or general logging, slow or blocking queries causing backlogs, or long-lived idle connections. Since logs and alert rules queries are blocked, querying Grafana Tempo traces for the rds-postgres-synthetic service will help reveal any slow or expensive queries, blocking behavior, or bottlenecks during pipeline execution. This can discriminate between workload-driven storage growth from background processes or query patterns, which will guide targeted remediation steps. Traces have high information gain to identify if pipeline query behavior is causing storage pressure or if the problem stems from other background processes or connection issues.

**Actions:** `query_grafana_traces`

#### Loop 4

**Planning rationale:** The alert indicates low free storage space on the orders-prod RDS Postgres instance. Plausible root-cause hypotheses include: (1) genuine storage growth due to large data ingestion or accumulation (e.g., audit logs, table bloat), (2) long-lived or idle connections causing resource pressure indirectly, (3) background processes like vacuum or WAL logs causing unexpected storage usage, or (4) no significant storage-related activity but an alert misconfiguration or transient state. Since querying Grafana logs and alert rules has already been exhausted, the next best step is to confirm which service names in Loki hold logs for the rds-postgres-synthetic pipeline, to better target further analysis if needed downstream. This action narrowly focuses on identifying relevant services that can support later root cause differentiation without repeating exhausted log or alert rule data queries.

**Actions:** `query_grafana_service_names`

#### Loop 5

**Planning rationale:** The alert indicates low FreeStorageSpace on the orders-prod RDS PostgreSQL instance. Plausible causes include: rapid storage growth from audit or general query logging, or vacuum/wal bloat issues causing storage pressure, or unexpected workload spikes increasing storage use. Since direct log or metrics queries are blocked, getting SRE best practices on resource planning and monitoring pipelines for storage issues can guide focused investigation and remediation. This helps differentiate whether the problem stems from workload patterns, logging behaviors, or maintenance tasks, providing guidance on next concrete steps beyond generic context.

**Actions:** `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_logs`: 10 entries
- `grafana_error_logs`: 0 entries
- `grafana_logs_query`: 0 entries
- `grafana_logs_service`: 22 entries
- `grafana_alert_rules`: 0 entries
- `grafana_alert_rules_count`: ? entries
- `grafana_metrics`: 12 entries
- `grafana_metric_name`: 19 entries
- `grafana_metrics_service`: 22 entries
- `grafana_traces`: 0 entries
- `grafana_pipeline_spans`: 0 entries
- `grafana_traces_service`: 22 entries
- `grafana_service_names`: 0 entries

## Validated claims

- Free storage space on the orders-prod database instance dropped below 10 GB triggering a warning [evidence: Grafana Logs].
- Storage autoscaling successfully increased the allocated storage from 100 GB to 200 GB, resolving the low storage condition [evidence: Grafana Logs].

## Non-validated claims

- No confirmed evidence of write IOPS collapsing due to storage exhaustion prior to autoscaling; metrics before expansion do not show blocked writes explicitly. Verification would require missing metrics indicating drop to 0 IOPS or explicit RDS event logs indicating storage blockage.

## Diagnosis

- Predicted root cause: Most likely: Resource exhaustion due to low free storage space initially triggered the alert, which was resolved by storage autoscaling. The claim is based on observed evidence of storage nearing depletion and subsequent successful autoscaling. However, direct confirmation of storage blockage effects (e.g., write IO failure) before autoscaling is missing.
- Predicted category:   `resource_exhaustion`
- Expected category:    `healthy`
- Matched keywords:     autoscal
- Missing keywords:     recovered, no active

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 5, after metrics were already queried at step 3. The agent queried metrics on instances it had not yet discovered.

### Reviewer notes

_(Add manual observations here.)_
