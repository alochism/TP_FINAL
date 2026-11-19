"""corrige tildes en nombres de categorias

Revision ID: 3b8d1c4e9a72
Revises: 7f2e6b6bb95e
Create Date: 2026-11-18 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '3b8d1c4e9a72'
down_revision: Union[str, Sequence[str], None] = '7f2e6b6bb95e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Nombres originales y corregidos. Solo cambia el texto visible:
# los identificadores se mantienen, por lo que los movimientos ya registrados no se ven afectados
RENAMES = [
    ("Alimentacion", "Alimentación"),
    ("Educacion", "Educación"),
]


def upgrade() -> None:
    """Upgrade schema."""
    for old_name, new_name in RENAMES:
        op.execute(
            f"UPDATE categories SET name = '{new_name}' WHERE name = '{old_name}'"
        )


def downgrade() -> None:
    """Downgrade schema."""
    for old_name, new_name in RENAMES:
        op.execute(
            f"UPDATE categories SET name = '{old_name}' WHERE name = '{new_name}'"
        )
