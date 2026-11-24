"""Definicion de las tools que se ofrecen a la IA y su ejecucion.

La IA solo elige la tool y propone parametros. La ejecucion reutiliza
app/routers/tools.py con el usuario autenticado por JWT: la IA nunca
indica a que usuario pertenece la operacion.
"""
import json

from app.models import Category, User
from app.routers import tools as backend_tools
from sqlalchemy.orm import Session
from pydantic import ValidationError

WRITE_TOOLS = {"create_expense", "create_income"}

def _movement_params(categories: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Monto. Omitir si el usuario no lo dijo."},
            "currency": {
                "type": "string",
                "description": "Codigo ISO de la moneda mencionada (ARS, USD, EUR). Omitir si no menciona moneda.",
            },
            "date": {"type": "string", "description": "Fecha AAAA-MM-DD. Omitir si es hoy."},
            "category": {
                "type": "string",
                "enum": categories,
                "description": "Categoria existente que mejor corresponde al movimiento.",
            },
            "account": {"type": "string", "description": "Cuenta SOLO si el usuario la menciono. Nunca inventarla."},
            "description": {"type": "string", "description": "Texto corto con el motivo."},
        },
    }


def _tool(name: str, description: str, parameters: dict) -> dict:
    return {"type": "function", "function": {"name": name, "description": description, "parameters": parameters}}


def build_tool_definitions(db: Session) -> list[dict]:
    """Arma las tools con las categorias reales, para que la IA elija una existente."""
    names = {"EXPENSE": [], "INCOME": []}
    for category in db.query(Category).order_by(Category.name).all():
        names[category.type].append(category.name)

    return [
        _tool("create_expense", "Registra un gasto del usuario.", _movement_params(names["EXPENSE"])),
        _tool("create_income", "Registra un ingreso del usuario (sueldo, cobro, venta).", _movement_params(names["INCOME"])),
        _tool(
            "get_balance",
            "Consulta el saldo registrado. Sin account devuelve el total de todas las cuentas.",
            {"type": "object", "properties": {"account": {"type": "string"}}},
        ),
        _tool(
            "get_transactions",
            "Lista movimientos. type: EXPENSE o INCOME. Fechas AAAA-MM-DD. limit maximo 50.",
            {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "type": {"type": "string", "enum": ["EXPENSE", "INCOME"]},
                    "account": {"type": "string"},
                    "category": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
        ),
        _tool(
            "get_expenses_by_category",
            "Total de gastos agrupado por categoria. Sin fechas usa el mes actual.",
            {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "account": {"type": "string"},
                },
            },
        ),
    ]


def _str(args: dict, key: str) -> str | None:
    value = args.get(key)
    return str(value) if value not in (None, "") else None


def execute(name: str, args: dict, db: Session, user: User) -> dict:
    """Ejecuta una tool con el usuario autenticado y devuelve el envelope del backend."""

    if name in WRITE_TOOLS:
        try:
            body = backend_tools.MovementIn(
                amount=args.get("amount"),
                date=_str(args, "date"),
                category=_str(args, "category"),
                account=_str(args, "account"),
                description=(_str(args, "description") or "")[:200] or None,
                currency=_str(args, "currency"),
            )
        except ValidationError:
            return backend_tools._env(
                "rejected",
                "INVALID_INPUT",
                hint="Los parametros enviados por la IA son invalidos. No se registro nada."
            )

        kind = "expense" if name == "create_expense" else "income"
        return backend_tools._create(kind, body, db, user)

    if name == "get_balance":
        return backend_tools.tools_balance(db=db, user=user, account=_str(args, "account"))

    if name == "get_transactions":
        try:
            limit = int(args.get("limit") or 10)
        except (TypeError, ValueError):
            limit = 10
        return backend_tools.tools_transactions(
            db=db, user=user,
            date_from=_str(args, "date_from"), date_to=_str(args, "date_to"),
            type_=_str(args, "type"), account=_str(args, "account"),
            category=_str(args, "category"), limit=limit,
        )

    if name == "get_expenses_by_category":
        return backend_tools.tools_expenses_by_category(
            db=db, user=user,
            date_from=_str(args, "date_from"), date_to=_str(args, "date_to"),
            account=_str(args, "account"),
        )

    return backend_tools._env("rejected", "UNKNOWN_TOOL", hint="Operacion no disponible.")


def parse_arguments(raw) -> dict | None:
    """Los argumentos llegan como texto JSON. Si no son un objeto valido se descartan."""
    if isinstance(raw, dict):
        return raw
    try:
        value = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None
