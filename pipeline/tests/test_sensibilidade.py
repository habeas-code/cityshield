"""Testes da análise de sensibilidade da fila (#106), com quatro áreas inventadas."""

import pytest

from pipeline.sensibilidade import _ordem_wlc, _spearman, comparar


def area(id_, posicao, risco, registros, tamanho):
    return {"id": id_, "nome": id_, "posicao": posicao,
            "fator_risco": risco, "fator_registros": registros, "fator_tamanho": tamanho}


def test_spearman_ordem_igual_da_1():
    assert _spearman(["a", "b", "c", "d"], ["a", "b", "c", "d"]) == pytest.approx(1)


def test_spearman_ordem_invertida_da_menos_1():
    assert _spearman(["a", "b", "c", "d"], ["d", "c", "b", "a"]) == pytest.approx(-1)


def test_ordem_wlc_empate_mantem_a_posicao():
    # Mesmos fatores: a soma empata e fica na frente quem está antes na nossa fila.
    areas = [area("B", 2, 0.5, 0.5, 0.5), area("A", 1, 0.5, 0.5, 0.5)]
    assert _ordem_wlc(areas, (1 / 3, 1 / 3, 1 / 3)) == ["A", "B"]


# Nossa fila: A, B, C, D. Fatores (risco, registros, tamanho):
AREAS = [
    area("A", 1, 0.9, 0.9, 0.1),
    area("B", 2, 0.5, 0.5, 0.5),
    area("C", 3, 0.3, 0.3, 1.0),
    area("D", 4, 0.1, 0.1, 1.0),
]

# Somas ponderadas, feitas à mão (n = 4, Spearman = 1 - 6·Σd² / (4·15)):
#   iguais (1/3 cada):   A 0,633  B 0,5  C 0,533  D 0,4   -> A C B D
#       B e C trocam: Σd² = 1 + 1 = 2 -> 1 - 12/60 = 0,8; B cai 1 posição
#   risco em dobro (0,50 0,25 0,25):   A 0,7  B 0,5  C 0,475  D 0,325 -> A B C D (igual)
#   registros em dobro (0,25 0,50 0,25): as mesmas somas -> A B C D (igual)
#   tamanho em dobro (0,25 0,25 0,50): A 0,5  B 0,5  C 0,65  D 0,55 -> C D A B
#       (A e B empatam: A fica antes). Top 3 {C, D, A}: 2 em comum com {A, B, C}.
#       d: A +2, B +2, C -2, D -2 -> Σd² = 16 -> 1 - 96/60 = -0,6; A e B caem 2
ESPERADO = {
    "iguais": {"top3_em_comum": 3, "spearman": 0.8, "maior_queda_do_top10": 1},
    "risco_em_dobro": {"top3_em_comum": 3, "spearman": 1.0, "maior_queda_do_top10": 0},
    "registros_em_dobro": {"top3_em_comum": 3, "spearman": 1.0, "maior_queda_do_top10": 0},
    "tamanho_em_dobro": {"top3_em_comum": 2, "spearman": -0.6, "maior_queda_do_top10": 2},
}


@pytest.mark.parametrize("cenario", ESPERADO)
def test_comparar_cenarios(cenario):
    c = comparar(AREAS)["cenarios"][cenario]
    for chave, valor in ESPERADO[cenario].items():
        assert c[chave] == pytest.approx(valor), chave
    assert c["top10_em_comum"] == 4   # com 4 áreas, todas estão no top 10


def test_comparar_resumo_e_top3():
    saida = comparar(AREAS)
    assert saida["areas"] == 4
    assert saida["nosso_top3"] == ["A", "B", "C"]
    assert saida["cenarios"]["tamanho_em_dobro"]["top3"] == ["C", "D", "A"]
    assert saida["resumo"] == {"top10_em_comum_minimo": 4, "top3_em_comum_minimo": 2,
                               "spearman_minimo": pytest.approx(-0.6)}
