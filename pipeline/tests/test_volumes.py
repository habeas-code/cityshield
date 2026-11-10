"""Testes das contas de volume (#106): só funções puras, com dados montados aqui.

Os valores esperados saem da fórmula de cada docstring, feita à mão nos comentários.
"""

import numpy as np
import pytest

from pipeline import volumes
from pipeline.volumes import _curva_cota_volume, _nivel_para, _volume_ate, enchimento, estimar


# ---------- enchimento ----------

def test_enchimento_faixa_em_mm():
    # enche com (mm) = capacidade ÷ (contribuição × C) × 1000, com C de 0,50 a 0,70
    # menor valor (C 0,70): 3.500 ÷ (10.000 × 0,70) × 1000 = 3.500 ÷ 7.000 × 1000 = 500
    # maior valor (C 0,50): 3.500 ÷ (10.000 × 0,50) × 1000 = 3.500 ÷ 5.000 × 1000 = 700
    saida = enchimento(3500, 10_000)
    assert saida == {"contribuicao_m2": 10_000, "enche_com_mm": [500, 700]}


def test_enchimento_sobe_com_curva_simples():
    # Água que chega em 16/10: 52 mm × 10.000 m² × C
    #   C 0,50: 0,052 × 10.000 × 0,50 = 260 m³
    #   C 0,70: 0,052 × 10.000 × 0,70 = 364 m³
    # Curva reta: 520 m³ por metro. 260 m³ -> 0,5 m; 364 m³ -> 0,7 m
    curva = [{"nivel_m": 1.0, "volume_m3": 520}, {"nivel_m": 2.0, "volume_m3": 1040}]
    assert enchimento(3500, 10_000, curva)["sobe_16_10_m"] == [0.5, 0.7]


def test_enchimento_none_quando_passa_do_ultimo_nivel():
    # Curva só até 300 m³ em 1 m: 260 m³ -> 260/300 = 0,87 m; 364 m³ passa do fim -> None
    curva = [{"nivel_m": 1.0, "volume_m3": 300}]
    assert enchimento(3500, 10_000, curva)["sobe_16_10_m"] == [0.87, None]


def test_enchimento_sem_curva_nao_diz_ate_onde_sobe():
    assert "sobe_16_10_m" not in enchimento(3500, 10_000)


@pytest.mark.parametrize("capacidade, contribuicao", [(0, 10_000), (None, 10_000), (3500, 0), (3500, None)])
def test_enchimento_vazio_sem_capacidade_ou_contribuicao(capacidade, contribuicao):
    assert enchimento(capacidade, contribuicao) == {}


# ---------- _nivel_para ----------

CURVA = [{"nivel_m": 0.5, "volume_m3": 100}, {"nivel_m": 1.0, "volume_m3": 300}]


def test_nivel_interpola_entre_dois_niveis():
    # 200 m³ fica no meio de 100 (0,5 m) e 300 (1,0 m): 0,5 + 100/200 × 0,5 = 0,75 m
    assert _nivel_para(CURVA, 200) == pytest.approx(0.75)


def test_nivel_interpola_a_partir_do_zero():
    # Antes do primeiro nível, parte de 0 m³ em 0 m: 50/100 × 0,5 = 0,25 m
    assert _nivel_para(CURVA, 50) == pytest.approx(0.25)


@pytest.mark.parametrize("volume, nivel", [(100, 0.5), (300, 1.0)])
def test_nivel_com_volume_exato_de_um_nivel(volume, nivel):
    assert _nivel_para(CURVA, volume) == pytest.approx(nivel)


def test_nivel_acima_do_ultimo_e_none():
    assert _nivel_para(CURVA, 301) is None


# ---------- _volume_ate e _curva_cota_volume ----------

# Três células de 100 m² com o chão a 10, 11 e 12 m; fundo em 10 m.
TERRENO = (np.array([10.0, 11.0, 12.0]), 10.0, 100.0)


@pytest.mark.parametrize("lamina, volume, area", [
    (1.0, 100, 100),   # água a 11 m: só a 1ª célula, 1 m de fundo -> 1 × 100 m³
    (1.5, 200, 200),   # água a 11,5 m: 1,5 + 0,5 = 2 m × 100 m²; duas células alagadas
    (2.5, 450, 300),   # água a 12,5 m: 2,5 + 1,5 + 0,5 = 4,5 m × 100 m²; as três
])
def test_volume_ate(lamina, volume, area):
    assert _volume_ate(TERRENO, lamina) == (pytest.approx(volume), pytest.approx(area))


def test_curva_cota_volume():
    # Um ponto por nível de CURVA_NIVEIS_M (0,25 a 2 m), com a mesma conta de cima.
    assert volumes.CURVA_NIVEIS_M == (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
    assert _curva_cota_volume(TERRENO) == [
        {"nivel_m": 0.25, "volume_m3": 25, "area_alagada_m2": 100},
        {"nivel_m": 0.5, "volume_m3": 50, "area_alagada_m2": 100},
        {"nivel_m": 0.75, "volume_m3": 75, "area_alagada_m2": 100},
        {"nivel_m": 1.0, "volume_m3": 100, "area_alagada_m2": 100},
        {"nivel_m": 1.5, "volume_m3": 200, "area_alagada_m2": 200},   # 1,5 + 0,5
        {"nivel_m": 2.0, "volume_m3": 300, "area_alagada_m2": 200},   # 2 + 1 (a 3ª fica no seco)
    ]


# ---------- estimar (piso, telhado e jardim não usam o relevo) ----------

def test_estimar_piso():
    # 2.000 m² × 50 mm (chuva de referência; a base segura até 50 mm) = 100 m³; segura tudo
    saida = estimar({"area_m2": 2000, "solucao": "piso_permeavel"}, None, None)
    assert saida["volume_m3"] == 100
    assert saida["fracao_retida"] == 1.0
    assert saida["volume_tipo"] == "retido"
    assert saida["volume_fonte"] == volumes.FONTES["piso_permeavel"]


def test_estimar_telhado():
    # 2.000 m² × 50 mm = 100 m³ que caem; 47% retido = 47 m³
    saida = estimar({"area_m2": 2000, "solucao": "telhado_verde"}, None, None)
    assert saida["volume_m3"] == 47
    assert saida["fracao_retida"] == 0.47
    assert saida["volume_fonte"] == volumes.FONTES["telhado_verde"]


def test_estimar_jardim():
    # Jardim = 10% de 2.000 m² = 200 m². Chega: 200 m² × 10 (área que escoa) × 50 mm = 100 m³.
    # Cabe: 200 m² × 15 cm = 30 m³. Segura o menor: 30 m³, 30% do que chega.
    saida = estimar({"area_m2": 2000, "solucao": "jardim_chuva"}, None, None)
    assert saida["volume_m3"] == 30
    assert saida["fracao_retida"] == 0.3
    assert saida["volume_fonte"] == volumes.FONTES["jardim_chuva"]
