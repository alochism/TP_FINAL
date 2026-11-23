from decimal import Decimal


def register(client, path, headers, account_id, category_id, amount, date="2026-11-10"):
    client.post(
        path,
        json={
            "account_id": account_id,
            "category_id": category_id,
            "amount": amount,
            "date": date
        },
        headers=headers
    )


def test_balance_is_calculated_from_transactions(client, create_user, create_account, category_id):
    # Saldo = saldo inicial + ingresos - gastos
    headers = create_user()
    account = create_account(headers, initial_balance=500000)

    register(client, "/transactions/income", headers, account["id"], category_id("Sueldo", "INCOME"), 100000)
    register(client, "/transactions/expense", headers, account["id"], category_id("Transporte", "EXPENSE"), 40000)

    response = client.get(f"/accounts/balance?account_id={account['id']}", headers=headers)

    assert Decimal(str(response.json()["balance"])) == Decimal("560000")


def test_total_balance_adds_all_accounts(client, create_user, create_account, category_id):
    headers = create_user()
    bank = create_account(headers, name="Banco Provincia del Neuquen", initial_balance=850000, type="BANK")
    wallet = create_account(headers, name="Mercado Pago", initial_balance=125500.50, type="WALLET")

    register(client, "/transactions/expense", headers, wallet["id"], category_id("Transporte", "EXPENSE"), 18500)

    response = client.get("/accounts/balance", headers=headers)

    assert Decimal(str(response.json()["balance"])) == Decimal("957000.50")
    assert bank["id"] != wallet["id"]


def test_balance_of_account_of_another_user_is_not_found(client, create_user, create_account):
    ana = create_user("ana.quiroga@correo.com")
    bruno = create_user("bruno.sepulveda@correo.com")

    bruno_account = create_account(bruno)

    response = client.get(f"/accounts/balance?account_id={bruno_account['id']}", headers=ana)

    assert response.status_code == 404


def test_expenses_by_category(client, create_user, create_account, category_id):
    headers = create_user()
    account = create_account(headers, initial_balance=100000)
    transport = category_id("Transporte", "EXPENSE")
    services = category_id("Servicios", "EXPENSE")

    register(client, "/transactions/expense", headers, account["id"], transport, 5000)
    register(client, "/transactions/expense", headers, account["id"], transport, 7000)
    register(client, "/transactions/expense", headers, account["id"], services, 20000)

    # Los ingresos no deben aparecer en el resumen de gastos
    register(client, "/transactions/income", headers, account["id"], category_id("Sueldo", "INCOME"), 90000)

    response = client.get("/transactions/expenses-by-category", headers=headers)
    totals = {item["category"]: Decimal(str(item["total"])) for item in response.json()}

    assert totals == {"Servicios": Decimal("20000"), "Transporte": Decimal("12000")}


def test_expenses_by_category_filters_by_date(client, create_user, create_account, category_id):
    headers = create_user()
    account = create_account(headers, initial_balance=100000)
    transport = category_id("Transporte", "EXPENSE")

    register(client, "/transactions/expense", headers, account["id"], transport, 5000, "2026-10-15")
    register(client, "/transactions/expense", headers, account["id"], transport, 7000, "2026-11-05")

    response = client.get(
        "/transactions/expenses-by-category?date_from=2026-11-01&date_to=2026-11-30",
        headers=headers
    )

    assert Decimal(str(response.json()[0]["total"])) == Decimal("7000")


def test_expenses_report_isolated_by_user(
    client, create_user, create_account, category_id
):
    ana = create_user("ana@correo.com")
    bruno = create_user("bruno@correo.com")

    ana_account = create_account(ana, name="Efectivo")
    bruno_account = create_account(bruno, name="Efectivo")

    transport = category_id("Transporte", "EXPENSE")

    register(
        client, "/transactions/expense",
        ana, ana_account["id"], transport, 5000
    )

    register(
        client, "/transactions/expense",
        bruno, bruno_account["id"], transport, 20000
    )

    response = client.get(
        "/transactions/expenses-by-category",
        headers=ana
    )

    assert response.status_code == 200

    totals = {
        item["category"]: Decimal(str(item["total"]))
        for item in response.json()
    }

    assert totals == {"Transporte": Decimal("5000")}


def test_voided_expense_is_excluded_from_category_report(
    client, create_user, create_account, category_id
):
    headers = create_user()
    account = create_account(headers, initial_balance=20000)
    transport = category_id("Transporte", "EXPENSE")

    first = client.post(
        "/transactions/expense",
        json={
            "account_id": account["id"],
            "category_id": transport,
            "amount": 3000,
            "date": "2026-11-10"
        },
        headers=headers
    )
    assert first.status_code == 201

    register(
        client, "/transactions/expense",
        headers, account["id"], transport, 7000
    )

    # Anulamos solamente el primer gasto
    response = client.patch(
        f"/transactions/{first.json()['id']}/void",
        headers=headers
    )
    assert response.status_code == 200

    report = client.get(
        "/transactions/expenses-by-category",
        headers=headers
    )

    totals = {
        item["category"]: Decimal(str(item["total"]))
        for item in report.json()
    }

    assert totals == {"Transporte": Decimal("7000")}

    balance = client.get("/accounts/balance", headers=headers)
    assert Decimal(str(balance.json()["balance"])) == Decimal("13000")
