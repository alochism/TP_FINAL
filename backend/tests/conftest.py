import os

# Las variables se definen antes de importar la aplicacion, porque
# database.py y security.py las leen al momento de importarse.
# Los tests usan una base SQLite en memoria: no requieren PostgreSQL
# y cada test arranca con una base vacia
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "clave-solo-para-tests"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Category
from app.seed import CATEGORIES

# StaticPool mantiene una unica conexion, necesario para que la base
# en memoria sea la misma durante todo el test
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Se cargan las mismas categorias que usa la aplicacion
    for category_data in CATEGORIES:
        session.add(Category(**category_data))

    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    # La aplicacion usa la sesion de test en lugar de la base real
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def create_user(client):
    # Registra un usuario, inicia sesion y devuelve los headers con su token
    def _create_user(email="ana.quiroga@correo.com", password="Clave1234"):
        client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )

        response = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )

        token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    return _create_user


@pytest.fixture
def create_account(client):
    def _create_account(headers, name="Efectivo", initial_balance=0, type="CASH"):
        response = client.post(
            "/accounts",
            json={
                "name": name,
                "type": type,
                "initial_balance": initial_balance
            },
            headers=headers
        )

        return response.json()

    return _create_account


@pytest.fixture
def category_id(db):
    # Devuelve el id de una categoria a partir de su nombre y tipo
    def _category_id(name, type):
        category = (
            db.query(Category)
            .filter(Category.name == name, Category.type == type)
            .first()
        )

        return category.id

    return _category_id
