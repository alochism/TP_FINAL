"""Tests del cliente del proveedor de IA (sin llamadas reales)."""
import httpx
import pytest
from app.agent import llm


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://llm-simulado")
    monkeypatch.setenv("LLM_MODEL", "modelo-principal")
    monkeypatch.delenv("LLM_FALLBACK_MODEL", raising=False)
    monkeypatch.setattr(llm, "RETRY_DELAYS", (0,))
    calls = []

    def _configure(*statuses):
        pending = list(statuses)

        def _fake_post(url, headers, json, timeout):
            calls.append(json["model"])
            status = pending.pop(0)
            if status == "timeout":
                raise httpx.ReadTimeout("lento")
            body = {"choices": [{"message": {"content": "ok"}}]} if status == 200 else {"error": "x"}
            return httpx.Response(status, json=body)

        monkeypatch.setattr(llm.httpx, "post", _fake_post)
        return calls

    return _configure


def test_retries_transient_errors(provider):
    calls = provider(503, 200)

    assert llm.chat_completion([], [])["content"] == "ok"
    assert calls == ["modelo-principal"] * 2


def test_uses_fallback_model_when_main_is_unavailable(provider, monkeypatch):
    monkeypatch.setenv("LLM_FALLBACK_MODEL", "modelo-respaldo")
    calls = provider(503, 503, 200)

    assert llm.chat_completion([], [])["content"] == "ok"
    assert calls[-1] == "modelo-respaldo"


def test_does_not_retry_non_transient_errors(provider):
    calls = provider(404)

    with pytest.raises(llm.LLMError):
        llm.chat_completion([], [])
    assert len(calls) == 1


def test_timeout_goes_to_fallback_model(provider, monkeypatch):
    monkeypatch.setenv("LLM_FALLBACK_MODEL", "modelo-respaldo")
    calls = provider("timeout", 200)

    assert llm.chat_completion([], [])["content"] == "ok"
    assert calls == ["modelo-principal", "modelo-respaldo"]


def test_fails_after_exhausting_retries(provider):
    provider(503, 503)

    with pytest.raises(llm.LLMError):
        llm.chat_completion([], [])
