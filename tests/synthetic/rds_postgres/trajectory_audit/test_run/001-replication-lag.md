# Trajectory audit — 001-replication-lag

- Captured: 2026-05-06T06:20:34+00:00
- Scenario difficulty: 1
- Failure mode: replication_lag
- Status: PASS

## Statistics

| Metric | Value |
|--------|-------|
| Tool calls | 6 total (6 successful, 0 failed) |
| Loops used | 4 / 4 max |
| Unique tools | 6 |

**Sequence:** `query_grafana_logs` → `query_grafana_alert_rules` → `query_grafana_metrics` → `query_grafana_traces` → `get_sre_guidance` → `query_grafana_service_names`

## Alert

- Title: [synthetic-rds] Replication Lag On payments-prod
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
5. `get_sre_guidance`
6. `query_grafana_service_names`

### Per investigation loop

#### Loop 1

**Planning rationale:** The alert is for replication lag on an RDS Postgres read replica. The key competing hypotheses are: (1) slow or blocking queries on the replica causing lag, (2) excessive idle or long-lived connections, (3) background processes (WAL shipping or vacuum) being blocked, or (4) workload spikes or stalls causing replication lag. Querying logs for the payments-prod database under the rds-postgres-synthetic service will help identify errors, slow queries, blocking events, or stalled replication events that explain the lag. This action offers direct evidence to distinguish between query-related resource issues, connection idling, or replication background process issues. Other actions like alert rules or metrics are less direct and may not expose the exact cause. Starting with logs optimizes information gain and assists next investigative steps.

**Actions:** `query_grafana_logs`

#### Loop 2

**Planning rationale:** Fallback plan: LLM returned invalid structured output.

**Actions:** `query_grafana_alert_rules`, `query_grafana_metrics`, `query_grafana_traces`

#### Loop 3

**Planning rationale:** The primary competing hypotheses for replication lag are: (1) resource bottlenecks such as slow/long-running queries or WAL shipping delays, (2) connection-related issues, including idle or blocking connections causing delays, and (3) background DB activities like autovacuum or logging leading to replication delay. Since direct log and alert query actions are blocked, retrieving SRE best practices focused on replication lag and pipeline failure from available guidance can help discriminate root causes by highlighting common failure patterns and remediation strategies. This action has high information gain potential by informing which subsequent diagnostics or metrics to prioritize and can guide effective next steps to resolve replication lag in the payments-prod RDS PostgreSQL instance.

**Actions:** `get_sre_guidance`

#### Loop 4

**Planning rationale:** Controller fallback: planner selected only unavailable or already-executed actions. Forcing next available action.

**Actions:** `query_grafana_service_names`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence trace

| # | Tool | Result |
|---|------|--------|
| 1 | `query_grafana_logs` | 11 logs, 0 error logs |
| 2 | `query_grafana_alert_rules` | 0 alert rules |
| 3 | `query_grafana_metrics` | 20 metrics |
| 4 | `query_grafana_traces` | 0 traces |
| 5 | `get_sre_guidance` | — |
| 6 | `query_grafana_service_names` | 0 service names |

## Validated claims

- Significant update load on the primary is indicated by "UPDATE orders SET status = 'settled'" with high wait times mostly on IO:WALWrite [evidence: grafana_logs]
- Replica lag exceeded 600 seconds [evidence: grafana_logs]
- High transaction log generation on payments-prod indicating increased write activity [evidence: grafana_metrics]

## Non-validated claims

- The exact nature of write workload that led to the high WAL write rate and subsequent replica lag isn't captured in provided evidence and would require RDS events or detailed transaction logs to confirm.
- The impact of subsequent analytics or secondary query loads on CPU is noted, but not proven as causally linked to the WAL replication lag event.

## Diagnosis

- Predicted root cause: Most likely: resource exhaustion due to a write-heavy workload on primary causing WAL generation that exceeds replica's replay capability. Evidence of this is missing direct confirmation of primary write volume spike or missing lag-specific RDS events outside of the observed spike.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     replication lag, write-heavy workload, replica, wal

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 6, after metrics were already queried at step 3. The agent queried metrics on instances it had not yet discovered.
- The agent reached the correct diagnosis category but recorded no causal chain steps. The conclusion appears to be based on pattern-matching rather than traced reasoning.

### Reviewer notes

_(Add manual observations here.)_
