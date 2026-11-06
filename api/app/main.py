from fastapi import FastAPI

app = FastAPI(
    title="CityShield API",
    description="Camadas de risco de enchente e soluções verdes para Sorocaba/SP.",
    version="0.1.0",
)


@app.get("/saude")
def saude():
    """Confere se a API está no ar."""
    return {"status": "ok"}
