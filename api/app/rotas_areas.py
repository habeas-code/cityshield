"""Rotas das áreas candidatas (#18): /areas e /areas/{id}."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import Response

from app import areas, respostas
from app.camadas import CamadaIndisponivel
from app.respostas import Bbox

rotas = APIRouter(tags=["áreas e cenário"])

CODIGOS = ", ".join(areas.SOLUCOES)


def solucao_valida(solucao: str | None) -> str | None:
    if solucao is not None and solucao not in areas.SOLUCOES:
        raise HTTPException(status_code=422, detail=f"solucao desconhecida: use {CODIGOS}.")
    return solucao


@rotas.get(
    "/areas",
    summary="Áreas candidatas, na ordem da fila",
    response_class=Response,
    responses=respostas.respostas(
        "FeatureCollection no mesmo formato do `recomendacoes.geojson`, na ordem da "
        "`posicao`, com fonte, área, aviso, método e parâmetros no topo."
    ),
)
def listar_areas(
    bbox: Bbox = None,
    solucao: Annotated[
        str | None,
        Query(
            description=f"Só as áreas desta solução. Um destes códigos: {CODIGOS}.",
            examples=["jardim_chuva"],
        ),
    ] = None,
):
    """Áreas candidatas a solução verde na área piloto, da mais indicada
    (`posicao` 1) para a menos indicada, com a solução escolhida, a nota de
    prioridade (0 a 100), o volume de água e o motivo.

    São **áreas candidatas a estudo, não terrenos disponíveis** (veja `aviso`
    no topo da resposta).

    Exemplos:
    - todas: `/areas`
    - só jardins de chuva: `/areas?solucao=jardim_chuva`
    - só na área visível do mapa: `/areas?bbox=-47.455,-23.478,-47.439,-23.463`
    """
    retangulo = respostas.retangulo(bbox)
    solucao = solucao_valida(solucao)
    try:
        return respostas.geojson(areas.areas_geojson(retangulo, solucao))
    except CamadaIndisponivel:
        return respostas.indisponivel()


@rotas.get(
    "/areas/{id_area}",
    summary="Ficha de uma área",
    response_class=Response,
    responses=respostas.respostas(
        "Uma Feature no mesmo formato das feições do `recomendacoes.geojson`.",
        extra={
            404: {
                "description": "Não há área com esse id.",
                "content": {
                    "application/json": {
                        "example": {"detail": "área way-1 não encontrada. Veja os ids em /areas."}
                    }
                },
            }
        },
    ),
)
def ficha_da_area(
    id_area: Annotated[
        str,
        Path(
            description=(
                "id fixo da área, vindo do OpenStreetMap (`way-`, `node-` ou "
                "`relation-` e o número). Use este, e não a `posicao`, que muda "
                "quando os parâmetros mudam."
            ),
            examples=["way-48448685"],
        ),
    ],
):
    """Uma área candidata, com tudo o que a ficha do site mostra: solução,
    motivo, nota e os três fatores dela, volume de água com a conta e a
    fonte, e avisos de projeto.

    Exemplo: `/areas/way-48448685` (Parque das Águas, 1º da fila)
    """
    if not areas.FORMATO_ID.fullmatch(id_area):
        raise HTTPException(
            status_code=422,
            detail="id inválido: use o id do OpenStreetMap, como way-48448685.",
        )
    try:
        feicao = areas.area_geojson(id_area)
    except CamadaIndisponivel:
        return respostas.indisponivel()
    if feicao is None:
        raise HTTPException(
            status_code=404, detail=f"área {id_area} não encontrada. Veja os ids em /areas."
        )
    return respostas.geojson(feicao)
