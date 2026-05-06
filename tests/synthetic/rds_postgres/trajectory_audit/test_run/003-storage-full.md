# Trajectory audit — 003-storage-full

- Captured: 2026-05-06T06:24:48+00:00
- Scenario difficulty: 1
- Failure mode: storage_full
- Status: FAIL
- Failure reason: `missing required keywords: ['FreeStorageSpace']`

## Statistics

| Metric | Value |
|--------|-------|
| Tool calls | 6 total (6 successful, 0 failed) |
| Loops used | 4 / 4 max |
| Unique tools | 6 |

**Sequence:** `query_grafana_logs` → `query_grafana_alert_rules` → `query_grafana_metrics` → `query_grafana_traces` → `query_grafana_service_names` → `get_sre_guidance`

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
2. `query_grafana_alert_rules` ✓
3. `query_grafana_metrics` ✓
4. `query_grafana_traces`
5. `query_grafana_service_names`
6. `get_sre_guidance`

### Per investigation loop

#### Loop 1

**Planning rationale:** The alert indicates critical storage space pressure on the 'orders-prod' RDS instance, pointing to potential causes such as audit log growth, long-lived or idle connections generating WAL, or slow/expensive queries causing storage bloat. Querying the Grafana logs for the 'rds-postgres-synthetic' service will help identify any pipeline errors, signs of abnormal query patterns, or background activities (e.g., vacuum or audit logging processes) in the relevant time window, which can discriminate between storage bloat causes and uncover mechanisms contributing to storage usage growth.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** The alert signals critical storage space on RDS orders-prod. Plausible hypotheses: (1) Storage pressure caused by growing audit or general log table data; (2) Storage pressure due to long-lived or idle connections causing resource locking; (3) Storage usage due to background processes like WAL or vacuum-related files not functioning well. First, querying the Grafana alert rules will expose the exact metric and threshold monitored, which will clarify whether the alert focuses specifically on storage usage, influenced tables, or logs. Second, querying Grafana metrics for the orders-prod service will help identify trends in storage use and resource metrics that can indicate query load, connection behavior, or storage bloat effects. This combo tightly focuses on understanding the monitored storage space issue and its mechanism, which rules out unrelated causes and directs next investigation steps.

**Actions:** `query_grafana_alert_rules`, `query_grafana_metrics`

#### Loop 3

**Planning rationale:** The incident is critical storage pressure on the 'orders-prod' RDS instance. Plausible root causes include uncontrolled storage growth from audit/log data, slow or blocking queries causing long-lived transactions that prevent space reclamation, or background processes like vacuum operations not keeping up. Querying Grafana Tempo traces for the rds-postgres-synthetic service will help identify any slow queries or transaction patterns related to storage usage spikes during pipeline runs. This single targeted action can help discriminate between query-driven storage growth and background process issues or idle transaction locking, improving the quality of the final root cause analysis.

**Actions:** `query_grafana_traces`

#### Loop 4

**Planning rationale:** The alert indicates critical storage space issues on the RDS instance orders-prod. Plausible root causes include: (1) storage growth from audit or general logging, (2) inefficient queries or transactions leading to long-lived connections or bloat, (3) background system processes (e.g. vacuum, WAL) causing storage pressure, or (4) an external traffic spike generating data quickly. Since query_grafana_logs and other Grafana queries are exhausted, using query_grafana_service_names can confirm if correct service labels are known and potentially reveal related services emitting logs that might help focus further evidence outside the blocked paths. Simultaneously, get_sre_guidance focused on 'resource_planning' and 'recovery_remediation' with keywords related to storage and logging will provide best practice insights on diagnosing and remediating critical storage pressure in pipelines. This minimal set targets both new evidence sources and remediation context to refine root cause hypotheses without redundant or already blocked log/metric queries.

**Actions:** `query_grafana_service_names`, `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence trace

| # | Tool | Result |
|---|------|--------|
| 1 | `query_grafana_logs` | 9 logs, 0 error logs |
| 2 | `query_grafana_alert_rules` | 0 alert rules |
| 3 | `query_grafana_metrics` | 20 metrics |
| 4 | `query_grafana_traces` | 0 traces |
| 5 | `query_grafana_service_names` | 0 service names |
| 6 | `get_sre_guidance` | — |

## Validated claims

- DB instance storage ran out, and it entered an incompatible-restore state, causing it to stop accepting connections. [evidence: grafana_logs]
- Free storage space in the DB instance reduced to 2.5 GB and eventually ran out. [evidence: grafana_logs]

## Non-validated claims

- There might have been a spike in database activity due to a large number of `INSERT INTO order_archive` queries. Confirmation of query-based load causing storage issues would require more detailed query execution metrics.
- It is possible that automated volume expansion was not configured or failed to trigger, preventing auto-scaling of storage. Confirmation requires AWS configuration audit logs.

## Diagnosis

- Predicted root cause: Most likely: Resource exhaustion due to storage space reaching its capacity limits, leading to a halt in database writes and resulting in the instance entering an incompatible-restore state.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     storage
- Missing keywords:     FreeStorageSpace

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 5, after metrics were already queried at step 3. The agent queried metrics on instances it had not yet discovered.

### Reviewer notes

_(Add manual observations here.)_
