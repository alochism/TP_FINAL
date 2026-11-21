def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "ana.quiroga@correo.com", "password": "Clave1234"}
    )

    assert response.status_code == 201
    assert response.json()["email"] == "ana.quiroga@correo.com"

    # La contraseña nunca se devuelve en la respuesta
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_register_duplicate_email_is_rejected(client):
    data = {"email": "ana.quiroga@correo.com", "password": "Clave1234"}

    client.post("/auth/register", json=data)
    response = client.post("/auth/register", json=data)

    assert response.status_code == 409


def test_login_with_wrong_password_is_rejected(client):
    client.post(
        "/auth/register",
        json={"email": "ana.quiroga@correo.com", "password": "Clave1234"}
    )

    response = client.post(
        "/auth/login",
        json={"email": "ana.quiroga@correo.com", "password": "OtraClave"}
    )

    assert response.status_code == 401


def test_protected_endpoint_without_token_is_rejected(client):
    response = client.get("/accounts")

    assert response.status_code in (401, 403)


def test_protected_endpoint_with_invalid_token_is_rejected(client):
    response = client.get(
        "/accounts",
        headers={"Authorization": "Bearer token-inventado"}
    )

    assert response.status_code == 401
