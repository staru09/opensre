from __future__ import annotations

from app.agent.tools.clients.llm_client import _format_anthropic_retry_error


def test_format_anthropic_retry_error_for_connection_issue() -> None:
    APIConnectionError = type("APIConnectionError", (Exception,), {})

    message = _format_anthropic_retry_error(APIConnectionError("boom"))

    assert "connection failed" in message.lower()


def test_format_anthropic_retry_error_for_529() -> None:
    OverloadedError = type("OverloadedError", (Exception,), {"status_code": 529})

    message = _format_anthropic_retry_error(OverloadedError("busy"))

    assert "HTTP 529" in message
