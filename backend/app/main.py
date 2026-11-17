from app.routers.accounts import router as accounts_router
from app.routers.auth import router as auth_router
from app.routers.transactions import router as transactions_router
from app.routers.agent import router as agent_router
from fastapi import FastAPI

app = FastAPI(
    title="Plataforma Conversacional de Finanzas Personales"
)

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(agent.router)


@app.get("/")
def root():
    return {"message": "Backend funcionando correctamente"}