from datetime import datetime, timezone

from app.database import Base
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditLog(Base):
    """Registro de cada mensaje procesado por el chat.

    Permite reconstruir que escribio el usuario, que interpreto la IA,
    que decidio el backend y que movimiento se genero.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_now,
        nullable=False
    )

    # Mensaje original del usuario
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Lista de operaciones solicitadas por la IA con sus parametros
    # y la decision del backend (status, code, missing_fields)
    actions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Movimiento generado, si la operacion se ejecuto
    transaction_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    reply: Mapped[str] = mapped_column(Text, nullable=False)

    # True si el proveedor de IA no respondio o respondio algo invalido
    llm_error: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
