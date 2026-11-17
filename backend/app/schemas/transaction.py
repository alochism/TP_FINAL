from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TransactionCreate(BaseModel):
    account_id: int
    category_id: int
    amount: Decimal
    date: date
    description: str | None = None


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    category_id: int
    type: str
    amount: Decimal
    date: date
    description: str | None
    status: str

    model_config = {
        "from_attributes": True
    }