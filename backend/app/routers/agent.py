"""Capa de tools para el agente (OpenClaw). Implementa docs/tools.md.

- Recibe NOMBRES (cuenta, categoria) y los resuelve contra los datos del usuario autenticado.
- Detecta datos faltantes y responde con el envelope {status, code, ...}.
- Ejecuta reutilizando las rutas existentes (transactions / accounts), asi las
  validaciones de negocio siguen viviendo en un solo lugar.
- Siempre responde HTTP 200 con envelope. Solo la autenticacion falla con 401/403.
"""
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated
from zoneinfo import ZoneInfo

from app.database import get_db
from app.models import Account, Category, User
from app.routers import accounts as accounts_routes
from app.routers import transactions as tx_routes
from app.schemas.transaction import TransactionCreate
from app.security import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(prefix="/agent", tags=["Agent"])

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
DbDep = Annotated[Session, Depends(get_db)]
UserDep = Annotated[User, Depends(get_current_user)]


# ---------- helpers ----------

def _today() -> date:
    return datetime.now(TZ).date()


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.strip().lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


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


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _account_issue(err: str, accounts):
    code = "ACCOUNT_AMBIGUOUS" if err == "AMBIGUOUS" else "ACCOUNT_NOT_FOUND"
    return _env(
        "needs_info", code, ["cuenta"],
        {"cuenta": [a.name for a in accounts]},
        hint="Preguntale al usuario de que cuenta se trata.",
    )


def _category_issue(categories):
    return _env(
        "needs_info", "CATEGORY_UNRESOLVED", ["categoria"],
        {"categoria": [c.name for c in categories]},
        hint="Preguntale al usuario que categoria usar.",
    )


def _invalid_date():
    return _env("rejected", "INVALID_DATE", hint="La fecha debe ser valida, con formato AAAA-MM-DD.")


# ---------- escritura ----------

class MovementIn(BaseModel):
    monto: float | int | str | None = None
    cuenta: str | None = None
    categoria_sugerida: str | None = None
    fecha: str | None = None
    descripcion: str | None = Field(default=None, max_length=200)


def _create(kind: str, body: MovementIn, db: Session, user: User):
    # 1) Rechazos: dato presente pero invalido
    amount = None
    if body.monto is not None:
        try:
            amount = Decimal(str(body.monto))
        except InvalidOperation:
            amount = Decimal(0)  # fuerza INVALID_AMOUNT
        if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
            return _env(
                "rejected", "INVALID_AMOUNT",
                hint="El monto debe ser un numero mayor a cero, con hasta 2 decimales.",
            )

    try:
        tx_date = _parse_date(body.fecha) or _today()
    except ValueError:
        return _invalid_date()
    if tx_date > _today():
        return _env("rejected", "INVALID_DATE", hint="No se pueden registrar movimientos con fecha futura.")

    # 2) Datos faltantes o ambiguos: no se ejecuta nada, se pregunta
    accounts = _accounts(db, user)
    categories = _categories(db, "EXPENSE" if kind == "expense" else "INCOME")
    missing, options, code = [], {}, None

    if amount is None:
        missing.append("monto")
        code = "MISSING_AMOUNT"

    account = None
    if body.cuenta:
        account, err = _match(body.cuenta, accounts)
        err_code = {"AMBIGUOUS": "ACCOUNT_AMBIGUOUS", "NOT_FOUND": "ACCOUNT_NOT_FOUND"}.get(err)
    else:
        err_code = "MISSING_ACCOUNT"
    if account is None:
        missing.append("cuenta")
        options["cuenta"] = [a.name for a in accounts]
        code = code or err_code

    category = None
    if body.categoria_sugerida:
        category, _ = _match(body.categoria_sugerida, categories)
    if category is None:
        missing.append("categoria")
        options["categoria"] = [c.name for c in categories]
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
                description=body.descripcion,
            ),
            db=db,
            current_user=user,
        )
    except HTTPException as exc:
        return _env("rejected", "RULE_VIOLATION", hint=str(exc.detail))

    balance = accounts_routes.get_balance(db=db, current_user=user, account_id=account.id)["balance"]
    return _env("ok", data={
        "transaction_id": tx.id,
        "tipo": "gasto" if kind == "expense" else "ingreso",
        "monto": float(tx.amount),
        "cuenta": account.name,
        "categoria": category.name,
        "fecha": tx_date.isoformat(),
        "saldo_cuenta": float(balance),
    })


@router.post("/expense")
def agent_create_expense(body: MovementIn, db: DbDep, user: UserDep):
    return _create("expense", body, db, user)


@router.post("/income")
def agent_create_income(body: MovementIn, db: DbDep, user: UserDep):
    return _create("income", body, db, user)


# ---------- lectura ----------

@router.get("/balance")
def agent_balance(db: DbDep, user: UserDep, cuenta: str | None = None):
    account = None
    if cuenta:
        accounts = _accounts(db, user)
        account, err = _match(cuenta, accounts)
        if err:
            return _account_issue(err, accounts)
    result = accounts_routes.get_balance(
        db=db, current_user=user, account_id=account.id if account else None
    )
    return _env("ok", data={
        "cuenta": account.name if account else None,
        "balance": float(result["balance"]),
        "moneda": "ARS",
    })


@router.get("/transactions")
def agent_transactions(
    db: DbDep,
    user: UserDep,
    cuenta: str | None = None,
    categoria: str | None = None,
    tipo: str | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    limite: int = 10,
):
    try:
        d_from, d_to = _parse_date(fecha_desde), _parse_date(fecha_hasta)
    except ValueError:
        return _invalid_date()

    tx_type = None
    if tipo:
        tx_type = {"gasto": "EXPENSE", "ingreso": "INCOME"}.get(_norm(tipo))
        if tx_type is None:
            return _env("rejected", "INVALID_TYPE", hint="El tipo debe ser 'gasto' o 'ingreso'.")

    accounts = _accounts(db, user)
    account_id = None
    if cuenta:
        account, err = _match(cuenta, accounts)
        if err:
            return _account_issue(err, accounts)
        account_id = account.id

    categories = _categories(db)
    category_id = None
    if categoria:
        category, _ = _match(categoria, categories)
        if category is None:
            return _category_issue(categories)
        category_id = category.id

    rows = tx_routes.get_transactions(
        db=db, current_user=user, date_from=d_from, date_to=d_to,
        type=tx_type, account_id=account_id, category_id=category_id,
    )
    rows = [t for t in rows if t.status == "ACTIVE"]  # ver nota: la ruta original no filtra
    acc_names = {a.id: a.name for a in accounts}
    cat_names = {c.id: c.name for c in categories}

    return _env("ok", data={
        "total_resultados": len(rows),
        "movimientos": [
            {
                "id": t.id,
                "tipo": "gasto" if t.type == "EXPENSE" else "ingreso",
                "monto": float(t.amount),
                "cuenta": acc_names.get(t.account_id),
                "categoria": cat_names.get(t.category_id),
                "fecha": t.date.isoformat(),
                "descripcion": t.description,
            }
            for t in rows[: max(1, min(limite, 50))]
        ],
    })


@router.get("/expenses-by-category")
def agent_expenses_by_category(
    db: DbDep,
    user: UserDep,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    cuenta: str | None = None,
    categoria: str | None = None,
):
    try:
        d_from, d_to = _parse_date(fecha_desde), _parse_date(fecha_hasta)
    except ValueError:
        return _invalid_date()
    if d_from is None and d_to is None:  # por defecto: mes actual
        d_to = _today()
        d_from = d_to.replace(day=1)

    account_id = None
    if cuenta:
        accounts = _accounts(db, user)
        account, err = _match(cuenta, accounts)
        if err:
            return _account_issue(err, accounts)
        account_id = account.id

    rows = tx_routes.get_expenses_by_category(
        db=db, current_user=user, date_from=d_from, date_to=d_to, account_id=account_id
    )
    items = [{"categoria": r["category"], "total": float(r["total"])} for r in rows]

    if categoria:
        expense_categories = _categories(db, "EXPENSE")
        category, _ = _match(categoria, expense_categories)
        if category is None:
            return _category_issue(expense_categories)
        items = [i for i in items if i["categoria"] == category.name] or [
            {"categoria": category.name, "total": 0.0}
        ]

    return _env("ok", data={
        "periodo": {
            "desde": d_from.isoformat() if d_from else None,
            "hasta": d_to.isoformat() if d_to else None,
        },
        "categorias": items,
        "total_gastos": sum(i["total"] for i in items),
    })
