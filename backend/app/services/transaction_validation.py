
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")
MAX_AMOUNT = Decimal("9999999999999.99")


class TransactionValidationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def today_local() -> date:
    return datetime.now(BUENOS_AIRES).date()


def validate_amount(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise TransactionValidationError(
            "INVALID_AMOUNT",
            "El monto debe ser mayor a cero, con hasta 2 decimales."
        ) from exc

    if (
        not amount.is_finite()
        or amount <= 0
        or amount.as_tuple().exponent < -2
        or amount > MAX_AMOUNT
    ):
        raise TransactionValidationError(
            "INVALID_AMOUNT",
            "El monto debe ser mayor a cero, con hasta 2 decimales."
        )

    return amount


def validate_date(value: date) -> date:
    if value > today_local():
        raise TransactionValidationError(
            "INVALID_DATE",
            "No se pueden registrar movimientos con fecha futura."
        )

    return value
