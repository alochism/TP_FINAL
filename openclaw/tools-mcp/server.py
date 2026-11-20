"""Servidor MCP de finanzas. Wrapper delgado sobre /tools/* del backend.

No contiene reglas de negocio: reenvia los parametros y devuelve el envelope tal cual.
Las unicas respuestas propias son errores de transporte/autenticacion.

MODO DE IDENTIDAD (solo desarrollo): inicia sesion con un usuario de prueba definido
por variables de entorno. El canal multiusuario es POST /chat del backend, donde el
usuario sale del JWT de la interfaz web (ver openclaw/README.md).
"""
import os

import httpx
from mcp.server.fastmcp import FastMCP

BACKEND_URL = os.environ["BACKEND_URL"].rstrip("/")
AGENT_USER_EMAIL = os.environ["AGENT_USER_EMAIL"]
AGENT_USER_PASSWORD = os.environ["AGENT_USER_PASSWORD"]

mcp = FastMCP("finanzas")
_token: str | None = None


def _error(code: str, hint: str) -> dict:
    return {
        "status": "rejected", "code": code, "missing_fields": [],
        "options": {}, "data": {}, "message_hint": hint,
    }


def _login(client: httpx.Client) -> str | None:
    r = client.post(
        "/auth/login",
        json={"email": AGENT_USER_EMAIL, "password": AGENT_USER_PASSWORD},
    )
    return r.json().get("access_token") if r.status_code == 200 else None


def _call(method: str, path: str, *, params: dict | None = None, body: dict | None = None) -> dict:
    global _token
    params = {k: v for k, v in (params or {}).items() if v is not None}
    body = {k: v for k, v in (body or {}).items() if v is not None} if body is not None else None

    try:
        with httpx.Client(base_url=BACKEND_URL, timeout=15) as client:
            for attempt in (1, 2):
                if _token is None:
                    _token = _login(client)
                    if _token is None:
                        return _error("UNAUTHENTICATED", "No se pudo autenticar. No se modifico nada.")
                r = client.request(
                    method, path, params=params, json=body,
                    headers={"Authorization": f"Bearer {_token}"},
                )
                if r.status_code in (401, 403) and attempt == 1:
                    _token = None  # token vencido: reintenta una vez con login nuevo
                    continue
                break
    except httpx.HTTPError:
        return _error("BACKEND_UNAVAILABLE", "No pude comunicarme con el sistema. No se modifico nada.")

    if r.status_code in (401, 403):
        return _error("UNAUTHENTICATED", "No autenticado. No se modifico nada.")
    if r.status_code == 422:
        return _error("INVALID_INPUT", "Los datos enviados no tienen el formato esperado.")
    if r.status_code >= 400:
        return _error("INTERNAL_ERROR", "Error del sistema. No se modifico nada.")
    return r.json()


@mcp.tool()
def create_expense(
    amount: float | None = None,
    account: str | None = None,
    category: str | None = None,
    date: str | None = None,
    description: str | None = None,
) -> dict:
    """Registra un gasto del usuario.

    - amount: numero en pesos. Convertir "20 lucas" -> 20000, "350 mil" -> 350000.
    - account: nombre de la cuenta SOLO si el usuario la menciono. Nunca la inventes ni la deduzcas.
    - category: tu mejor interpretacion (ej. "Alimentacion", "Servicios").
    - date: AAAA-MM-DD. Resolver "ayer", "el martes" con la fecha actual. Omitir si es hoy.
    - description: texto corto.
    Si falta un dato, la respuesta tiene status "needs_info" y NO se registro nada:
    pregunta al usuario solo lo que figura en missing_fields y vuelve a llamar con todos los datos.
    """
    return _call("POST", "/tools/expense", body={
        "amount": amount, "account": account, "category": category,
        "date": date, "description": description,
    })


@mcp.tool()
def create_income(
    amount: float | None = None,
    account: str | None = None,
    category: str | None = None,
    date: str | None = None,
    description: str | None = None,
) -> dict:
    """Registra un ingreso del usuario (ej. sueldo, cobro). Mismas reglas que create_expense;
    'account' es la cuenta donde se acredito el dinero. Nunca inventes la cuenta."""
    return _call("POST", "/tools/income", body={
        "amount": amount, "account": account, "category": category,
        "date": date, "description": description,
    })


@mcp.tool()
def get_balance(account: str | None = None) -> dict:
    """Consulta el saldo registrado. Sin 'account' devuelve el total de todas las cuentas."""
    return _call("GET", "/tools/balance", params={"account": account})


@mcp.tool()
def get_transactions(
    account: str | None = None,
    category: str | None = None,
    type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10,
) -> dict:
    """Lista movimientos recientes. type: "EXPENSE" o "INCOME". Fechas AAAA-MM-DD. limit maximo 50."""
    return _call("GET", "/tools/transactions", params={
        "account": account, "category": category, "type": type,
        "date_from": date_from, "date_to": date_to, "limit": limit,
    })


@mcp.tool()
def get_expenses_by_category(
    date_from: str | None = None,
    date_to: str | None = None,
    account: str | None = None,
) -> dict:
    """Total de gastos agrupado por categoria. Si no se indican fechas, usa el mes actual.
    Resolver "este mes", "el mes pasado" a fechas AAAA-MM-DD."""
    return _call("GET", "/tools/expenses-by-category", params={
        "date_from": date_from, "date_to": date_to, "account": account,
    })


if __name__ == "__main__":
    mcp.run()  # stdio
