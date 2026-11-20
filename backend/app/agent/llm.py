"""Cliente del proveedor de IA.

Usa el formato de Chat Completions de OpenAI, que aceptan tanto el gateway
de OpenClaw como Gemini y otros proveedores. Cambiar de proveedor es cambiar
LLM_BASE_URL, LLM_API_KEY y LLM_MODEL: la logica financiera no se toca.
"""
import logging
import os

import httpx

logger = logging.getLogger("uvicorn.error")


class LLMError(Exception):
    """El proveedor no respondio, tardo demasiado o devolvio algo invalido."""


def is_configured() -> bool:
    return bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_MODEL"))


def chat_completion(messages: list[dict], tools: list[dict]) -> dict:
    """Devuelve el mensaje del asistente: {"content": ..., "tool_calls": [...]}."""
    base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
    timeout = float(os.getenv("LLM_TIMEOUT", "30"))
    api_key = os.getenv("LLM_API_KEY", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": os.getenv("LLM_MODEL"),
                "messages": messages,
                "tools": tools,
                "temperature": 0,
            },
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        logger.warning("Proveedor de IA no disponible: %s", type(exc).__name__)
        raise LLMError("Proveedor de IA no disponible") from exc

    if response.status_code != 200:
        # Se registra el codigo y el mensaje del proveedor (nunca la API key)
        logger.warning("Proveedor de IA respondio %s: %s", response.status_code, response.text[:300])
        raise LLMError(f"Proveedor de IA respondio {response.status_code}")

    try:
        return response.json()["choices"][0]["message"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Respuesta invalida del proveedor de IA: %s", response.text[:300])
        raise LLMError("Respuesta invalida del proveedor de IA") from exc
