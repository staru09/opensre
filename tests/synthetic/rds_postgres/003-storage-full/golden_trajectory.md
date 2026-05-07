# Golden trajectory — 003-storage-full

> **Difficulty:** L1 — single-fault with a smoking-gun RDS event
> **Root cause category:** `resource_exhaustion`
> **Required evidence:** `aws_rds_events` (served via `query_grafana_logs`)

## Phases

### Phase 1 — See the storage cliff (must come first)
1. `query_grafana_metrics`

**Why first:** `FreeStorageSpace` collapsing from ~15 GB to ~500 MB over 15 minutes is the headline signal. The same call also returns `WriteIOPS` peaking at 8,100 then collapsing to near-zero (writes blocked by full disk) and the Performance Insights snapshot showing the INSERT archival query as dominant load with `IO:DataFileWrite` waits. Without these metrics there is no way to know *when* storage filled or *why*.

### Phase 2 — Confirm with the RDS event (must come after Phase 1)
2. `query_grafana_logs`

**Why second and required:** This scenario's `required_evidence_sources` lists `aws_rds_events` because the RDS control-plane event at 02:12:33Z — `"DB instance ran out of storage space"` — is the canonical confirmation that storage was the *cause* of the outage, not just a coincident drop. Metrics alone could be confused with disk autoscaling or a snapshot operation; the event makes it definitive.

This phase is sequential, not parallel with metrics, because the metric pattern (cliff in `FreeStorageSpace`, collapse in `WriteIOPS`) is what tells you to *look for* a storage event in the first place. Reading logs without that prior framing burns budget and wastes context window on irrelevant lines.

### Phase 3 — Confirm threshold (any order — single-element parallel block)
- `query_grafana_alert_rules` (parallel)

**Why last:** Alert rules tell you which threshold tripped. By the time you arrive here you already know the cause; this is housekeeping that closes out the model response. Allowed in any order with itself (trivially).

## Forbidden orderings

- **Logs before metrics.** The agent risks finding the storage event and immediately diagnosing without quantifying the duration or tying the cause to the bulk INSERT job. The model response *uses* logs to confirm the metric pattern — reversing the order makes the diagnosis less defensible.
- **Skipping logs entirely.** `aws_rds_events` is in `required_evidence_sources`. A trajectory that produces a correct diagnosis from metrics alone still fails the evidence completeness check.

## Allowed alternative paths

- If `query_grafana_metrics` returns `FreeStorageSpace` already at zero with no historical decline visible, the agent may go directly to `query_grafana_logs` to read the RDS event timeline (this would happen if the investigation window is too narrow). Not expected for scenario 003 as authored.

## Authoring rationale

- **Why metrics first even when logs holds required evidence:** the model_response narrative cites evidence in this order: FreeStorageSpace drop → WriteIOPS collapse → RDS event → PI INSERT. The trajectory mirrors that order. The smoking-gun event in logs is the *confirmation*, not the discovery — the discovery is the metric cliff.
- **Why three serial phases instead of metrics + parallel(logs, alerts):** logs and alert_rules are not interchangeable for this scenario. Logs carries required evidence and adds to the diagnosis; alert_rules is supplementary. Treating them as a parallel pair would let an agent skip logs and still be marked `ordering_ok=True` — wrong outcome.
- **Counterfactual:** Removing Phase 2 makes `aws_rds_events` evidence missing — strict failure. Removing Phase 1 leaves the agent guessing why storage filled. Removing Phase 3 still allows correct diagnosis but the model response is less complete.

## Cross-check vs `test_run_002` actual

`test_run_002/003-storage-full.md` shows `metrics → logs → alert_rules → traces → guidance → service_names`. First three match this golden in both order and required composition. The agent passed strictly *and* would pass under the new ordered scorer. The trailing three calls are still redundant and would drop the efficiency score below 1.0.
