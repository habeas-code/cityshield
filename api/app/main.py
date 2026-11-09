from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import banco
from app.config import origens_cors

app = FastAPI(
    title="CityShield API",
    description="Camadas de risco de enchente e soluções verdes para Sorocaba/SP.",
    version="0.1.0",
)

# CORS: diz ao navegador quais sites podem ler as respostas da API.
# Só os endereços de CORS_ORIGINS (o site no GitHub Pages e o localhost),
# e só GET, porque o site só lê (D7).
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_cors(),
    allow_methods=["GET"],
)


@app.get(
    "/saude",
    responses={503: {"description": "O banco não respondeu"}},
)
def saude():
    """Confere se a API e o banco estão no ar.

    Faz uma consulta mínima no banco (SELECT 1). O Render e o ping do GitHub
    Actions usam esta rota: se o banco cair, ela tem que dizer (503).
    """
    if banco.banco_responde():
        return {"status": "ok", "banco": "ok"}
    return JSONResponse(status_code=503, content={"status": "erro", "banco": "fora do ar"})
