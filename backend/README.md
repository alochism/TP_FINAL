# Backend — Plataforma Conversacional de Finanzas Personales

Backend desarrollado con **Python y FastAPI**, encargado de gestionar las operaciones financieras y la integración con Gemini.

## Responsabilidades

- Autenticación y autorización mediante JWT.
- Administración de usuarios, cuentas y categorías.
- Registro, consulta y anulación de movimientos.
- Validación de importes, fechas y permisos.
- Cálculo de saldos y consultas financieras.
- Procesamiento conversacional mediante `POST /chat`.
- Ejecución controlada de herramientas solicitadas por Gemini.
- Auditoría de interacciones conversacionales.

## Tecnologías

- Python y FastAPI.
- PostgreSQL y SQLAlchemy.
- Alembic para migraciones.
- Pydantic para validación.
- Gemini mediante una API compatible con OpenAI.
- pytest para pruebas automatizadas.

## Estructura

```text
app/
├── agent/       # Integración con Gemini y herramientas
├── models/      # Modelos de base de datos
├── routers/     # Endpoints REST y conversacionales
├── schemas/     # Validación de datos
└── services/    # Reglas y validaciones compartidas

alembic/         # Migraciones
evaluacion/      # Evaluación de lenguaje natural
tests/           # Pruebas automatizadas
```

## Ejecución local

Desde `backend/`, con las dependencias instaladas y el archivo `.env` configurado:

```powershell
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

Documentación de la API:

`http://127.0.0.1:8000/docs`

## Pruebas

```powershell
pytest
```

Última ejecución verificada: **72 pruebas aprobadas**.

## Documentación

La instalación completa, configuración de variables de entorno y arquitectura general se encuentran en el [README principal](../README.md).

Los contratos de las herramientas conversacionales están documentados en [docs/tools.md](../docs/tools.md).

> El agente interpreta. El backend decide.