from __future__ import annotations

from pathlib import Path

from app.analytics import provider


def _clear_hosted_ci_env(monkeypatch) -> None:
    for name in provider._CI_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_base_properties_include_machine_architecture() -> None:
    assert "machine_arch" in provider._BASE_PROPERTIES
    assert provider._BASE_PROPERTIES["machine_arch"] != ""


def test_generic_ci_env_does_not_disable_analytics(monkeypatch) -> None:
    _clear_hosted_ci_env(monkeypatch)
    monkeypatch.setenv("CI", "true")

    assert provider._is_ci_environment() is False
    assert provider._is_opted_out() is False


def test_hosted_ci_environment_disables_analytics(monkeypatch) -> None:
    _clear_hosted_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    assert provider._is_ci_environment() is True
    assert provider._is_opted_out() is True


def test_capture_first_run_if_needed_skips_files_in_ci(
    monkeypatch,
    tmp_path: Path,
) -> None:
    anonymous_id_path = tmp_path / "anonymous_id"
    first_run_path = tmp_path / "installed"

    _clear_hosted_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(provider, "_ANONYMOUS_ID_PATH", anonymous_id_path)
    monkeypatch.setattr(provider, "_FIRST_RUN_PATH", first_run_path)
    monkeypatch.setattr(provider, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(provider, "_instance", None)

    analytics = provider.Analytics()
    provider.capture_first_run_if_needed()

    assert analytics._disabled is True
    assert anonymous_id_path.exists() is False
    assert first_run_path.exists() is False
