"""Capa de tools para OpenClaw. Implementa docs/tools.md.

- Parametros y resultados siguen el contrato de docs/tools.md (nombres en ingles).
- Las cuentas y categorias llegan como NOMBRE y se resuelven solo entre las del usuario autenticado.
- Si falta o es ambiguo un dato requerido, NO se ejecuta nada: se responde needs_info.
- Se ejecuta reutilizando las rutas existentes (transactions / accounts): las reglas de negocio
  siguen en un solo lugar.
- Siempre responde HTTP 200 con envelope. Solo la autenticacion falla con 401/403.
"""
import datetime as dt
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Annotated
from zoneinfo import ZoneInfo

from app.database import get_db
from app.models import Account, Category, User
from app.routers import accounts as accounts_routes
from app.routers import transactions as tx_routes
from app.schemas.transaction import TransactionCreate
from app.security import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tools", tags=["Tools"])

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
DbDep = Annotated[Session, Depends(get_db)]
UserDep = Annotated[User, Depends(get_current_user)]


# ---------- helpers ----------

def _today() -> dt.date:
    return dt.datetime.now(TZ).date()


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.strip().lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _num(value):
    value = Decimal(str(value))
    return int(value) if value == value.to_integral_value() else float(value)


def _env(status, code=None, missing=None, options=None, data=None, hint=None):
    return {
        "status": status,
        "code": code,
        "missing_fields": missing or [],
        "options": options or {},
        "data": data or {},
        "message_hint": hint,
    }


def _match(name: str, items):
    """Devuelve (item, None) o (None, 'AMBIGUOUS' | 'NOT_FOUND')."""
    target = _norm(name)
    if not target:
        return None, "NOT_FOUND"
    found = [i for i in items if _norm(i.name) == target]
    found = found or [i for i in items if target in _norm(i.name)]
    if len(found) == 1:
        return found[0], None
    return None, ("AMBIGUOUS" if found else "NOT_FOUND")


def _accounts(db: Session, user: User):
    return (
        db.query(Account)
        .filter(Account.user_id == user.id, Account.active.is_(True))
        .all()
    )


def _categories(db: Session, kind: str | None = None):
    query = db.query(Category)
    if kind:
        query = query.filter(Category.type == kind)
    return query.all()


def _parse_date(value: str | None) -> dt.date | None:
    return dt.date.fromisoformat(value) if value else None


def _account_issue(err: str, accounts):
    code = "ACCOUNT_AMBIGUOUS" if err == "AMBIGUOUS" else "ACCOUNT_NOT_FOUND"
    return _env(
        "needs_info", code, ["account"],
        {"account": [a.name for a in accounts]},
        hint="Pregunta al usuario de que cuenta se trata.",
    )


def _category_issue(categories):
    return _env(
        "needs_info", "CATEGORY_UNRESOLVED", ["category"],
        {"category": [c.name for c in categories]},
        hint="Pregunta al usuario que categoria usar.",
    )


def _invalid_date():
    return _env("rejected", "INVALID_DATE", hint="La fecha debe ser valida, con formato AAAA-MM-DD.")


# ---------- escritura: create_expense / create_income ----------

class MovementIn(BaseModel):
    amount: float | int | str | None = None
    date: str | None = None
    category: str | None = None
    account: str | None = None
    description: str | None = Field(default=None, max_length=200)
    # Moneda mencionada por el usuario. En P0 solo se admite ARS
    currency: str | None = Field(default=None, max_length=10)


def _create(kind: str, body: MovementIn, db: Session, user: User):
    # 1) Rechazos: dato presente pero invalido
    if body.currency and _norm(body.currency) not in {"ars", "pesos", "peso", "$"}:
        return _env(
            "rejected", "UNSUPPORTED_CURRENCY",
            hint="Por ahora solo se registran movimientos en pesos argentinos (ARS). No se registro nada.",
        )

    amount = None
    if body.amount is not None:
        try:
            amount = Decimal(str(body.amount))
        except InvalidOperation:
            amount = Decimal(0)  # fuerza INVALID_AMOUNT
        if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
            return _env(
                "rejected", "INVALID_AMOUNT",
                hint="El monto debe ser un numero mayor a cero, con hasta 2 decimales.",
            )

    tx_date = None
    if body.date:
        try:
            tx_date = _parse_date(body.date)
        except ValueError:
            return _invalid_date()
        if tx_date > _today():
            return _env("rejected", "INVALID_DATE", hint="No se pueden registrar movimientos con fecha futura.")

    # 2) Datos requeridos faltantes o ambiguos: no se ejecuta nada, se pregunta
    accounts = _accounts(db, user)
    categories = _categories(db, "EXPENSE" if kind == "expense" else "INCOME")
    missing, options, code = [], {}, None

    if amount is None:
        missing.append("amount")
        code = "MISSING_AMOUNT"

    if tx_date is None:  # sin fecha mencionada: se registra con la fecha de hoy
        tx_date = _today()

    account = None
    if body.account:
        account, err = _match(body.account, accounts)
        err_code = {"AMBIGUOUS": "ACCOUNT_AMBIGUOUS", "NOT_FOUND": "ACCOUNT_NOT_FOUND"}.get(err)
    else:
        err_code = "MISSING_ACCOUNT"
    if account is None:
        missing.append("account")
        options["account"] = [a.name for a in accounts]
        code = code or err_code

    category = None
    if body.category:
        category, _ = _match(body.category, categories)
    if category is None:
        missing.append("category")
        options["category"] = [c.name for c in categories]
        code = code or "CATEGORY_UNRESOLVED"

    if missing:
        return _env(
            "needs_info", code, missing, options,
            hint="No se registro nada. Pedi al usuario solo los datos faltantes.",
        )

    # 3) Ejecucion: reutiliza las validaciones de las rutas existentes
    handler = tx_routes.create_expense if kind == "expense" else tx_routes.create_income
    try:
        tx = handler(
            transaction_data=TransactionCreate(
                account_id=account.id,
                category_id=category.id,
                amount=amount,
                date=tx_date,
                description=body.description,
            ),
            db=db,
            current_user=user,
        )
    except HTTPException as exc:
        return _env("rejected", "RULE_VIOLATION", hint=str(exc.detail))

    return _env("ok", data={
        "success": True,
        "transaction_id": tx.id,
        "message": "Gasto registrado correctamente" if kind == "expense" else "Ingreso registrado correctamente",
        # eco normalizado de lo registrado (nombres resueltos por el backend)
        "amount": _num(tx.amount),
        "date": tx_date.isoformat(),
        "account": account.name,
        "category": category.name,
    })


@router.post("/expense")
def tools_create_expense(body: MovementIn, db: DbDep, user: UserDep):
    return _create("expense", body, db, user)


@router.post("/income")
def tools_create_income(body: MovementIn, db: DbDep, user: UserDep):
    return _create("income", body, db, user)


# ---------- lectura ----------

@router.get("/balance")
def tools_balance(db: DbDep, user: UserDep, account: str | None = None):
    acc = None
    if account:
        accounts = _accounts(db, user)
        acc, err = _match(account, accounts)
        if err:
            return _account_issue(err, accounts)
    result = accounts_routes.get_balance(
        db=db, current_user=user, account_id=acc.id if acc else None
    )
    return _env("ok", data={
        "account": acc.name if acc else None,
        "currency": "ARS",
        "balance": _num(result["balance"]),
    })


@router.get("/transactions")
def tools_transactions(
    db: DbDep,
    user: UserDep,
    date_from: str | None = None,
    date_to: str | None = None,
    type_: str | None = Query(default=None, alias="type"),
    account: str | None = None,
    category: str | None = None,
    limit: int = 10,
):
    try:
        d_from, d_to = _parse_date(date_from), _parse_date(date_to)
    except ValueError:
        return _invalid_date()

    tx_type = None
    if type_:
        tx_type = {"EXPENSE": "EXPENSE", "GASTO": "EXPENSE", "INCOME": "INCOME", "INGRESO": "INCOME"}.get(
            _norm(type_).upper()
        )
        if tx_type is None:
            return _env("rejected", "INVALID_TYPE", hint="type debe ser EXPENSE o INCOME.")

    accounts = _accounts(db, user)
    account_id = None
    if account:
        acc, err = _match(account, accounts)
        if err:
            return _account_issue(err, accounts)
        account_id = acc.id

    categories = _categories(db)
    category_id = None
    if category:
        cat, _ = _match(category, categories)
        if cat is None:
            return _category_issue(categories)
        category_id = cat.id

    rows = tx_routes.get_transactions(
        db=db, current_user=user, date_from=d_from, date_to=d_to,
        type=tx_type, account_id=account_id, category_id=category_id,
    )
    rows = [t for t in rows if t.status == "ACTIVE"]  # los anulados no se informan
    acc_names = {a.id: a.name for a in accounts}
    cat_names = {c.id: c.name for c in categories}

    return _env("ok", data={
        "transactions": [
            {
                "id": t.id,
                "type": t.type,
                "amount": _num(t.amount),
                "date": t.date.isoformat(),
                "category": cat_names.get(t.category_id),
                "account": acc_names.get(t.account_id),
                "description": t.description,
            }
            for t in rows[: max(1, min(limit, 50))]
        ],
    })


@router.get("/expenses-by-category")
def tools_expenses_by_category(
    db: DbDep,
    user: UserDep,
    date_from: str | None = None,
    date_to: str | None = None,
    account: str | None = None,
):
    try:
        d_from, d_to = _parse_date(date_from), _parse_date(date_to)
    except ValueError:
        return _invalid_date()
    if d_from is None and d_to is None:  # por defecto: mes actual
        d_to = _today()
        d_from = d_to.replace(day=1)

    account_id = None
    if account:
        accounts = _accounts(db, user)
        acc, err = _match(account, accounts)
        if err:
            return _account_issue(err, accounts)
        account_id = acc.id

    rows = tx_routes.get_expenses_by_category(
        db=db, current_user=user, date_from=d_from, date_to=d_to, account_id=account_id
    )
    return _env("ok", data={
        "date_from": d_from.isoformat() if d_from else None,
        "date_to": d_to.isoformat() if d_to else None,
        "expenses": [{"category": r["category"], "amount": _num(r["total"])} for r in rows],
    })
