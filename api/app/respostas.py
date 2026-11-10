"""Peças comuns das rotas que leem o banco: respostas, bbox e documentação.

Usadas pelas camadas (#11) e pelas áreas e cenário (#18), para que 503,
cache e bbox funcionem igual em todas as rotas.
"""

from typing import Annotated

from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse, Response

from app.bbox import BboxInvalido, ler_bbox

GEOJSON = "application/geo+json"

# Os dados só mudam quando o pipeline e a carga rodam de novo (D7): o
# navegador pode reaproveitar a resposta por 5 minutos sem pedir outra vez.
CACHE = "public, max-age=300"

ERRO_503 = {"erro": "camada indisponível, tente de novo em instantes"}


def geojson(texto: str) -> Response:
    """Resposta 200 com o GeoJSON montado no banco, já com cache."""
    return Response(content=texto, media_type=GEOJSON, headers={"Cache-Control": CACHE})


def json_com_cache(conteudo) -> JSONResponse:
    """Resposta 200 em JSON comum, com o mesmo cache das camadas."""
    return JSONResponse(content=conteudo, headers={"Cache-Control": CACHE})


def indisponivel() -> JSONResponse:
    """503 simples: sem detalhe técnico e sem ficar guardado no navegador."""
    return JSONResponse(status_code=503, content=ERRO_503, headers={"Cache-Control": "no-store"})


def retangulo(bbox: str | None) -> tuple[float, float, float, float] | None:
    """Lê o bbox do pedido; se for inválido, responde 422 com o motivo."""
    if bbox is None:
        return None
    try:
        return ler_bbox(bbox)
    except BboxInvalido as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from None


Bbox = Annotated[
    str | None,
    Query(
        description=(
            "Retângulo da área visível do mapa: `xmin,ymin,xmax,ymax` "
            "(oeste, sul, leste, norte), em graus de longitude e latitude "
            "(SRID 4326). Devolve só as feições que encostam nele. "
            "Sem bbox, devolve tudo, igual ao arquivo de `docs/dados/`."
        ),
        examples=["-47.455,-23.478,-47.439,-23.463"],
    ),
]


def respostas(descricao_200: str, tipo_200: str = GEOJSON, extra: dict | None = None) -> dict:
    """Respostas documentadas no /docs: 200, 422 e 503 (e outras, se houver)."""
    return {
        200: {"description": descricao_200, "content": {tipo_200: {}}},
        422: {
            "description": "Parâmetro inválido. A mensagem diz o motivo.",
            "content": {
                "application/json": {"example": {"detail": "latitude do bbox fora de -90 a 90."}}
            },
        },
        503: {
            "description": "O banco não respondeu. O site usa os arquivos estáticos (D10).",
            "content": {"application/json": {"example": ERRO_503}},
        },
        **(extra or {}),
    }
