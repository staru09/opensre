# Trajectory audit — 005-failover

- Captured: 2026-05-05T15:16:08+00:00
- Scenario difficulty: 1
- Failure mode: failover
- Status: PASS

## Alert

- Title: [synthetic-rds] Connection Drop Detected On payments-prod
- Severity: critical

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
5. `get_sre_guidance`
6. `query_grafana_service_names`

### Per investigation loop

#### Loop 1

**Planning rationale:** The alert indicates a sudden drop in connection count to zero, which could be caused by either a network/connectivity issue, a database failover/restart, or a pipeline shutdown/crash. Querying Grafana logs for the rds-postgres-synthetic service around the alert time will reveal any error messages, connection failures, or pipeline crashes that triggered the connection drop. Querying Grafana metrics (e.g., connection counts, error rates, CPU, and throughput) for the same period will help identify if the connection drop coincides with traffic spikes, resource pressure, or DB-side failover events. Together, logs and metrics will discriminate between infrastructure issues, pipeline crashes, or DB failover/restart as root causes, reducing uncertainty with minimal overlap.

**Actions:** `query_grafana_logs`, `query_grafana_metrics`

#### Loop 2

**Planning rationale:** The alert indicates a sudden drop to zero in connection count, which could be caused by multiple scenarios such as a connectivity issue, a database restart, or an alert misconfiguration. Querying the Grafana alert rules for the 'rds-postgres-synthetic' pipeline will clarify the exact alert query and thresholds, helping to confirm if the alert reflects a genuine sudden outage or a monitoring artifact. This action can discriminate between real connection drops due to external issues (like DB restart, network) versus false positives or threshold anomalies, thus efficiently focusing the next investigation steps.

**Actions:** `query_grafana_alert_rules`

#### Loop 3

**Planning rationale:** The alert indicates a sudden drop to zero in connection count on the payments-prod RDS instance, signaling a brief outage window. Plausible hypotheses include a genuine transient loss of connections due to network or infrastructure issues, a database crash or restart event, or an upstream client/service disconnection spike. Querying Grafana traces for the rds-postgres-synthetic service allows us to identify patterns of timeouts, slow or cancelled spans, and any distributed trace errors around the outage window, which can discriminate between a genuine outage, a blocking or resource-related query issue, or synthetic pipeline problems upstream. This single action offers the highest information gain to identify the mechanism underlying the connection drop, ruling out or confirming infrastructure versus application-level causes.

**Actions:** `query_grafana_traces`

#### Loop 4

**Planning rationale:** The alert indicates a critical connection drop resulting in zero connections temporarily on the payments-prod RDS instance. Possible root causes include: a genuine outage or network blip, resource exhaustion causing connections to be dropped, or a systemic pipeline/configuration issue causing synthetic checks to fail. Since detailed logs, metrics, and traces are inaccessible, retrieving SRE best practices for pipeline incidents can help prioritize diagnostic focus and remediation actions. This can also guide on specific failure patterns (e.g., network, resource, dependency failure) that match a sudden connection drop, improving hypothesis discrimination without redundant or unavailable data queries.

**Actions:** `get_sre_guidance`

#### Loop 5

**Planning rationale:** The alert indicates an unexpected drop to zero in connection count on the payments-prod RDS instance, which could be caused by connection pool exhaustion, network or instance-level issues, or an application issue affecting connection usage. Since query_grafana_logs and other pipeline log or alert rule queries are blocked, the next best step is to discover the correct service_name labels in Loki via query_grafana_service_names. This will enable a precise targeted search for relevant logs or metrics next, which can help differentiate if the drop was due to external connectivity problems, client-side issues, or RDS instance-side failures. This action offers highest information gain by allowing refined follow-up targeted log or trace queries to distinguish among connection pool problems, query performance issues, or infrastructure outages.

**Actions:** `query_grafana_service_names`

### Trajectory score (set-membership — ordering NOT enforced)

- sequencing_ok: True
- calibration_ok: True  (4/4 loops)
- efficiency_score: 1.0

## Evidence gathered

- `grafana_logs`: 9 entries
- `grafana_error_logs`: 3 entries
- `grafana_logs_query`: 0 entries
- `grafana_logs_service`: 22 entries
- `grafana_metrics`: 21 entries
- `grafana_metric_name`: 19 entries
- `grafana_metrics_service`: 22 entries
- `grafana_alert_rules`: 0 entries
- `grafana_alert_rules_count`: ? entries
- `grafana_traces`: 0 entries
- `grafana_pipeline_spans`: 0 entries
- `grafana_traces_service`: 22 entries
- `grafana_service_names`: 0 entries

## Validated claims

- failover initiated -> failover in progress -> failover completed -> instance available. [evidence: Grafana Error Logs]
- The system recovered and workload resumed normally. [evidence: Grafana Error Logs]
- The health check failure may have been caused by transient network issues or hardware failure, but specific diagnostics or logs showing the underlying reason for the health check failure were not available.

## Non-validated claims

- The connection drop to zero suggests a brief disruption, yet further details about client-side connection handling during failover could confirm if reconnection logic was robust enough.

## Diagnosis

- Predicted root cause: Based on the RDS event timeline (primary evidence source), the root cause was the failover initiated due to a health check failure on the primary host, resulting in a brief outage window.
- Predicted category:   `infrastructure`
- Expected category:    `infrastructure`
- Matched keywords:     failover, Multi-AZ, health check failure, primary evidence source, workload resumed normally, failover initiated, failover in progress, failover completed, instance available

## Observations

- Service enumeration (`query_grafana_service_names`) happened at step 6, after metrics were already queried at step 2. The agent queried metrics on instances it had not yet discovered.
- The agent reached the correct diagnosis category but recorded no causal chain steps. The conclusion appears to be based on pattern-matching rather than traced reasoning.

### Reviewer notes

_(Add manual observations here.)_
