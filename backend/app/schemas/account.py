
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class AccountCreate(BaseModel):
    name: str
    type: str
    currency: str = "ARS"
    initial_balance: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=15,
        decimal_places=2
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()

        if not name:
            raise ValueError("El nombre de la cuenta no puede estar vacio")

        if len(name) > 100:
            raise ValueError("El nombre no puede superar 100 caracteres")

        return name



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