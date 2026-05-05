# Trajectory audit — 008-storage-full-missing-metric

- Captured: 2026-05-05T15:19:11+00:00
- Scenario difficulty: 3
- Failure mode: storage_full
- Status: PASS

## Alert

- Title: [synthetic-rds] Write Latency Critical On billing-prod
- Severity: critical

## Trajectory

### Expected (from `answer.yml:optimal_trajectory`)

1. `query_grafana_logs`
2. `query_grafana_metrics`
3. `query_grafana_alert_rules`

### Actual (flattened across investigation loops)

1. `query_grafana_metrics` ✓
2. `query_grafana_logs` ✓
3. `query_grafana_alert_rules` ✓
4. `query_grafana_traces`
5. `get_sre_guidance`

### Per investigation loop

#### Loop 1

**Planning rationale:** The alert signals critical write latency on the billing-prod RDS instance. Key hypotheses include: (1) high load causing slow or expensive writes, (2) blocking or long-running queries causing contention, (3) background processes such as autovacuum or WAL causing latency spikes, or (4) many idle or long-lived connections affecting performance. Querying Grafana metrics specific to this service and instance can provide immediate insights into write latency patterns, throughput, CPU, connection counts, and any correlated resource usage spikes. This single source of quantitative performance data can discriminate among query load, blocking, and resource contention causes efficiently, guiding or potentially obviating the need for heavier log/tracing analysis.

**Actions:** `query_grafana_metrics`

#### Loop 2

**Planning rationale:** Prioritize querying Grafana Loki logs for the 'rds-postgres-synthetic' service on the 'billing-prod' instance to identify slow or blocking queries, connection issues (idle or excessive), or other error patterns that can explain high write latency. This directly targets the most plausible root causes: slow queries versus connection problems, without chasing configuration or trace data that are less immediately discriminative.

**Actions:** `query_grafana_logs`

#### Loop 3

**Planning rationale:** To investigate critical write latency on RDS instance billing-prod, plausible root causes include: (1) slow or blocking queries causing write delays, (2) high resource contention (CPU, IO), (3) misconfigured or excessively sensitive alert thresholds. Since logs and metrics queries were exhausted, querying Grafana alert rules will clarify exactly what metric and threshold triggered the alert, helping us evaluate if the alert is aligned with genuine latency issues or possibly secondary symptoms or noise. This action can also reveal if the alert monitors specific query patterns, connection counts, or resource usage, thus directly discriminating among competing root causes without redundant data fetches.

**Actions:** `query_grafana_alert_rules`

#### Loop 4

**Planning rationale:** The critical write latency alert on the 'billing-prod' RDS instance could be due to slow or blocking queries, connection saturation (idle or long-lived connections), or background resource-consuming processes. Querying Grafana Tempo traces for the 'rds-postgres-synthetic' service will help identify slow query spans or bottlenecks during the write operations, thus discriminating between slow queries, transaction contention, or other pipeline-related performance issues. This single action targets evidence that can directly confirm or rule out slow/expensive queries as the root cause, which is essential to improve diagnosis quality and focus next steps effectively.

**Actions:** `query_grafana_traces`

#### Loop 5

**Planning rationale:** The alert reports critical write latency on the billing-prod RDS instance. Plausible root causes include slow or blocking queries consuming resources, background Postgres processes like vacuum or WAL activities causing I/O pressure, or contention caused by idle connections or audit/logging overhead. Since direct log and trace queries are already blocked, getting SRE best practices for data pipeline incidents focusing on pipeline_types and failure patterns can efficiently guide whether resource contention patterns, slow queries, or background processes are typical root causes and remediation approaches. This helps refine hypotheses and informs next diagnostic actions in a high information-gain way.

**Actions:** `get_sre_guidance`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_metrics`: 19 entries
- `grafana_metric_name`: 19 entries
- `grafana_metrics_service`: 22 entries
- `grafana_logs`: 7 entries
- `grafana_error_logs`: 0 entries
- `grafana_logs_query`: 0 entries
- `grafana_logs_service`: 22 entries
- `grafana_alert_rules`: 0 entries
- `grafana_alert_rules_count`: ? entries
- `grafana_traces`: 0 entries
- `grafana_pipeline_spans`: 0 entries
- `grafana_traces_service`: 22 entries

## Validated claims

- The DB instance storage is critically low with only 0.8 GB free. [evidence: Grafana Logs]
- The DB instance ran out of storage space, causing write operations to be blocked. [evidence: Grafana Logs]
- The database is in an incompatible-restore state due to insufficient storage space. [evidence: Grafana Logs]

## Non-validated claims

- Potentially high volume of data being inserted into the DB led to storage exhaustion. Confirmation requires data on recent database growth trends and operation types.
- An unexpected surge in data writes could have accelerated storage exhaustion. Verification requires historical Write IOPS and transaction logs.

## Diagnosis

- Predicted root cause: The database ran out of storage space, blocking all write operations and resulting in the write latency alert.
- Predicted category:   `resource_exhaustion`
- Expected category:    `resource_exhaustion`
- Matched keywords:     storage, storage space

## Observations

- The agent reached the correct diagnosis category but recorded no causal chain steps. The conclusion appears to be based on pattern-matching rather than traced reasoning.

### Reviewer notes

_(Add manual observations here.)_
