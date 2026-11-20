"""Cliente del proveedor de IA.

Usa el formato de Chat Completions de OpenAI, que aceptan tanto el gateway
de OpenClaw como Gemini y otros proveedores. Cambiar de proveedor es cambiar
LLM_BASE_URL, LLM_API_KEY y LLM_MODEL: la logica financiera no se toca.

Ante errores transitorios del proveedor (429 o 5xx) se reintenta y, si esta
configurado, se usa un modelo de respaldo (LLM_FALLBACK_MODEL). Reintentar es
seguro: la IA no ejecuta operaciones, solo propone la tool que ejecuta el backend.
"""
import logging
import os
import time

import httpx

logger = logging.getLogger("uvicorn.error")

TRANSIENT_STATUS = {429, 500, 502, 503, 504}
RETRY_DELAYS = (1.5, 3.0)


class LLMError(Exception):
    """El proveedor no respondio, tardo demasiado o devolvio algo invalido."""


def is_configured() -> bool:
    return bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_MODEL"))


def _post(model: str, messages: list[dict], tools: list[dict]) -> httpx.Response:
    base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    return httpx.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json={"model": model, "messages": messages, "tools": tools, "temperature": 0},
        timeout=float(os.getenv("LLM_TIMEOUT", "30")),
    )


def chat_completion(messages: list[dict], tools: list[dict]) -> dict:
    """Devuelve el mensaje del asistente: {"content": ..., "tool_calls": [...]}."""
    models = [os.getenv("LLM_MODEL")]
    if os.getenv("LLM_FALLBACK_MODEL"):
        models.append(os.getenv("LLM_FALLBACK_MODEL"))

    response = None
    for model in models:
        for attempt in range(len(RETRY_DELAYS) + 1):
            try:
                response = _post(model, messages, tools)
            except httpx.HTTPError as exc:
                logger.warning("Proveedor de IA no disponible (%s): %s", model, type(exc).__name__)
                raise LLMError("Proveedor de IA no disponible") from exc

            if response.status_code not in TRANSIENT_STATUS:
                break

            # Se registra el codigo y el mensaje del proveedor (nunca la API key)
            logger.warning("Proveedor de IA respondio %s (%s, intento %s): %s",
                           response.status_code, model, attempt + 1, response.text[:200])
            if attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])

        if response.status_code not in TRANSIENT_STATUS:
            break

    if response.status_code != 200:
        logger.warning("Proveedor de IA respondio %s: %s", response.status_code, response.text[:300])
        raise LLMError(f"Proveedor de IA respondio {response.status_code}")

    try:
        return response.json()["choices"][0]["message"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Respuesta invalida del proveedor de IA: %s", response.text[:300])
        raise LLMError("Respuesta invalida del proveedor de IA") from exc
