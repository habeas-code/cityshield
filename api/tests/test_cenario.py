"""Testes da conta do cenário (#18), sem banco: a função pura contra a tabela
de docs/recomendacoes.md ("Cenário antes e depois") e contra o volume_m3 que
o pipeline gravou em cada área."""

import copy
import json
from pathlib import Path

import pytest

from app.cenario import ParametrosIncompletos, agua_da_area, calcular_cenario

ARQUIVO = Path(__file__).resolve().parents[2] / "docs" / "dados" / "recomendacoes.geojson"
DADOS = json.loads(ARQUIVO.read_text(encoding="utf-8"))
META = {k: v for k, v in DADOS.items() if k not in ("type", "features")}
AREAS = [f["properties"] for f in DADOS["features"]]
PARAMETROS = META["parametros"]


# ---------------------------------------------------------------- tabela do documento


@pytest.mark.parametrize(
    ("chuva_mm", "chega", "retida", "pct"),
    [(10, 1337, 1195, 89), (50, 6686, 2937, 44), (120, 16047, 3818, 24)],
)
def test_bate_com_a_tabela_de_docs_recomendacoes(chuva_mm, chega, retida, pct):
    r = calcular_cenario(AREAS, META, chuva_mm)

    assert round(r["chega_m3"]) == chega
    assert round(r["retida_m3"]) == retida
    assert round(r["retido_pct"]) == pct
    assert r["segue_m3"] == pytest.approx(r["chega_m3"] - r["retida_m3"])


def test_sem_arredondar_120_mm_continua_16047():
    # 16047,48: arredondar duas vezes (16047,5 → 16048) mudaria o número.
    assert round(calcular_cenario(AREAS, META, 120)["chega_m3"]) == 16047


def test_com_a_chuva_de_referencia_cada_area_retem_o_volume_do_pipeline():
    chuva_ref = PARAMETROS["chuva_ref_mm"]
    conferidas = 0
    for area in AREAS:
        agua = agua_da_area(area, chuva_ref, PARAMETROS)
        if agua is None:
            continue
        assert round(agua[1]) == area["volume_m3"], area["id"]
        conferidas += 1
    assert conferidas == sum(1 for a in AREAS if a["solucao"] != "parque_inundavel")


# ---------------------------------------------------------------- parques e filtros


def test_parques_ficam_fora_da_conta_com_a_capacidade():
    r = calcular_cenario(AREAS, META, 50)
    parques = [a for a in AREAS if a["solucao"] == "parque_inundavel"]

    assert r["parques"]["n"] == len(parques)
    assert r["parques"]["capacidade_m3"] == sum(a["volume_m3"] for a in parques)
    assert "parque_inundavel" not in r["por_solucao"]
    assert r["n_areas"] == len(AREAS) - len(parques)


def test_capacidade_dos_parques_nao_muda_com_a_chuva():
    assert (
        calcular_cenario(AREAS, META, 10)["parques"]
        == calcular_cenario(AREAS, META, 120)["parques"]
    )


def test_filtro_de_solucoes_e_nota_minima():
    r = calcular_cenario(AREAS, META, 50, ("jardim_chuva", "piso_permeavel"), nota_minima=10)
    esperadas = [
        a for a in AREAS if a["solucao"] in ("jardim_chuva", "piso_permeavel") and a["nota"] >= 10
    ]

    assert r["n_areas"] == len(esperadas)
    assert set(r["por_solucao"]) == {"jardim_chuva", "piso_permeavel"}
    assert r["parques"]["n"] == 0
    assert r["filtros"] == {"solucoes": ["jardim_chuva", "piso_permeavel"], "nota_minima": 10}


def test_por_solucao_soma_o_total():
    r = calcular_cenario(AREAS, META, 50)

    assert sum(s["chega_m3"] for s in r["por_solucao"].values()) == pytest.approx(r["chega_m3"])
    assert sum(s["retida_m3"] for s in r["por_solucao"].values()) == pytest.approx(r["retida_m3"])


def test_sem_nenhuma_area_na_conta_retido_e_zero():
    r = calcular_cenario(AREAS, META, 50, ("parque_inundavel",))

    assert (r["n_areas"], r["chega_m3"], r["retida_m3"], r["retido_pct"]) == (0, 0, 0, 0)


# ---------------------------------------------------------------- números de parametros


def test_os_numeros_da_conta_vem_de_parametros():
    # Se 0,47 estivesse escrito no código, mudar o parâmetro não mudaria nada.
    meta = copy.deepcopy(META)
    meta["parametros"]["telhado_retencao"] = 0.9
    antes = calcular_cenario(AREAS, META, 50)["por_solucao"]["telhado_verde"]
    depois = calcular_cenario(AREAS, meta, 50)["por_solucao"]["telhado_verde"]

    assert depois["retida_m3"] == pytest.approx(antes["retida_m3"] / 0.47 * 0.9)


@pytest.mark.parametrize(
    "nome",
    ["piso_capacidade_mm", "telhado_retencao", "jardim_fracao_da_area", "jardim_area_que_escoa", "jardim_lamina_m"],
)
def test_cada_numero_da_conta_e_lido_de_parametros(nome):
    meta = copy.deepcopy(META)
    del meta["parametros"][nome]

    with pytest.raises(ParametrosIncompletos, match=nome):
        calcular_cenario(AREAS, meta, 50)


def test_premissas_trazem_valores_e_fontes_de_parametros():
    p = calcular_cenario(AREAS, META, 50)["premissas"]

    assert p["piso_permeavel"]["capacidade_mm"] == PARAMETROS["piso_capacidade_mm"]
    assert p["telhado_verde"]["retencao"] == PARAMETROS["telhado_retencao"]
    assert p["jardim_chuva"]["fracao_da_area"] == PARAMETROS["jardim_fracao_da_area"]
    assert p["jardim_chuva"]["area_que_escoa"] == PARAMETROS["jardim_area_que_escoa"]
    assert p["jardim_chuva"]["lamina_m"] == PARAMETROS["jardim_lamina_m"]
    for solucao, fonte in PARAMETROS["fontes"].items():
        assert p[solucao]["fonte"] == fonte


def test_resposta_traz_area_aviso_e_metodo_do_arquivo():
    r = calcular_cenario(AREAS, META, 50)

    assert (r["area"], r["aviso"], r["metodo"]) == (META["area"], META["aviso"], META["metodo"])
