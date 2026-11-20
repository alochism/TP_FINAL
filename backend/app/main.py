import os

from app.routers.accounts import router as accounts_router
from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.chat import router as chat_router
from app.routers.tools import router as tools_router
from app.routers.transactions import router as transactions_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Plataforma Conversacional de Finanzas Personales"
)

# Origenes del frontend habilitados (separados por coma).
# En desarrollo no hace falta: Vite reenvia /api al backend.
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(tools_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"message": "Backend funcionando correctamente"}
