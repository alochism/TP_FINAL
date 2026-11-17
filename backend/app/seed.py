from app.database import SessionLocal
from app.models import Category

CATEGORIES = [
    # Gastos
    {"name": "Alimentacion", "type": "EXPENSE"},
    {"name": "Transporte", "type": "EXPENSE"},
    {"name": "Servicios", "type": "EXPENSE"},
    {"name": "Vivienda", "type": "EXPENSE"},
    {"name": "Salud", "type": "EXPENSE"},
    {"name": "Educacion", "type": "EXPENSE"},
    {"name": "Entretenimiento", "type": "EXPENSE"},
    {"name": "Compras", "type": "EXPENSE"},
    {"name": "Otros", "type": "EXPENSE"},

    # Ingresos
    {"name": "Sueldo", "type": "INCOME"},
    {"name": "Honorarios", "type": "INCOME"},
    {"name": "Inversiones", "type": "INCOME"},
    {"name": "Otros", "type": "INCOME"},
]


def seed_categories():
    db = SessionLocal()

    try:
        for category_data in CATEGORIES:
            existing_category = (
                db.query(Category)
                .filter(
                    Category.name == category_data["name"],
                    Category.type == category_data["type"]
                )
                .first()
            )

            if existing_category is None:
                category = Category(**category_data)
                db.add(category)

        db.commit()
        print("Categorias cargadas correctamente")

    finally:
        db.close()


if __name__ == "__main__":
    seed_categories()