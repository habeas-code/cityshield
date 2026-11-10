"""Conta do cenário antes e depois (#18).

A mesma conta da aba Simulação do site (docs/mapa.html, aguaArea) e de
pipeline/pipeline/volumes.py, descrita em docs/recomendacoes.md, "Cenário
antes e depois". Para cada área de jardim, piso ou telhado, com chuva de P mm:

    Piso permeável   chega = área × P      retida = área × mín(P, capacidade)
    Telhado verde    chega = área × P      retida = área × P × retenção
    Jardim de chuva  jardim = fração × área
                     chega = jardim × área_que_escoa × P
                     retida = mín(chega, jardim × lâmina)

Antes = soma do que chega; depois = antes − retida. Os parques ficam à parte,
com a capacidade (volume_m3), que não muda com a chuva e não entra na conta.

Nenhum número da conta está escrito aqui: todos vêm de camadas_meta →
parametros, que o pipeline grava. Assim pipeline, site e API usam sempre os
mesmos valores.

Os volumes (m³) e a porcentagem saem sem arredondar: quem mostra arredonda
uma vez, como o site. Arredondar aqui e de novo na tela pode mudar o último
algarismo (16047,48 → 16047,5 → 16048, e não 16047).

Funções puras: não leem banco nem rede, então os testes conferem a conta
direto com a tabela de docs/recomendacoes.md.
"""

from app.areas import SOLUCOES

# Soluções que entram na conta de antes e depois (o parque fica à parte).
NA_CONTA = ("jardim_chuva", "piso_permeavel", "telhado_verde")


class ParametrosIncompletos(Exception):
    """Falta um parâmetro da conta em camadas_meta (a carga está velha?)."""


def _parametro(parametros: dict, nome: str):
    try:
        return parametros[nome]
    except KeyError:
        raise ParametrosIncompletos(f"falta o parâmetro {nome} em camadas_meta.") from None


def agua_da_area(area: dict, chuva_mm: float, parametros: dict) -> tuple[float, float] | None:
    """Água que chega e água retida (m³) numa área; None para o parque."""
    metros = chuva_mm / 1000
    a = area["area_m2"]
    solucao = area["solucao"]

    if solucao == "piso_permeavel":
        capacidade_mm = _parametro(parametros, "piso_capacidade_mm")
        return a * metros, a * min(chuva_mm, capacidade_mm) / 1000
    if solucao == "telhado_verde":
        retencao = _parametro(parametros, "telhado_retencao")
        return a * metros, a * metros * retencao
    if solucao == "jardim_chuva":
        jardim = a * _parametro(parametros, "jardim_fracao_da_area")
        chega = jardim * _parametro(parametros, "jardim_area_que_escoa") * metros
        return chega, min(chega, jardim * _parametro(parametros, "jardim_lamina_m"))
    return None  # parque: capacidade fixa, não depende da chuva


def premissas(parametros: dict) -> dict:
    """Os valores usados na conta, com a fonte de cada um (parametros.fontes)."""
    fontes = _parametro(parametros, "fontes")
    return {
        "piso_permeavel": {
            "conta": "chega = área × chuva; retida = área × mín(chuva, capacidade_mm)",
            "capacidade_mm": _parametro(parametros, "piso_capacidade_mm"),
            "fonte": fontes.get("piso_permeavel"),
        },
        "telhado_verde": {
            "conta": "chega = área × chuva; retida = chega × retencao",
            "retencao": _parametro(parametros, "telhado_retencao"),
            "fonte": fontes.get("telhado_verde"),
        },
        "jardim_chuva": {
            "conta": (
                "jardim = área × fracao_da_area; chega = jardim × area_que_escoa × chuva; "
                "retida = mín(chega, jardim × lamina_m)"
            ),
            "fracao_da_area": _parametro(parametros, "jardim_fracao_da_area"),
            "area_que_escoa": _parametro(parametros, "jardim_area_que_escoa"),
            "lamina_m": _parametro(parametros, "jardim_lamina_m"),
            "fonte": fontes.get("jardim_chuva"),
        },
        "parque_inundavel": {
            "conta": "capacidade fixa (volume_m3), fora da conta de antes e depois",
            "fonte": fontes.get("parque_inundavel"),
        },
    }


def calcular_cenario(
    areas: list[dict],
    meta: dict,
    chuva_mm: float,
    solucoes: tuple[str, ...] = SOLUCOES,
    nota_minima: int = 0,
) -> dict:
    """Soma o antes e depois das áreas escolhidas para uma chuva de chuva_mm.

    areas: cada uma com solucao, nota, area_m2 e volume_m3.
    meta: o topo do recomendacoes.geojson (camadas_meta), com parametros.
    """
    parametros = _parametro(meta, "parametros")
    escolhidas = [a for a in areas if a["solucao"] in solucoes and a["nota"] >= nota_minima]

    por_solucao = {s: {"n": 0, "chega_m3": 0.0, "retida_m3": 0.0} for s in NA_CONTA if s in solucoes}
    parques = {"n": 0, "capacidade_m3": 0.0}
    chega = retida = 0.0

    for area in escolhidas:
        agua = agua_da_area(area, chuva_mm, parametros)
        if agua is None:
            parques["n"] += 1
            parques["capacidade_m3"] += area.get("volume_m3") or 0
            continue
        chega_area, retida_area = agua
        chega += chega_area
        retida += retida_area
        soma = por_solucao[area["solucao"]]
        soma["n"] += 1
        soma["chega_m3"] += chega_area
        soma["retida_m3"] += retida_area

    return {
        "chuva_mm": chuva_mm,
        "filtros": {"solucoes": [s for s in SOLUCOES if s in solucoes], "nota_minima": nota_minima},
        "n_areas": sum(s["n"] for s in por_solucao.values()),
        "chega_m3": chega,
        "retida_m3": retida,
        "segue_m3": chega - retida,
        "retido_pct": retida / chega * 100 if chega else 0.0,
        "por_solucao": por_solucao,
        "parques": {
            **parques,
            "observacao": "Capacidade fixa: não muda com a chuva e não entra na conta de antes e depois.",
        },
        "premissas": premissas(parametros),
        "area": meta.get("area"),
        "aviso": meta.get("aviso"),
        "metodo": meta.get("metodo"),
    }
