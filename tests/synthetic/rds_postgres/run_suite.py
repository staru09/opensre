from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.pipeline.runners import run_investigation
from tests.synthetic.mock_grafana_backend.backend import FixtureGrafanaBackend
from tests.synthetic.rds_postgres.scenario_loader import (
    SUITE_DIR,
    ScenarioFixture,
    load_all_scenarios,
)

# Maps fixture schema evidence keys to the agent's internal state keys.
_EVIDENCE_KEY_MAP: dict[str, str] = {
    "aws_cloudwatch_metrics": "grafana_metrics",
    "aws_rds_events": "grafana_logs",
    "aws_performance_insights": "grafana_metrics",
}


@dataclass(frozen=True)
class TrajectoryScore:
    actual_sequence: list[str]  # flattened actions from executed_hypotheses
    expected_sequence: list[str]  # from answer_key.optimal_trajectory
    loops_used: int
    max_loops: int
    sequencing_ok: bool  # all expected actions appear in actual (set membership)
    calibration_ok: bool  # loops_used <= max_loops
    efficiency_score: float  # mean(sequencing_ok, calibration_ok)


@dataclass(frozen=True)
class ReasoningScore:
    """Axis 2 adversarial reasoning quality score.

    ruling_out_ok: every ruling_out_keywords token was found in agent output.
    queries_ok: every required_queries metric name was requested via query_timeseries.
    reasoning_score: mean(ruling_out_ok, queries_ok); 1.0 = full pass.
    """

    ruling_out_ok: bool
    queries_ok: bool
    missing_ruling_out: list[str]
    missing_queries: list[str]
    reasoning_score: float


@dataclass(frozen=True)
class ScenarioScore:
    scenario_id: str
    passed: bool
    root_cause_present: bool
    expected_category: str
    actual_category: str
    missing_keywords: list[str]
    matched_keywords: list[str]
    root_cause: str
    failure_reason: str = ""
    trajectory: TrajectoryScore | None = None
    reasoning: ReasoningScore | None = None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the synthetic RDS PostgreSQL RCA suite.")
    parser.add_argument(
        "--scenario",
        default="",
        help="Run a single scenario directory name, e.g. 001-replication-lag.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON results.",
    )
    parser.add_argument(
        "--mock-grafana",
        action="store_true",
        dest="mock_grafana",
        help="Serve fixture data via FixtureGrafanaBackend instead of real Grafana calls.",
    )
    parser.add_argument(
        "--axis2",
        action="store_true",
        help="Print Axis 1 vs Axis 2 gap report (requires results from both suites).",
    )
    parser.add_argument(
        "--capture-trajectory",
        dest="capture_trajectory",
        default="",
        metavar="OUTPUT_DIR",
        help=(
            "Write a per-scenario trajectory audit markdown file to OUTPUT_DIR. "
            "Captures alert, plan, ordered tool calls, evidence, validated claims, "
            "and final diagnosis for trajectory anomaly analysis."
        ),
    )
    return parser.parse_args(argv)


def _build_resolved_integrations(
    fixture: ScenarioFixture,
    use_mock_grafana: bool,
    grafana_backend: Any = None,
) -> dict[str, Any] | None:
    """Build pre-resolved integrations to inject into run_investigation.

    Accepts an optional pre-built grafana_backend (e.g. SelectiveGrafanaBackend)
    so callers can instrument the backend before injection.  Falls back to a fresh
    FixtureGrafanaBackend when use_mock_grafana=True and no backend is provided.
    """
    if not use_mock_grafana and grafana_backend is None:
        return None
    backend = grafana_backend or FixtureGrafanaBackend(fixture)
    return {
        "grafana": {
            "endpoint": "",
            "api_key": "",
            "_backend": backend,
        }
    }


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def _normalize_query_token(value: str) -> str:
    return _normalize_text(value).replace(" ", "_").replace("-", "_")


def _matches_required_keyword(normalized_output: str, keyword: str) -> bool:
    normalized_keyword = _normalize_text(keyword)
    if normalized_keyword in normalized_output:
        return True

    keyword_aliases = {
        "max_connections": (
            "maximum allowed connections",
            "max allowed connections",
            "allowed connections",
            "connection slots",
        ),
        "performanceinsights": (
            "top sql activity",
            "avg load",
            "aas",
            "active sessions",
            "db load",
        ),
        "client sessions": (
            "client session",
            "idle database sessions",
            "database sessions",
        ),
        "idle": (
            "clientread",
            "waiting for client response",
            "sessions remain open",
            "open sessions",
        ),
    }
    for alias in keyword_aliases.get(normalized_keyword.replace(" ", ""), ()):
        if _normalize_text(alias) in normalized_output:
            return True

    keyword_tokens = set(re.findall(r"[a-z0-9]+", normalized_keyword))
    if not keyword_tokens:
        return False

    output_tokens = set(re.findall(r"[a-z0-9]+", normalized_output))
    return keyword_tokens.issubset(output_tokens)


def _scored_output_text(final_state: dict[str, Any]) -> str:
    """Return the broadest textual output we should grade for synthetic scenarios."""
    return " ".join(
        [
            str(final_state.get("root_cause") or ""),
            " ".join(claim.get("claim", "") for claim in final_state.get("validated_claims", [])),
            " ".join(
                claim.get("claim", "") for claim in final_state.get("non_validated_claims", [])
            ),
            " ".join(final_state.get("causal_chain", [])),
            str(final_state.get("report") or ""),
            str((final_state.get("problem_report") or {}).get("report_md") or ""),
        ]
    )


def score_trajectory(
    fixture: ScenarioFixture,
    final_state: dict[str, Any],
) -> TrajectoryScore | None:
    """Score the agent's investigation trajectory against the expected sequence.

    Returns None when no optimal_trajectory is declared for the scenario.
    """
    expected = list(fixture.answer_key.optimal_trajectory)
    if not expected:
        return None

    max_loops = fixture.answer_key.max_investigation_loops

    # Flatten all actions across every investigation loop (order preserved)
    executed_hypotheses: list[dict[str, Any]] = final_state.get("executed_hypotheses") or []
    actual_sequence: list[str] = []
    for hyp in executed_hypotheses:
        for action in hyp.get("actions", []):
            actual_sequence.append(action)

    loops_used: int = int(final_state.get("investigation_loop_count") or len(executed_hypotheses))

    # Sequencing: all expected actions must appear in the actual sequence.
    # Actions run in parallel so completion order is non-deterministic; we check
    # coverage (set membership) rather than position.  When a real LLM is used,
    # it may skip actions entirely — that will surface as sequencing_ok=False.
    sequencing_ok = set(expected) <= set(actual_sequence)

    calibration_ok = loops_used <= max_loops
    efficiency_score = (int(sequencing_ok) + int(calibration_ok)) / 2.0

    return TrajectoryScore(
        actual_sequence=actual_sequence,
        expected_sequence=expected,
        loops_used=loops_used,
        max_loops=max_loops,
        sequencing_ok=sequencing_ok,
        calibration_ok=calibration_ok,
        efficiency_score=efficiency_score,
    )


def score_reasoning(
    fixture: ScenarioFixture,
    final_state: dict[str, Any],
    queried_metrics: list[str] | None = None,
) -> ReasoningScore | None:
    """Score Axis 2 adversarial reasoning quality.

    Returns None when neither ruling_out_keywords nor required_queries are
    declared for the scenario.

    Args:
        fixture: The scenario fixture containing the answer key.
        final_state: The agent's final investigation state dict.
        queried_metrics: List of metric_name values the agent requested via
            query_timeseries (from SelectiveGrafanaBackend.queried_metrics).
            Pass None or [] when the backend does not record queries (Axis 1).
    """
    has_ruling_out = bool(fixture.answer_key.ruling_out_keywords)
    has_required_queries = bool(fixture.answer_key.required_queries)
    if not has_ruling_out and not has_required_queries:
        return None

    # --- ruling_out_keywords: check each token appears anywhere in agent output ---
    evidence_text = _scored_output_text(final_state)
    normalized_output = _normalize_text(evidence_text)

    missing_ruling_out: list[str] = []
    if has_ruling_out:
        for token in fixture.answer_key.ruling_out_keywords:
            if not _matches_required_keyword(normalized_output, token):
                missing_ruling_out.append(token)

    # --- required_queries: each token must appear in at least one queried metric name ---
    missing_queries: list[str] = []
    if has_required_queries:
        audited = {_normalize_query_token(item) for item in (queried_metrics or [])}
        for required in fixture.answer_key.required_queries:
            token = _normalize_query_token(required)
            if not any(token in q for q in audited):
                missing_queries.append(required)

    ruling_out_ok = not missing_ruling_out
    queries_ok = not missing_queries
    reasoning_score = (int(ruling_out_ok) + int(queries_ok)) / 2.0

    return ReasoningScore(
        ruling_out_ok=ruling_out_ok,
        queries_ok=queries_ok,
        missing_ruling_out=missing_ruling_out,
        missing_queries=missing_queries,
        reasoning_score=reasoning_score,
    )


def score_result(
    fixture: ScenarioFixture,
    final_state: dict[str, Any],
    queried_metrics: list[str] | None = None,
) -> ScenarioScore:
    root_cause = str(final_state.get("root_cause") or "").strip()
    actual_category = str(final_state.get("root_cause_category") or "unknown").strip()
    root_cause_present = bool(root_cause and root_cause.lower() != "unable to determine root cause")

    evidence_text = _scored_output_text(final_state)
    normalized_output = _normalize_text(evidence_text)

    matched_keywords = [
        keyword
        for keyword in fixture.answer_key.required_keywords
        if _matches_required_keyword(normalized_output, keyword)
    ]
    missing_keywords = [
        keyword
        for keyword in fixture.answer_key.required_keywords
        if keyword not in matched_keywords
    ]

    answer_key = fixture.answer_key
    failure_reason = ""

    # 1. Category match
    if not root_cause_present:
        failure_reason = "no root cause in output"
    elif actual_category != answer_key.root_cause_category:
        failure_reason = (
            f"wrong category: got {actual_category!r}, expected {answer_key.root_cause_category!r}"
        )
    elif missing_keywords:
        failure_reason = f"missing required keywords: {missing_keywords}"
    # 2. Forbidden category check (level 2+ adversarial)
    elif answer_key.forbidden_categories and actual_category in answer_key.forbidden_categories:
        failure_reason = f"forbidden category in output: {actual_category!r}"
    # 3. Forbidden keyword check — none of these may appear in evidence_text
    elif answer_key.forbidden_keywords:
        forbidden_hits = [
            kw for kw in answer_key.forbidden_keywords if _normalize_text(kw) in normalized_output
        ]
        if forbidden_hits:
            failure_reason = f"forbidden keywords in output: {forbidden_hits}"
    # 4. Evidence path check — required sources must be non-empty in final_state["evidence"].
    # Fixture schema keys (aws_cloudwatch_metrics, aws_rds_events, aws_performance_insights) map to the agent's
    # internal evidence keys (grafana_metrics, grafana_logs) set by _map_grafana_*.
    if not failure_reason and answer_key.required_evidence_sources:
        evidence = final_state.get("evidence") or {}
        performance_insights_tokens = (
            "top sql activity",
            "avg load",
            "aas",
            "db load",
            "walwrite",
        )

        for source_key in answer_key.required_evidence_sources:
            if source_key == "aws_performance_insights":
                state_key = _EVIDENCE_KEY_MAP.get(source_key, source_key)

                has_state_evidence = bool(evidence.get(state_key))
                has_pi_signal = any(
                    token in normalized_output for token in performance_insights_tokens
                )

                if not (has_state_evidence and has_pi_signal):
                    failure_reason = f"required evidence not gathered: {source_key!r}"
                    break

                continue

            state_key = _EVIDENCE_KEY_MAP.get(source_key, source_key)
            if not evidence.get(state_key):
                failure_reason = f"required evidence not gathered: {source_key!r}"
                break

    # 5. Primary evidence + explicit sequence check — only for scenarios that
    # explicitly require the failover event timeline wording.
    failover_required_tokens = {
        "primary evidence source",
        "failover initiated",
        "failover in progress",
        "failover completed",
        "instance available",
    }
    normalized_required_keywords = {
        _normalize_text(keyword) for keyword in answer_key.required_keywords
    }
    requires_failover_event_reasoning = failover_required_tokens.issubset(
        normalized_required_keywords
    )

    if not failure_reason and requires_failover_event_reasoning:
        root_cause_text = _normalize_text(root_cause)
        validated_text = _normalize_text(
            " ".join(claim.get("claim", "") for claim in final_state.get("validated_claims", []))
        )
        causal_chain_text = _normalize_text(" ".join(final_state.get("causal_chain", [])))

        reasoning_text = " ".join([root_cause_text, validated_text, causal_chain_text])

        mentions_event_reasoning = (
            "rds" in reasoning_text
            and ("event" in reasoning_text or "timeline" in reasoning_text)
            and "primary evidence source" in reasoning_text
        )

        if not mentions_event_reasoning:
            failure_reason = "RDS events gathered but not used as primary reasoning signal"

        required_sequence_tokens = (
            "failover initiated",
            "failover in progress",
            "failover completed",
            "instance available",
        )

        sequence_present = all(token in reasoning_text for token in required_sequence_tokens)

        if not failure_reason and not sequence_present:
            failure_reason = "RDS event sequence not explicitly listed in required form"

    passed = not failure_reason
    trajectory = score_trajectory(fixture, final_state)
    reasoning = score_reasoning(fixture, final_state, queried_metrics)
    return ScenarioScore(
        scenario_id=fixture.scenario_id,
        passed=passed,
        root_cause_present=root_cause_present,
        expected_category=fixture.answer_key.root_cause_category,
        actual_category=actual_category,
        missing_keywords=missing_keywords,
        matched_keywords=matched_keywords,
        root_cause=root_cause,
        failure_reason=failure_reason,
        trajectory=trajectory,
        reasoning=reasoning,
    )


def run_scenario(
    fixture: ScenarioFixture,
    use_mock_grafana: bool = False,
    grafana_backend: Any = None,
) -> tuple[dict[str, Any], ScenarioScore]:
    alert = fixture.alert
    labels = alert.get("commonLabels", {}) or {}

    alert_name = str(alert.get("title") or labels.get("alertname") or fixture.scenario_id)
    pipeline_name = str(labels.get("pipeline_name") or "rds-postgres-synthetic")
    severity = str(labels.get("severity") or "critical")

    resolved_integrations = _build_resolved_integrations(
        fixture, use_mock_grafana, grafana_backend=grafana_backend
    )

    final_state = run_investigation(
        alert_name=alert_name,
        pipeline_name=pipeline_name,
        severity=severity,
        raw_alert=alert,
        resolved_integrations=resolved_integrations,
    )
    state_dict = dict(final_state)

    # Extract query audit log from SelectiveGrafanaBackend if one was injected.
    queried_metrics: list[str] | None = None
    if grafana_backend is not None and hasattr(grafana_backend, "queried_metrics"):
        queried_metrics = list(grafana_backend.queried_metrics)

    return state_dict, score_result(fixture, state_dict, queried_metrics=queried_metrics)


_TOOL_EVIDENCE_SUMMARY: dict[str, tuple[str, ...]] = {
    "query_grafana_logs": ("grafana_logs", "grafana_error_logs"),
    "query_grafana_metrics": ("grafana_metrics",),
    "query_grafana_traces": ("grafana_traces",),
    "query_grafana_alert_rules": ("grafana_alert_rules",),
    "query_grafana_service_names": ("grafana_service_names",),
}


def _evidence_result_summary(tool: str, evidence: dict[str, Any]) -> str:
    """One-line result summary for a tool call, derived from the evidence dict."""
    keys = _TOOL_EVIDENCE_SUMMARY.get(tool)
    if not keys:
        return "—"
    parts: list[str] = []
    for key in keys:
        val = evidence.get(key)
        try:
            n = len(val) if val and hasattr(val, "__len__") else 0
        except TypeError:
            n = 0
        label = key.replace("grafana_", "").replace("_", " ")
        parts.append(f"{n} {label}")
    return ", ".join(parts) if parts else "—"


def _format_trajectory_markdown(
    fixture: ScenarioFixture,
    final_state: dict[str, Any],
    score: ScenarioScore,
    queried_metrics: list[str] | None,
) -> str:
    """Render a verbose, human-readable trajectory audit document.

    Sections: Statistics, Alert, Expected vs Actual trajectory, Per-loop tool
    calls, Evidence trace, Validated claims, Causal chain, Diagnosis, Observations.
    Designed for manual review during Phase 2A trajectory analysis.
    """
    lines: list[str] = []
    answer_key = fixture.answer_key
    metadata = fixture.metadata

    expected = list(answer_key.optimal_trajectory)
    executed_hypotheses: list[dict[str, Any]] = final_state.get("executed_hypotheses") or []
    actual_sequence: list[str] = []
    failed_sequence: list[str] = []
    for hyp in executed_hypotheses:
        for action in hyp.get("actions", []):
            actual_sequence.append(action)
        for fa in hyp.get("failed_actions", []):
            name = fa.get("action", str(fa)) if isinstance(fa, dict) else str(fa)
            failed_sequence.append(name)

    loops_used = int(final_state.get("investigation_loop_count") or len(executed_hypotheses))

    lines.append(f"# Trajectory audit — {fixture.scenario_id}")
    lines.append("")
    lines.append(f"- Captured: {datetime.now(UTC).isoformat(timespec='seconds')}")
    lines.append(f"- Scenario difficulty: {getattr(metadata, 'scenario_difficulty', '?')}")
    lines.append(f"- Failure mode: {getattr(metadata, 'failure_mode', '?')}")
    lines.append(f"- Status: {'PASS' if score.passed else 'FAIL'}")
    if score.failure_reason:
        lines.append(f"- Failure reason: `{score.failure_reason}`")
    lines.append("")

    total_calls = len(actual_sequence) + len(failed_sequence)
    unique_tools = list(dict.fromkeys(actual_sequence))  # ordered, deduplicated
    sequence_str = " → ".join(f"`{a}`" for a in actual_sequence)
    lines.append("## Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(
        f"| Tool calls | {total_calls} total ({len(actual_sequence)} successful, {len(failed_sequence)} failed) |"
    )
    lines.append(f"| Loops used | {loops_used} / {answer_key.max_investigation_loops} max |")
    lines.append(f"| Unique tools | {len(unique_tools)} |")
    lines.append("")
    lines.append(f"**Sequence:** {sequence_str}")
    lines.append("")

    alert = fixture.alert or {}
    labels = (alert.get("commonLabels") or {}) if isinstance(alert, dict) else {}
    lines.append("## Alert")
    lines.append("")
    lines.append(f"- Title: {alert.get('title') or labels.get('alertname') or fixture.scenario_id}")
    lines.append(f"- Severity: {labels.get('severity') or 'unknown'}")
    if alert.get("annotations"):
        ann = alert["annotations"]
        if isinstance(ann, dict):
            for k, v in ann.items():
                lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## Trajectory")
    lines.append("")
    lines.append("### Expected (from `answer.yml:optimal_trajectory`)")
    lines.append("")
    if expected:
        for i, action in enumerate(expected, 1):
            lines.append(f"{i}. `{action}`")
    else:
        lines.append("_No optimal_trajectory declared._")
    lines.append("")

    lines.append("### Actual (flattened across investigation loops)")
    lines.append("")
    if actual_sequence:
        for i, action in enumerate(actual_sequence, 1):
            marker = " ✓" if action in expected else ""
            lines.append(f"{i}. `{action}`{marker}")
    else:
        lines.append("_No actions recorded._")
    lines.append("")

    if executed_hypotheses:
        lines.append("### Per investigation loop")
        lines.append("")
        for idx, hyp in enumerate(executed_hypotheses, 1):
            lines.append(f"#### Loop {idx}")
            rationale = hyp.get("rationale") or ""
            if rationale:
                lines.append("")
                lines.append(f"**Planning rationale:** {rationale}")
            actions = hyp.get("actions") or []
            if actions:
                lines.append("")
                lines.append(f"**Actions:** {', '.join(f'`{a}`' for a in actions)}")
            failed = hyp.get("failed_actions") or []
            if failed:
                failed_names = [
                    f.get("action", str(f)) if isinstance(f, dict) else str(f) for f in failed
                ]
                lines.append(f"**Failed:** {', '.join(f'`{a}`' for a in failed_names)}")
            lines.append("")

    if score.trajectory is not None:
        traj = score.trajectory
        lines.append("### Trajectory score (set-membership — ordering NOT enforced)")
        lines.append("")
        lines.append(f"- sequencing_ok: {traj.sequencing_ok}")
        lines.append(
            f"- calibration_ok: {traj.calibration_ok}  ({traj.loops_used}/{traj.max_loops} loops)"
        )
        lines.append(f"- efficiency_score: {traj.efficiency_score}")
        lines.append("")

    evidence = final_state.get("evidence") or {}
    lines.append("## Evidence trace")
    lines.append("")
    lines.append("| # | Tool | Result |")
    lines.append("|---|------|--------|")
    for i, action in enumerate(actual_sequence, 1):
        result = _evidence_result_summary(action, evidence)
        lines.append(f"| {i} | `{action}` | {result} |")
    if failed_sequence:
        for action in failed_sequence:
            lines.append(f"| — | `{action}` _(failed)_ | — |")
    if not actual_sequence and not failed_sequence:
        lines.append("| — | _No actions recorded_ | — |")
    lines.append("")

    if queried_metrics:
        lines.append("### Queried metric names (Selective backend)")
        lines.append("")
        for m in queried_metrics:
            lines.append(f"- `{m}`")
        lines.append("")

    validated = final_state.get("validated_claims") or []
    if validated:
        lines.append("## Validated claims")
        lines.append("")
        for vc in validated:
            claim = vc.get("claim", "")
            ev = vc.get("evidence", "")
            ev_str = f" _(evidence: {ev})_" if ev else ""
            lines.append(f"- {claim}{ev_str}")
        lines.append("")

    non_validated = final_state.get("non_validated_claims") or []
    if non_validated:
        lines.append("## Non-validated claims")
        lines.append("")
        for nv in non_validated:
            claim = nv.get("claim", "") if isinstance(nv, dict) else str(nv)
            lines.append(f"- {claim}")
        lines.append("")

    causal = final_state.get("causal_chain") or []
    if causal:
        lines.append("## Causal chain")
        lines.append("")
        for i, step in enumerate(causal, 1):
            lines.append(f"{i}. {step}")
        lines.append("")

    lines.append("## Diagnosis")
    lines.append("")
    lines.append(f"- Predicted root cause: {final_state.get('root_cause') or '_(empty)_'}")
    lines.append(f"- Predicted category:   `{score.actual_category}`")
    lines.append(f"- Expected category:    `{score.expected_category}`")
    if score.matched_keywords:
        lines.append(f"- Matched keywords:     {', '.join(score.matched_keywords)}")
    if score.missing_keywords:
        lines.append(f"- Missing keywords:     {', '.join(score.missing_keywords)}")
    lines.append("")

    lines.append("## Observations")
    lines.append("")

    observations: list[str] = []

    services_actions = [
        a
        for a in actual_sequence
        if "service" in a.lower()
        and ("query" in a.lower() or "list" in a.lower() or "enumerate" in a.lower())
    ]
    metrics_actions = [
        a for a in actual_sequence if "metric" in a.lower() and "service" not in a.lower()
    ]
    if services_actions and metrics_actions:
        first_service_idx = next(i for i, a in enumerate(actual_sequence) if a in services_actions)
        first_metric_idx = next(i for i, a in enumerate(actual_sequence) if a in metrics_actions)
        if first_service_idx > first_metric_idx:
            observations.append(
                f"Service enumeration (`{services_actions[0]}`) happened at step {first_service_idx + 1}, "
                f"after metrics were already queried at step {first_metric_idx + 1}. "
                "The agent queried metrics on instances it had not yet discovered."
            )

    if score.passed and not causal:
        observations.append(
            "The agent reached the correct diagnosis category but recorded no causal chain steps. "
            "The conclusion appears to be based on pattern-matching rather than traced reasoning."
        )

    if not observations:
        lines.append(
            "_No issues auto-detected. Reviewer: read the per-loop rationale above and add notes below._"
        )
    else:
        for obs in observations:
            lines.append(f"- {obs}")
    lines.append("")
    lines.append("### Reviewer notes")
    lines.append("")
    lines.append("_(Add manual observations here.)_")
    lines.append("")

    return "\n".join(lines)


def _write_trajectory_audit(
    output_dir: Path,
    fixture: ScenarioFixture,
    final_state: dict[str, Any],
    score: ScenarioScore,
    queried_metrics: list[str] | None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{fixture.scenario_id}.md"
    body = _format_trajectory_markdown(fixture, final_state, score, queried_metrics)
    target.write_text(body, encoding="utf-8")
    return target


def _print_gap_report(
    axis1_results: list[ScenarioScore],
    axis2_results: list[ScenarioScore],
    all_fixtures: list[ScenarioFixture],
) -> None:
    """Print Axis 1 vs Axis 2 pass-rate gap, overall and per difficulty level."""
    difficulty_map = {f.scenario_id: f.metadata.scenario_difficulty for f in all_fixtures}

    def _pass_rate(results: list[ScenarioScore]) -> float:
        return sum(1 for r in results if r.passed) / len(results) * 100 if results else 0.0

    ax1_pct = _pass_rate(axis1_results)
    ax2_pct = _pass_rate(axis2_results)
    gap = ax1_pct - ax2_pct

    print("\n=== Axis 1 vs Axis 2 Gap Report ===")
    print(
        f"  Axis 1 (all scenarios, full data):  {ax1_pct:.0f}%  ({sum(r.passed for r in axis1_results)}/{len(axis1_results)})"
    )
    print(
        f"  Axis 2 (adversarial, selective):    {ax2_pct:.0f}%  ({sum(r.passed for r in axis2_results)}/{len(axis2_results)})"
    )
    print(f"  Gap:                                {gap:+.0f}pp")

    print("\n  Per difficulty level:")
    for level in sorted(
        {difficulty_map.get(r.scenario_id, 0) for r in axis1_results + axis2_results}
    ):
        ax1_level = [r for r in axis1_results if difficulty_map.get(r.scenario_id, 0) == level]
        ax2_level = [r for r in axis2_results if difficulty_map.get(r.scenario_id, 0) == level]
        ax1_pct_l = _pass_rate(ax1_level)
        ax2_pct_l = _pass_rate(ax2_level)
        gap_l = ax1_pct_l - ax2_pct_l
        print(
            f"    Difficulty {level}: Axis1={ax1_pct_l:.0f}% ({len(ax1_level)} scenarios)  "
            f"Axis2={ax2_pct_l:.0f}% ({len(ax2_level)} scenarios)  gap={gap_l:+.0f}pp"
        )


def run_suite(argv: list[str] | None = None) -> list[ScenarioScore]:
    args = parse_args(argv)
    fixtures = load_all_scenarios(SUITE_DIR)
    if args.scenario:
        fixtures = [fixture for fixture in fixtures if fixture.scenario_id == args.scenario]
        if not fixtures:
            raise SystemExit(f"Unknown scenario: {args.scenario}")

    capture_dir: Path | None = Path(args.capture_trajectory) if args.capture_trajectory else None

    results: list[ScenarioScore] = []
    for fixture in fixtures:
        final_state, score = run_scenario(fixture, use_mock_grafana=args.mock_grafana)
        results.append(score)
        if capture_dir is not None:
            target = _write_trajectory_audit(
                capture_dir, fixture, final_state, score, queried_metrics=None
            )
            if not args.json:
                print(f"  trajectory audit -> {target}")

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            detail = (
                f"reason={result.failure_reason!r}"
                if result.failure_reason
                else f"category={result.actual_category}"
            )
            print(f"{status} {result.scenario_id} {detail}")

        passed_count = sum(1 for result in results if result.passed)
        print(f"\nResults: {passed_count}/{len(results)} passed")

    return results


def main(argv: list[str] | None = None) -> int:
    results = run_suite(argv)
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
