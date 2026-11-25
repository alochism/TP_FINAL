def test_create_account(client, create_user):
    headers = create_user()

    response = client.post(
        "/accounts",
        json={"name": "Mercado Pago", "type": "WALLET", "initial_balance": 1500},
        headers=headers
    )

    assert response.status_code == 201
    assert response.json()["currency"] == "ARS"
    assert response.json()["active"] is True


def test_create_account_with_invalid_type_is_rejected(client, create_user):
    headers = create_user()

    response = client.post(
        "/accounts",
        json={"name": "Visa", "type": "CREDIT_CARD"},
        headers=headers
    )

    assert response.status_code == 400


def test_create_account_with_other_currency_is_rejected(client, create_user):
    # En P0 solo se admiten cuentas en pesos
    headers = create_user()

    response = client.post(
        "/accounts",
        json={"name": "Ahorro", "type": "BANK", "currency": "USD"},
        headers=headers
    )

    assert response.status_code == 400


def test_user_only_sees_own_accounts(client, create_user, create_account):
    ana = create_user("ana.quiroga@correo.com")
    bruno = create_user("bruno.sepulveda@correo.com")

    create_account(ana, name="Cuenta de Ana")
    create_account(bruno, name="Cuenta de Bruno")

    response = client.get("/accounts", headers=ana)
    names = [account["name"] for account in response.json()]

    assert names == ["Cuenta de Ana"]


def test_deactivated_account_is_hidden_and_cannot_be_used(client, create_user, create_account, category_id):
    headers = create_user()
    account = create_account(headers)

    response = client.patch(f"/accounts/{account['id']}/deactivate", headers=headers)
    expense = client.post(
        "/transactions/expense",
        json={
            "account_id": account["id"],
            "category_id": category_id("Transporte", "EXPENSE"),
            "amount": 1000,
            "date": "2026-11-10"
        },
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["active"] is False
    assert client.get("/accounts", headers=headers).json() == []
    assert expense.status_code == 404


def test_cannot_deactivate_account_of_another_user(client, create_user, create_account):
    owner = create_user(email="bruno.salas@correo.com")
    account = create_account(owner)
    headers = create_user()

    response = client.patch(f"/accounts/{account['id']}/deactivate", headers=headers)

    assert response.status_code == 404


def test_deactivated_account_is_excluded_from_total_balance(
    client, create_user
):
    headers = create_user()

    first = client.post(
        "/accounts",
        json={
            "name": "Efectivo",
            "type": "CASH",
            "initial_balance": 100000
        },
        headers=headers
    )

    second = client.post(
        "/accounts",
        json={
            "name": "Mercado Pago",
            "type": "WALLET",
            "initial_balance": 50000
        },
        headers=headers
    )

    assert first.status_code == 201
    assert second.status_code == 201

    before = client.get("/accounts/balance", headers=headers)
    assert before.json()["balance"] == 150000

    response = client.patch(
        f"/accounts/{first.json()['id']}/deactivate",
        headers=headers
    )

    assert response.status_code == 200

    after = client.get("/accounts/balance", headers=headers)
    assert after.json()["balance"] == 50000


def test_reject_blank_account_name(client, create_user):
    headers = create_user()

    response = client.post(
        "/accounts",
        json={
            "name": "   ",
            "type": "CASH",
            "initial_balance": 0
        },
        headers=headers
    )

    assert response.status_code in (400, 422)


def test_reject_duplicate_account_name(client, create_user):
    headers = create_user()

    first = client.post(
        "/accounts",
        json={"name": "Mercado Pago", "type": "WALLET"},
        headers=headers
    )

    second = client.post(
        "/accounts",
        json={"name": " mercado pago ", "type": "WALLET"},
        headers=headers
    )

    assert first.status_code == 201
    assert second.status_code == 400


def test_reject_negative_initial_balance(client, create_user):
    headers = create_user()

    response = client.post(
        "/accounts",
        json={
            "name": "Efectivo",
            "type": "CASH",
            "initial_balance": -500
        },
        headers=headers
    )

    assert response.status_code in (400, 422)
