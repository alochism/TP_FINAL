from decimal import Decimal

from pydantic import BaseModel


class AccountCreate(BaseModel):
    name: str
    type: str
    currency: str = "ARS"
    initial_balance: Decimal = Decimal("0.00")


class AccountResponse(BaseModel):
    id: int
    name: str
    type: str
    currency: str
    initial_balance: Decimal
    active: bool

    model_config = {
        "from_attributes": True
    }