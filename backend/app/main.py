from app.routers.accounts import router as accounts_router
from app.routers.auth import router as auth_router
from fastapi import FastAPI

app = FastAPI(
    title="Plataforma Conversacional de Finanzas Personales"
)

app.include_router(auth_router)
app.include_router(accounts_router)


@app.get("/")
def root():
    return {"message": "Backend funcionando correctamente"}