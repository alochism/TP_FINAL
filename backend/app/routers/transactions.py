from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Category, Transaction, User
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.security import get_current_user


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El monto debe ser mayor a cero"
        )

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
        amount=transaction_data.amount,
        date=transaction_data.date,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El monto debe ser mayor a cero"
        )

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
        amount=transaction_data.amount,
        date=transaction_data.date,
        description=transaction_data.description,
        status="ACTIVE"
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction