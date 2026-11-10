"""Testes da escolha da solução e dos avisos de projeto (#106)."""

import pytest

from pipeline.recomendacoes import ROTULO_ALERTA, _alertas, _solucao


# ---------- _solucao ----------

@pytest.mark.parametrize("area, solucao", [
    ({"tipo": "estacionamento", "area_m2": 50_000, "fracao_alto": 1.0}, "piso_permeavel"),
    ({"tipo": "telhado", "area_m2": 50_000, "fracao_alto": 1.0}, "telhado_verde"),
    # parque: área verde com 1 ha ou mais e metade ou mais no risco alto (os dois limites)
    ({"tipo": "area_verde", "area_m2": 10_000, "fracao_alto": 0.5}, "parque_inundavel"),
    ({"tipo": "area_verde", "area_m2": 9_999, "fracao_alto": 1.0}, "jardim_chuva"),
    ({"tipo": "area_verde", "area_m2": 50_000, "fracao_alto": 0.49}, "jardim_chuva"),
])
def test_solucao(area, solucao):
    assert _solucao(area) == solucao


# ---------- _alertas ----------

def rotulos(p, solucao):
    return tuple(r for _, r in _alertas(p, solucao))


@pytest.mark.parametrize("solucao", ["jardim_chuva", "piso_permeavel"])
def test_lencol_abaixo_de_1_m_em_jardim_e_piso(solucao):
    assert rotulos({"hand_min_m": 0.5}, solucao) == ("lençol",)


@pytest.mark.parametrize("solucao", ["telhado_verde", "parque_inundavel"])
def test_lencol_nao_vale_para_telhado_nem_parque(solucao):
    assert rotulos({"hand_min_m": 0.5}, solucao) == ()


def test_lencol_com_hand_de_1_m_nao_avisa():
    assert rotulos({"hand_min_m": 1.0}, "jardim_chuva") == ()


def test_piso_inclinado_acima_de_3_pct():
    assert rotulos({"hand_min_m": 5, "declividade_pct": 3}, "piso_permeavel") == ()
    avisos = _alertas({"hand_min_m": 5, "declividade_pct": 3.5}, "piso_permeavel")
    assert [r for _, r in avisos] == ["inclinação"]
    assert "3,5%" in avisos[0][0]


def test_jardim_inclinado_a_partir_de_15_pct():
    assert rotulos({"hand_min_m": 5, "declividade_pct": 14.9}, "jardim_chuva") == ()
    assert rotulos({"hand_min_m": 5, "declividade_pct": 15}, "jardim_chuva") == ("inclinação",)


def test_declividade_nao_vale_para_telhado_nem_parque():
    for solucao in ("telhado_verde", "parque_inundavel"):
        assert rotulos({"hand_min_m": 5, "declividade_pct": 40}, solucao) == ()


def test_os_dois_avisos_juntos():
    assert rotulos({"hand_min_m": 0.5, "declividade_pct": 20}, "jardim_chuva") == ("lençol", "inclinação")


def test_nenhum_aviso():
    assert _alertas({"hand_min_m": 2, "declividade_pct": None}, "jardim_chuva") == []
    assert _alertas({"hand_min_m": 2}, "piso_permeavel") == []


def test_rotulos_curtos():
    assert ROTULO_ALERTA[("lençol",)] == "conferir o lençol freático"
    assert ROTULO_ALERTA[("inclinação",)] == "terreno inclinado"
    assert ROTULO_ALERTA[("lençol", "inclinação")] == "conferir lençol e inclinação"
