"""Rotas das áreas candidatas e do cenário (#18): /areas, /areas/{id} e /cenario."""

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import JSONResponse, Response

from app import areas, cenario, respostas
from app.camadas import CamadaIndisponivel
from app.respostas import Bbox

log = logging.getLogger(__name__)

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


# ---------------------------------------------------------------- cenário

# Limites da chuva que a API aceita (o site usa de 10 a 120 mm). São limites
# da entrada, não números da conta: esses vêm todos de camadas_meta.
CHUVA_MIN_MM, CHUVA_MAX_MM = 1, 300

# Exemplo do /docs: saída real de /cenario?chuva_mm=50 com os dados de hoje
# (volumes encurtados para 2 casas, premissas resumidas).
EXEMPLO_CENARIO = {
    "chuva_mm": 50.0,
    "filtros": {"solucoes": list(areas.SOLUCOES), "nota_minima": 0},
    "n_areas": 44,
    "chega_m3": 6686.45,
    "retida_m3": 2937.43,
    "segue_m3": 3749.02,
    "retido_pct": 43.93,
    "por_solucao": {
        "jardim_chuva": {"n": 31, "chega_m3": 4342.2, "retida_m3": 1302.66},
        "piso_permeavel": {"n": 7, "chega_m3": 1005.6, "retida_m3": 1005.6},
        "telhado_verde": {"n": 6, "chega_m3": 1338.65, "retida_m3": 629.17},
    },
    "parques": {
        "n": 4,
        "capacidade_m3": 131691.0,
        "observacao": "Capacidade fixa: não muda com a chuva e não entra na conta de antes e depois.",
    },
    "premissas": {
        "telhado_verde": {
            "conta": "chega = área × chuva; retida = chega × retencao",
            "retencao": 0.47,
            "fonte": "Vacari et al., 2019, E&S Engineering and Science, UFMT",
        },
    },
    "area": "raio de 800 m em torno de -23.4702, -47.4472",
    "aviso": "Áreas candidatas a estudo, não terrenos disponíveis. Mapeamento de prédios no OSM é parcial.",
    "metodo": "docs/recomendacoes.md",
}


def solucoes_validas(texto: str | None) -> tuple[str, ...]:
    if texto is None:
        return areas.SOLUCOES
    pedidas = {s.strip() for s in texto.split(",") if s.strip()}
    desconhecidas = sorted(pedidas - set(areas.SOLUCOES))
    if not pedidas or desconhecidas:
        raise HTTPException(
            status_code=422,
            detail=f"solucoes desconhecidas ({', '.join(desconhecidas) or 'vazio'}): use {CODIGOS}.",
        )
    return tuple(s for s in areas.SOLUCOES if s in pedidas)


RESPOSTAS_CENARIO = respostas.respostas(
    "Água que chega, retida e que segue para a rua, com as premissas e as fontes.",
    tipo_200="application/json",
    extra={
        500: {
            "description": "Falta um parâmetro da conta no banco (carga desatualizada).",
            "content": {
                "application/json": {
                    "example": {"erro": "cenário indisponível: parâmetros incompletos no banco"}
                }
            },
        }
    },
)
RESPOSTAS_CENARIO[200]["content"]["application/json"]["example"] = EXEMPLO_CENARIO


@rotas.get(
    "/cenario",
    summary="Cenário antes e depois para uma chuva",
    responses=RESPOSTAS_CENARIO,
)
def cenario_antes_depois(
    chuva_mm: Annotated[
        float,
        Query(
            description=f"Chuva em milímetros, de {CHUVA_MIN_MM} a {CHUVA_MAX_MM}.",
            examples=[50],
        ),
    ],
    solucoes: Annotated[
        str | None,
        Query(
            description=(
                "Soluções que entram, separadas por vírgula. Sem este parâmetro, "
                f"entram todas. Códigos: {CODIGOS}."
            ),
            examples=["jardim_chuva,piso_permeavel"],
        ),
    ] = None,
    nota_minima: Annotated[
        int,
        Query(
            description=(
                "Só as áreas com nota de prioridade a partir desta (0 a 100). "
                "Com 10, fica igual ao \"só prioridade média ou alta\" do site."
            ),
            examples=[10],
        ),
    ] = 0,
):
    """Quanto da chuva vai para a rua **antes** e **depois** das soluções
    verdes na área piloto: a mesma conta da aba Simulação do site
    (docs/recomendacoes.md, "Cenário antes e depois").

    - `chega_m3`: água que cai nas áreas escolhidas (antes);
    - `retida_m3`: o que as soluções seguram;
    - `segue_m3`: o que ainda vai para a rua (depois);
    - `por_solucao`: o mesmo, separado por solução;
    - `parques`: à parte, com a capacidade, que não muda com a chuva e
      não entra na conta;
    - `premissas`: cada valor usado na conta, com a fonte.

    Os volumes vêm sem arredondar: arredonde só na hora de mostrar.

    Exemplos:
    - `/cenario?chuva_mm=50`
    - `/cenario?chuva_mm=120&solucoes=jardim_chuva,piso_permeavel&nota_minima=10`
    """
    if not CHUVA_MIN_MM <= chuva_mm <= CHUVA_MAX_MM:  # também recusa nan e inf
        raise HTTPException(
            status_code=422,
            detail=f"chuva_mm tem que ficar entre {CHUVA_MIN_MM} e {CHUVA_MAX_MM} mm.",
        )
    if not 0 <= nota_minima <= 100:
        raise HTTPException(status_code=422, detail="nota_minima tem que ficar entre 0 e 100.")
    escolhidas = solucoes_validas(solucoes)

    try:
        dados = areas.dados_cenario()
    except CamadaIndisponivel:
        return respostas.indisponivel()
    try:
        resultado = cenario.calcular_cenario(
            dados["areas"], dados["meta"] or {}, chuva_mm, escolhidas, nota_minima
        )
    except cenario.ParametrosIncompletos as erro:
        log.error("Cenário sem parâmetros: %s", erro)  # o detalhe fica só no log
        return JSONResponse(
            status_code=500,
            content={"erro": "cenário indisponível: parâmetros incompletos no banco"},
            headers={"Cache-Control": "no-store"},
        )
    return respostas.json_com_cache(resultado)
