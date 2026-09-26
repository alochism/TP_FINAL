from app.database import get_db
from app.models import Account, User
from app.schemas.account import AccountCreate, AccountResponse
from app.security import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"]
)


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED
)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed_types = {"CASH", "BANK", "WALLET"}

    if account_data.type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de cuenta invalido"
        )

    if account_data.currency.upper() != "ARS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Por el momento solo se admite la moneda ARS"
        )

    new_account = Account(
        user_id=current_user.id,
        name=account_data.name,
        type=account_data.type,
        currency=account_data.currency.upper(),
        initial_balance=account_data.initial_balance
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account


@router.get(
    "",
    response_model=list[AccountResponse]
)
def get_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Account)
        .filter(
            Account.user_id == current_user.id,
            Account.active.is_(True)
        )
        .all()
    )