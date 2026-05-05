# Trajectory Audit — run_003

**Captured:** 2026-05-05
**Scope:** All 15 RDS scenarios (000–014)
**LLM provider:** OpenAI (`gpt-4o` reasoning, `gpt-4.1-mini-2025-04-14` toolcall)
**Backend:** `FixtureGrafanaBackend` (`--mock-grafana`)

---

## Pass/fail snapshot

| Scenario | Difficulty | Failure mode | Result | Failure reason |
|----------|-----------|--------------|--------|----------------|
| 000-healthy | 1 | healthy | PASS | — |
| 001-replication-lag | 1 | replication_lag | PASS | — |
| 002-connection-exhaustion | 1 | connection_exhaustion | **FAIL** | missing keyword: `client sessions` |
| 003-storage-full | 1 | storage_full | **FAIL** | missing keyword: `FreeStorageSpace` |
| 004-cpu-saturation-bad-query | 1 | cpu_saturation | PASS | — |
| 005-failover | 1 | failover | PASS | — |
| 006-replication-lag-cpu-redherring | 2 | replication_lag | **FAIL** | missing keyword: `causally independent` |
| 007-connection-pressure-noisy-healthy | 2 | healthy | PASS | — |
| 008-storage-full-missing-metric | 3 | storage_full | PASS | — |
| 009-dual-fault-connection-cpu | 4 | connection_exhaustion | PASS | — |
| 010-replication-lag-missing-metric | 3 | replication_lag | PASS | — |
| 011-cpu-storage-compositional | 3 | cpu_saturation | PASS | — |
| 012-replication-lag-misleading-events | 3 | replication_lag | **FAIL** | wrong category: got `infrastructure`, expected `resource_exhaustion` |
| 013-storage-recovery-false-alert | 3 | healthy | **FAIL** | wrong category: got `resource_exhaustion`, expected `healthy` |
| 014-checkpoint-storm-cpu-saturation | 3 | cpu_saturation | PASS | — |

**Aggregate: 10/15 passed (67%)**

---

## Two distinct failure modes

### 1. Keyword fragility (002, 003, 006)

The agent's category is correct and its reasoning is sound, but it fails because it doesn't use the exact required keyword phrase. Examples:

- **002**: Says "469 out of 500 connections" and "connection exhaustion" — doesn't write "client sessions"
- **003**: Correctly diagnoses storage exhaustion — doesn't use the metric name "FreeStorageSpace"
- **006**: Explicitly says "CPU is not causally linked to the replication lag" — doesn't say "causally independent"

These are scorer failures, not agent reasoning failures. The fix is an LLM-judge rubric that grades meaning rather than string matching.

### 2. Category misclassification (012, 013) — genuine reasoning errors

**012-replication-lag-misleading-events**: The fixture contains failover events in `grafana_error_logs`. The agent fixated on these — "failover initiated, failover in progress, failover completed" — and concluded `infrastructure` (Multi-AZ failover). The actual root cause is `resource_exhaustion` from write-heavy WAL generation causing replication lag. The failover events are a red herring; the agent was misled by the most salient signal in the logs.

**013-storage-recovery-false-alert**: The fixture shows storage dropped below threshold, then autoscaling resolved it. The agent correctly identified both facts but categorized the outcome as `resource_exhaustion`. The expected answer is `healthy` — the alert was real but the system self-healed, so the current state is normal. The agent cannot reason that "resolved past incident = current state healthy".

---

## Universal ordering pattern

**All 15 scenarios** show `query_grafana_service_names` called at step 5 or 6, after metrics and logs have already been queried. Looking at the per-loop rationale, this is not a planning choice — it's a controller fallback. In most Loop 5 entries the rationale reads:

> *"Since querying logs, metrics, traces, and alert rules is blocked or exhausted, querying available service names helps identify correct labels..."*

Or explicitly:

> *"Controller fallback: planner selected only unavailable or already-executed actions. Forcing next available action."*

Service enumeration is treated as a last resort rather than a first step. The agent never deliberately chooses to enumerate services before querying their metrics — it only lands there when everything else is exhausted. This is the systematic ordering bug identified in the original `Screenshot 2026-05-05 120015.png` observation, now confirmed across all 15 scenarios.

---

## Key findings for Phase 2B

1. **The scorer needs an LLM-judge layer.** 3 of 5 failures are phrasing failures, not reasoning failures. Keyword matching is grading the wrong thing.

2. **The agent cannot reason about resolved states.** Scenario 013 demonstrates the agent has no concept of "the alert fired but is no longer active". It sees evidence of a past problem and calls it the current root cause. This is a gap in the diagnosis prompt.

3. **The agent is misled by salient log events.** Scenario 012 shows the agent anchoring on the most prominent entries in the log (failover events) rather than reading them as context and identifying the underlying cause (WAL backlog). This is the confounder-reasoning failure the L2+ scenarios are designed to expose.

4. **Service enumeration ordering is a prompt-level fix.** The rationale text makes clear the LLM understands that service names discovery is a prerequisite for targeted queries — it just never acts on this understanding proactively. A single instruction in the system prompt to enumerate services before querying metrics should close this.
