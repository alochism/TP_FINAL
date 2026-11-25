
import pytest

from app.routers.chat import HistoryItem, _category_needs_confirmation


@pytest.mark.parametrize(
    "message, category, expected",
    [
        ("Me entraron 50k en Mercado Pago", "Otros", True),
        ("Me entraron 50k en Mercado Pago", "Sueldo", True),
        ("Cobré 50k de sueldo en Mercado Pago", "Sueldo", False),
        ("Me pagaron 50k de honorarios", "Honorarios", False),
        ("Recibí 50k de inversiones", "Inversiones", False),
        ("Me entraron 50k en Mercado Pago, ponelo en Otros", "Otros", False),
    ],
)
def test_income_category_confirmation(message, category, expected):
    result = _category_needs_confirmation(
        message,
        category,
        tool_name="create_income",
    )
    assert result is expected


def test_income_category_clarification():
    history = [
        HistoryItem(
            role="user",
            content="Me entraron 50k en Mercado Pago",
        ),
        HistoryItem(
            role="assistant",
            content="¿Qué categoría le ponemos a este ingreso?",
        ),
    ]

    result = _category_needs_confirmation(
        "Otros",
        "Otros",
        tool_name="create_income",
        history=history,
    )

    assert result is False