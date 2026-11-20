"""POST /chat: canal conversacional del P0.

Flujo: mensaje -> IA (interpreta y elige tool) -> backend (valida y decide)
-> PostgreSQL -> IA redacta la respuesta con los datos del backend.

Reglas que aplica el backend, sin depender de la IA:
- el usuario sale del JWT, nunca del mensaje ni de la IA;
- como maximo una operacion de escritura por mensaje;
- si la IA falla, no se modifica nada y se informa;
- cada mensaje queda registrado en audit_logs.
"""
import json
from pathlib import Path
from typing import Annotated, Literal

from app.agent import llm
from app.agent import tools as agent_tools
from app.database import get_db
from app.models import AuditLog, User
from app.routers.tools import _today
from app.security import get_current_user
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(prefix="/chat", tags=["Chat"])

PROMPT_TEMPLATE = (Path(__file__).resolve().parent.parent / "agent" / "prompt.md").read_text(encoding="utf-8")
WEEKDAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MAX_ROUNDS = 4
MAX_HISTORY = 20

FALLBACK_REPLY = "No pude procesar tu mensaje en este momento. No se registró nada. ¿Podés intentar de nuevo?"
NOT_CONFIGURED_REPLY = "El asistente no está disponible en este momento. No se registró nada."


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    # Mensajes anteriores de la conversacion, solo texto. Permite responder
    # a las preguntas del asistente ("¿desde que cuenta?" -> "Mercado Pago")
    history: list[HistoryItem] = Field(default_factory=list)


class ChatAction(BaseModel):
    tool: str
    arguments: dict
    status: str
    code: str | None = None
    missing_fields: list[str] = []


class ChatOut(BaseModel):
    reply: str
    actions: list[ChatAction]
    transaction_id: int | None = None


def _system_prompt() -> str:
    today = _today()
    return PROMPT_TEMPLATE.format(today=today.isoformat(), weekday=WEEKDAYS[today.weekday()])


def _save_audit(db: Session, user: User, message: str, actions: list[dict],
                transaction_id: int | None, reply: str, llm_error: bool) -> None:
    db.add(AuditLog(
        user_id=user.id, message=message, actions=actions,
        transaction_id=transaction_id, reply=reply, llm_error=llm_error,
    ))
    db.commit()


@router.post("", response_model=ChatOut)
def chat(
    body: ChatIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    actions: list[dict] = []
    transaction_id = None

    if not llm.is_configured():
        _save_audit(db, user, body.message, actions, None, NOT_CONFIGURED_REPLY, True)
        return ChatOut(reply=NOT_CONFIGURED_REPLY, actions=[])

    messages = [{"role": "system", "content": _system_prompt()}]
    messages += [item.model_dump() for item in body.history[-MAX_HISTORY:]]
    messages.append({"role": "user", "content": body.message})

    write_done = False
    reply = None

    try:
        for _ in range(MAX_ROUNDS):
            answer = llm.chat_completion(messages, agent_tools.TOOL_DEFINITIONS)
            tool_calls = answer.get("tool_calls") or []

            if not tool_calls:
                reply = (answer.get("content") or "").strip()
                break

            messages.append({"role": "assistant", "content": answer.get("content") or "", "tool_calls": tool_calls})

            for call in tool_calls:
                name = call.get("function", {}).get("name", "")
                args = agent_tools.parse_arguments(call.get("function", {}).get("arguments"))

                if args is None:
                    result = {"status": "rejected", "code": "INVALID_INPUT", "missing_fields": [],
                              "options": {}, "data": {}, "message_hint": "Parametros invalidos."}
                elif name in agent_tools.WRITE_TOOLS and write_done:
                    # El backend impide dos escrituras por mensaje aunque la IA las pida
                    result = {"status": "rejected", "code": "ONE_WRITE_PER_MESSAGE", "missing_fields": [],
                              "options": {}, "data": {},
                              "message_hint": "Solo se registra una operacion por mensaje. No se guardo esta."}
                else:
                    result = agent_tools.execute(name, args, db, user)
                    if name in agent_tools.WRITE_TOOLS and result["status"] == "ok":
                        write_done = True
                        transaction_id = result["data"].get("transaction_id")

                actions.append({
                    "tool": name, "arguments": args or {}, "status": result["status"],
                    "code": result.get("code"), "missing_fields": result.get("missing_fields", []),
                })
                messages.append({
                    "role": "tool", "tool_call_id": call.get("id", ""),
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
    except llm.LLMError:
        # Si ya se registro algo, se informa con datos del backend, no de la IA
        reply = FALLBACK_REPLY if transaction_id is None else (
            "Registré el movimiento, pero no pude terminar de redactar la respuesta. "
            "Revisalo en Movimientos."
        )
        _save_audit(db, user, body.message, actions, transaction_id, reply, True)
        return ChatOut(reply=reply, actions=actions, transaction_id=transaction_id)

    if not reply:
        reply = FALLBACK_REPLY if transaction_id is None else "Listo, quedó registrado."

    _save_audit(db, user, body.message, actions, transaction_id, reply, False)
    return ChatOut(reply=reply, actions=actions, transaction_id=transaction_id)
