from fastapi import FastAPI

app = FastAPI(
    title="Plataforma Conversacional de Finanzas Personales"
)


@app.get("/")
def root():
    return {"message": "Backend funcionando correctamente"}