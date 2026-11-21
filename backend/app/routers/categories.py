from typing import Annotated

from app.database import get_db
from app.models import Category, User
from app.schemas.category import CategoryResponse
from app.security import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


# Devuelve las categorias predefinidas del sistema.
# Permite que el frontend y el agente obtengan los identificadores reales
# en lugar de depender del orden en que fueron cargadas por el seed
@router.get(
    "",
    response_model=list[CategoryResponse]
)
def get_categories(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    type: str | None = None
):
    query = db.query(Category)

    if type is not None:
        category_type = type.upper()

        if category_type not in {"EXPENSE", "INCOME"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de categoria invalido"
            )

        query = query.filter(Category.type == category_type)

    return (
        query
        .order_by(Category.type, Category.name)
        .all()
    )
