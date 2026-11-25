from datetime import date
from typing import Annotated

from app.database import get_db
from app.models import Account, Category, Transaction, User
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.security import get_current_user
from app.services.transaction_validation import (
    TransactionValidationError,
    validate_amount,
    validate_date,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


@router.post(
    "/expense",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_expense(
    transaction_data: TransactionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        amount = validate_amount(transaction_data.amount)
        movement_date = validate_date(transaction_data.date)
    except TransactionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message
        ) from exc

    account = db.get(Account, transaction_data.account_id)

    if (
        account is None
        or account.user_id != current_user.id
        or not account.active
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )

    category = db.get(Category, transaction_data.category_id)

    if category is None or category.type != "EXPENSE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Categoria de gasto invalida"
        )

    new_transaction = Transaction(
        account_id=account.id,
        category_id=category.id,
        type="EXPENSE",
        amount=amount,
        date=movement_date,
        description=transaction_data.description,
        status="ACTIVE"
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction


@router.post(
    "/income",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_income(
    transaction_data: TransactionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        amount = validate_amount(transaction_data.amount)
        movement_date = validate_date(transaction_data.date)
    except TransactionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message
        ) from exc

    account = db.get(Account, transaction_data.account_id)

    if (
        account is None
        or account.user_id != current_user.id
        or not account.active
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )

    category = db.get(Category, transaction_data.category_id)

    if category is None or category.type != "INCOME":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Categoria de ingreso invalida"
        )

    new_transaction = Transaction(
        account_id=account.id,
        category_id=category.id,
        type="INCOME",
        amount=amount,
        date=movement_date,
        description=transaction_data.description,
        status="ACTIVE"
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction


@router.get(
    "",
    response_model=list[TransactionResponse]
)
def get_transactions(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    date_from: date | None = None,
    date_to: date | None = None,
    type: str | None = None,
    account_id: int | None = None,
    category_id: int | None = None
):
    query = (
        db.query(Transaction)
        .join(Account)
        .filter(Account.user_id == current_user.id)
    )

    if date_from is not None:
        query = query.filter(Transaction.date >= date_from)

    if date_to is not None:
        query = query.filter(Transaction.date <= date_to)

    if type is not None:
        transaction_type = type.upper()

        if transaction_type not in {"EXPENSE", "INCOME"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de transaccion invalido"
            )

        query = query.filter(Transaction.type == transaction_type)

    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)

    return (
        query
        .order_by(Transaction.date.desc())
        .all()
    )

@router.patch(
    "/{transaction_id}/void",
    response_model=TransactionResponse
)
def void_transaction(
    transaction_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    # Anulacion logica: el movimiento se conserva con estado VOIDED
    # y deja de contar para saldos y consultas
    transaction = db.get(Transaction, transaction_id)
    account = db.get(Account, transaction.account_id) if transaction else None

    if account is None or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimiento no encontrado"
        )

    if transaction.status == "VOIDED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El movimiento ya esta anulado"
        )

    transaction.status = "VOIDED"
    db.commit()
    db.refresh(transaction)

    return transaction


@router.get("/expenses-by-category")
def get_expenses_by_category(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    date_from: date | None = None,
    date_to: date | None = None,
    account_id: int | None = None
):
    query = (
        db.query(
            Category.name.label("category"),
            func.sum(Transaction.amount).label("total")
        )
        .join(
            Transaction,
            Transaction.category_id == Category.id
        )
        .join(
            Account,
            Transaction.account_id == Account.id
        )
        .filter(
            Account.user_id == current_user.id,
            Transaction.type == "EXPENSE",
            Transaction.status == "ACTIVE"
        )
    )

    if date_from is not None:
        query = query.filter(Transaction.date >= date_from)

    if date_to is not None:
        query = query.filter(Transaction.date <= date_to)

    if account_id is not None:
        account = db.get(Account, account_id)

        if (
            account is None
            or account.user_id != current_user.id
            or not account.active
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta no encontrada"
            )

        query = query.filter(Transaction.account_id == account_id)

    results = (
        query
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    return [
        {
            "category": result.category,
            "total": result.total
        }
        for result in results
    ]