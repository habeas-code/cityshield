"""Testes das funções de nome de rua e proporção da validação (#106).

Só leem pipeline/validacao.py; não baixam nada do OSM.
"""

import pytest

from pipeline.validacao import SEMELHANCA_MINIMA, _normalizar, _parecido, _proporcao


@pytest.mark.parametrize("nome, normalizado", [
    ("Rua São João", "rua sao joao"),                       # acentos
    ("Avenida Itavuvu (Bairro Jardim)", "avenida itavuvu"),  # tira o "(bairro)"
    ("AVENIDA DOM AGUIRRE", "avenida dom aguirre"),         # maiúsculas
    ("Rua XV de Agosto", "rua 15 de agosto"),               # XV vira 15, como no OSM
    ("  Praça   Coronel  Fernando ", "praca coronel fernando"),  # espaços
])
def test_normalizar(nome, normalizado):
    assert _normalizar(nome) == normalizado


def test_parecido_palavras_do_relatorio_dentro_do_nome_do_osm():
    assert _parecido("afonso vergueiro", "doutor afonso vergueiro") == 1.0
    # "de", "da"... não contam: "rua da penha" cabe em "rua penha"
    assert _parecido("rua da penha", "rua penha") == 1.0


def test_parecido_grafia_diferente():
    # "mota" x "motta": 4 letras iguais em 4 + 5 -> 2·4/9 = 0,889, acima do mínimo de 0,88
    assert _parecido("mota", "motta") == pytest.approx(8 / 9)
    assert _parecido("mota", "motta") >= SEMELHANCA_MINIMA


def test_parecido_nomes_sem_nada_em_comum():
    assert _parecido("abc", "xyz") == 0.0


def test_proporcao():
    assert _proporcao({"alto": 1, "medio": 3}) == {"alto": 0.25, "medio": 0.75}


def test_proporcao_sem_nada_contado():
    assert _proporcao({"alto": 0, "medio": 0}) == {"alto": 0.0, "medio": 0.0}
    assert _proporcao({}) == {}
