def expense_data(account_id, category_id, amount=18500):
    return {
        "account_id": account_id,
        "category_id": category_id,
        "amount": amount,
        "date": "2026-11-10",
        "description": "Carga de combustible"
    }


def test_create_expense(client, create_user, create_account, category_id):
    headers = create_user()
    account = create_account(headers)

    response = client.post(
        "/transactions/expense",
        json=expense_data(account["id"], category_id("Transporte", "EXPENSE")),
        headers=headers
    )

    assert response.status_code == 201
    assert response.json()["type"] == "EXPENSE"
    assert response.json()["status"] == "ACTIVE"


def test_create_income(client, create_user, create_account, category_id):
    headers = create_user()
    account = create_account(headers)

    response = client.post(
        "/transactions/income",
        json=expense_data(account["id"], category_id("Sueldo", "INCOME"), 350000),
        headers=headers
    )

    assert response.status_code == 201
    assert response.json()["type"] == "INCOME"


def test_amount_must_be_greater_than_zero(client, create_user, create_account, category_id):
    headers = create_user()
    account = create_account(headers)
    transport = category_id("Transporte", "EXPENSE")

    for amount in (0, -500):
        response = client.post(
            "/transactions/expense",
            json=expense_data(account["id"], transport, amount),
            headers=headers
        )

        assert response.status_code == 400


def test_cannot_use_account_of_another_user(client, create_user, create_account, category_id):
    # Regla central de autorizacion: un usuario no puede operar
    # sobre la cuenta de otro aunque conozca su identificador
    ana = create_user("ana.quiroga@correo.com")
    bruno = create_user("bruno.sepulveda@correo.com")

    bruno_account = create_account(bruno, name="Cuenta de Bruno")

    response = client.post(
        "/transactions/expense",
        json=expense_data(bruno_account["id"], category_id("Transporte", "EXPENSE")),
        headers=ana
    )

    assert response.status_code == 404


def test_expense_requires_expense_category(client, create_user, create_account, category_id):
    headers = create_user()
    account = create_account(headers)

    response = client.post(
        "/transactions/expense",
        json=expense_data(account["id"], category_id("Sueldo", "INCOME")),
        headers=headers
    )

    assert response.status_code == 400


def test_income_requires_income_category(client, create_user, create_account, category_id):
    headers = create_user()
    account = create_account(headers)

    response = client.post(
        "/transactions/income",
        json=expense_data(account["id"], category_id("Transporte", "EXPENSE")),
        headers=headers
    )

    assert response.status_code == 400


def test_user_only_sees_own_transactions(client, create_user, create_account, category_id):
    ana = create_user("ana.quiroga@correo.com")
    bruno = create_user("bruno.sepulveda@correo.com")
    transport = category_id("Transporte", "EXPENSE")

    ana_account = create_account(ana)
    bruno_account = create_account(bruno)

    client.post("/transactions/expense", json=expense_data(ana_account["id"], transport), headers=ana)
    client.post("/transactions/expense", json=expense_data(bruno_account["id"], transport), headers=bruno)

    response = client.get("/transactions", headers=ana)

    assert len(response.json()) == 1
    assert response.json()[0]["account_id"] == ana_account["id"]
