"""Tests del canal conversacional.

El proveedor de IA se reemplaza por respuestas simuladas: lo que se prueba
es que el backend decide, sin importar lo que la IA proponga.
"""
import json

import pytest
from app.agent import llm
from app.models import AuditLog, Transaction


def tool_call(name, arguments, call_id="call_1"):
    return {"id": call_id, "type": "function",
            "function": {"name": name, "arguments": json.dumps(arguments)}}


@pytest.fixture
def fake_llm(monkeypatch):
    """Simula al proveedor: devuelve en orden las respuestas indicadas."""
    monkeypatch.setenv("LLM_BASE_URL", "http://llm-simulado")
    monkeypatch.setenv("LLM_MODEL", "modelo-simulado")

    def _configure(*answers):
        pending = list(answers)

        def _fake(messages, tools):
            answer = pending.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return answer

        monkeypatch.setattr(llm, "chat_completion", _fake)

    return _configure


def test_chat_requires_authentication(client):
    response = client.post("/chat", json={"message": "Gasté 5000 en nafta"})

    assert response.status_code in (401, 403)


def test_chat_registers_expense(client, db, create_user, create_account, fake_llm):
    headers = create_user()
    create_account(headers, name="Mercado Pago", type="WALLET", initial_balance=100000)
    fake_llm(
        {"content": None, "tool_calls": [tool_call("create_expense", {
            "amount": 18500, "category": "Alimentacion", "account": "mercado pago",
            "description": "supermercado"})]},
        {"content": "Listo: gasto de $18.500 en Alimentación desde Mercado Pago."},
    )

    response = client.post("/chat", json={"message": "Gasté 18.500 en el súper con Mercado Pago"},
                           headers=headers)

    body = response.json()
    assert response.status_code == 200
    assert body["actions"][0]["status"] == "ok"
    assert body["transaction_id"] is not None
    assert db.query(Transaction).count() == 1

    audit = db.query(AuditLog).one()
    assert audit.message == "Gasté 18.500 en el súper con Mercado Pago"
    assert audit.transaction_id == body["transaction_id"]
    assert audit.actions[0]["arguments"]["amount"] == 18500


def test_chat_asks_for_missing_account(client, db, create_user, create_account, fake_llm):
    headers = create_user()
    create_account(headers, name="Efectivo")
    fake_llm(
        {"content": None, "tool_calls": [tool_call("create_expense", {
            "amount": 20000, "category": "Servicios", "description": "luz"})]},
        {"content": "Entendí $20.000 de luz. ¿Desde qué cuenta lo pagaste?"},
    )

    response = client.post("/chat", json={"message": "Pagué 20 lucas de luz"}, headers=headers)

    body = response.json()
    assert body["actions"][0]["status"] == "needs_info"
    assert "account" in body["actions"][0]["missing_fields"]
    assert body["transaction_id"] is None
    assert db.query(Transaction).count() == 0


def test_chat_allows_only_one_write_per_message(client, db, create_user, create_account, fake_llm):
    headers = create_user()
    create_account(headers, name="Efectivo")
    expense = {"amount": 5000, "category": "Transporte", "account": "Efectivo"}
    fake_llm(
        {"content": None, "tool_calls": [
            tool_call("create_expense", expense, "call_1"),
            tool_call("create_expense", expense, "call_2"),
        ]},
        {"content": "Registré un gasto."},
    )

    response = client.post("/chat", json={"message": "Gasté 5000 en nafta"}, headers=headers)

    statuses = [action["code"] for action in response.json()["actions"]]
    assert statuses == [None, "ONE_WRITE_PER_MESSAGE"]
    assert db.query(Transaction).count() == 1


def test_chat_does_not_modify_anything_if_llm_fails(client, db, create_user, create_account, fake_llm):
    headers = create_user()
    create_account(headers, name="Efectivo")
    fake_llm(llm.LLMError("timeout"))

    response = client.post("/chat", json={"message": "Gasté 5000 en nafta"}, headers=headers)

    assert response.status_code == 200
    assert "No se registró nada" in response.json()["reply"]
    assert db.query(Transaction).count() == 0
    assert db.query(AuditLog).one().llm_error is True


def test_chat_cannot_use_accounts_of_another_user(client, db, create_user, create_account, fake_llm):
    other = create_user(email="bruno.salas@correo.com")
    create_account(other, name="Banco Galicia")
    headers = create_user()
    create_account(headers, name="Efectivo")
    fake_llm(
        {"content": None, "tool_calls": [tool_call("create_expense", {
            "amount": 5000, "category": "Transporte", "account": "Banco Galicia"})]},
        {"content": "¿Desde qué cuenta lo pagaste?"},
    )

    response = client.post("/chat", json={"message": "Gasté 5000 en nafta con Galicia"}, headers=headers)

    action = response.json()["actions"][0]
    assert action["status"] == "needs_info"
    assert action["code"] == "ACCOUNT_NOT_FOUND"
    assert db.query(Transaction).count() == 0


def test_chat_rejects_invalid_amount(client, db, create_user, create_account, fake_llm):
    headers = create_user()
    create_account(headers, name="Efectivo")
    fake_llm(
        {"content": None, "tool_calls": [tool_call("create_expense", {
            "amount": -300, "category": "Transporte", "account": "Efectivo"})]},
        {"content": "El monto tiene que ser mayor a cero."},
    )

    response = client.post("/chat", json={"message": "Gasté -300 en nafta"}, headers=headers)

    assert response.json()["actions"][0]["code"] == "INVALID_AMOUNT"
    assert db.query(Transaction).count() == 0


def test_chat_without_provider_configured(client, db, create_user, monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    headers = create_user()

    response = client.post("/chat", json={"message": "¿Cuánto tengo?"}, headers=headers)

    assert response.status_code == 200
    assert "no está disponible" in response.json()["reply"]


def test_tool_uses_today_when_date_is_missing(client, create_user, create_account):
    headers = create_user()
    create_account(headers, name="Efectivo")

    response = client.post("/tools/expense", json={
        "amount": 1000, "category": "Transporte", "account": "Efectivo"}, headers=headers)

    assert response.json()["status"] == "ok"


def test_chat_rejects_other_currency(client, db, create_user, create_account, fake_llm):
    headers = create_user()
    create_account(headers, name="Efectivo")
    fake_llm(
        {"content": None, "tool_calls": [tool_call("create_expense", {
            "amount": 50, "currency": "USD", "category": "Educación", "account": "Efectivo"})]},
        {"content": "Por ahora solo registro movimientos en pesos."},
    )

    response = client.post("/chat", json={"message": "Gasté 50 dólares en un libro con efectivo"},
                           headers=headers)

    assert response.json()["actions"][0]["code"] == "UNSUPPORTED_CURRENCY"
    assert db.query(Transaction).count() == 0


def test_tools_offer_only_existing_categories(db):
    from app.agent.tools import build_tool_definitions

    tools = {t["function"]["name"]: t for t in build_tool_definitions(db)}
    expense_categories = tools["create_expense"]["function"]["parameters"]["properties"]["category"]["enum"]

    assert "Alimentación" in expense_categories
    assert "Sueldo" not in expense_categories
