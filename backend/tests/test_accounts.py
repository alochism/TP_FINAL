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
