from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response

from app import banco, camadas, respostas
from app.config import origens_cors
from app.respostas import Bbox

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

# GZip: comprime as respostas grandes (a camada de risco tem ~1,8 MB de texto)
# para quem aceita (todo navegador). Respostas pequenas, como a /saude, vão
# sem comprimir.
app.add_middleware(GZipMiddleware, minimum_size=1000)


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


# ---------------------------------------------------------------- camadas

RESPOSTAS_CAMADA = respostas.respostas(
    "FeatureCollection no mesmo formato dos arquivos de `docs/dados/`."
)


def responder_camada(nome: str, bbox: str | None) -> Response:
    """Valida o bbox, lê a camada no banco e devolve o GeoJSON."""
    retangulo = respostas.retangulo(bbox)
    try:
        return respostas.geojson(camadas.camada_geojson(nome, retangulo))
    except camadas.CamadaIndisponivel:
        return respostas.indisponivel()


@app.get(
    "/camadas/risco",
    tags=["camadas"],
    summary="Manchas de risco de enchente",
    response_class=Response,
    responses=RESPOSTAS_CAMADA,
)
def camada_risco(bbox: Bbox = None):
    """Manchas de risco de enchente calculadas pelo HAND (altura acima da
    drenagem mais próxima), com a classe de cada mancha (`alto`, `medio`).

    A fonte do cálculo vem no topo da resposta (`fonte`).

    Exemplo, só a área piloto: `/camadas/risco?bbox=-47.455,-23.478,-47.439,-23.463`
    """
    return responder_camada("risco", bbox)


@app.get(
    "/camadas/registros",
    tags=["camadas"],
    summary="Registros de alagamento por rua",
    response_class=Response,
    responses=RESPOSTAS_CAMADA,
)
def camada_registros(bbox: Bbox = None):
    """Registros de alagamento e inundação da Defesa Civil, somados por rua:
    um ponto por rua, com o total de registros (`registros`) e quantos são
    alagamentos, inundações e relatórios.

    Mostra a **concentração por rua**, não o endereço exato.

    Exemplo, só a área piloto: `/camadas/registros?bbox=-47.455,-23.478,-47.439,-23.463`
    """
    return responder_camada("registros", bbox)
