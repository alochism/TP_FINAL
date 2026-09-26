from datetime import datetime
from decimal import Decimal

from app.database import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="ARS",
        nullable=False
    )

    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=0,
        nullable=False
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )