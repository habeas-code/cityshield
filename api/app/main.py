from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response

from app import banco, camadas
from app.bbox import BboxInvalido, ler_bbox
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

GEOJSON = "application/geo+json"

# As camadas só mudam quando o pipeline e a carga rodam de novo (D7): o
# navegador pode reaproveitar a resposta por 5 minutos sem pedir outra vez.
CACHE_CAMADAS = "public, max-age=300"

Bbox = Annotated[
    str | None,
    Query(
        description=(
            "Retângulo da área visível do mapa: `xmin,ymin,xmax,ymax` "
            "(oeste, sul, leste, norte), em graus de longitude e latitude "
            "(SRID 4326). Devolve só as feições que encostam nele. "
            "Sem bbox, devolve a camada inteira, igual ao arquivo de `docs/dados/`."
        ),
        examples=["-47.455,-23.478,-47.439,-23.463"],
    ),
]

RESPOSTAS = {
    200: {
        "description": "FeatureCollection no mesmo formato dos arquivos de `docs/dados/`.",
        "content": {GEOJSON: {}},
    },
    422: {
        "description": "bbox inválido. A mensagem diz o motivo.",
        "content": {
            "application/json": {
                "example": {"detail": "latitude do bbox fora de -90 a 90."}
            }
        },
    },
    503: {
        "description": "O banco não respondeu. O site usa os arquivos estáticos (D10).",
        "content": {
            "application/json": {
                "example": {"erro": "camada indisponível, tente de novo em instantes"}
            }
        },
    },
}


def responder_camada(nome: str, bbox: str | None) -> Response:
    """Valida o bbox, lê a camada no banco e devolve o GeoJSON."""
    try:
        retangulo = ler_bbox(bbox) if bbox is not None else None
    except BboxInvalido as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from None

    try:
        geojson = camadas.camada_geojson(nome, retangulo)
    except camadas.CamadaIndisponivel:
        return JSONResponse(
            status_code=503,
            content={"erro": "camada indisponível, tente de novo em instantes"},
            headers={"Cache-Control": "no-store"},  # erro não fica guardado no navegador
        )
    return Response(
        content=geojson, media_type=GEOJSON, headers={"Cache-Control": CACHE_CAMADAS}
    )


@app.get(
    "/camadas/risco",
    tags=["camadas"],
    summary="Manchas de risco de enchente",
    response_class=Response,
    responses=RESPOSTAS,
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
    responses=RESPOSTAS,
)
def camada_registros(bbox: Bbox = None):
    """Registros de alagamento e inundação da Defesa Civil, somados por rua:
    um ponto por rua, com o total de registros (`registros`) e quantos são
    alagamentos, inundações e relatórios.

    Mostra a **concentração por rua**, não o endereço exato.

    Exemplo, só a área piloto: `/camadas/registros?bbox=-47.455,-23.478,-47.439,-23.463`
    """
    return responder_camada("registros", bbox)
