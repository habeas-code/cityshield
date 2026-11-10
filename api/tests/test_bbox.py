"""Testes da leitura do bbox (#11)."""

import pytest

from app.bbox import BboxInvalido, ler_bbox


def test_bbox_valido_vira_quatro_numeros():
    assert ler_bbox("-47.455,-23.478,-47.439,-23.463") == (-47.455, -23.478, -47.439, -23.463)


def test_bbox_aceita_espacos_e_inteiros():
    assert ler_bbox(" -48 , -24 , -47 , -23 ") == (-48.0, -24.0, -47.0, -23.0)


def test_bbox_aceita_o_mundo_inteiro():
    assert ler_bbox("-180,-90,180,90") == (-180.0, -90.0, 180.0, 90.0)


@pytest.mark.parametrize(
    ("texto", "motivo"),
    [
        ("-47.4,-23.4,-47.3", "4 números e veio com 3"),
        ("-47.4,-23.4,-47.3,-23.3,0", "4 números e veio com 5"),
        ("", "4 números e veio com 1"),
        ("a,b,c,d", "só aceita números"),
        ("-47.4,,-47.3,-23.3", "só aceita números"),
        ("-181,-23.4,-47.3,-23.3", "longitude"),
        ("-47.4,-23.4,181,-23.3", "longitude"),
        ("-47.4,-91,-47.3,-23.3", "latitude"),
        ("-47.4,-23.4,-47.3,91", "latitude"),
        ("nan,-23.4,-47.3,-23.3", "longitude"),
        ("-47.4,-inf,-47.3,-23.3", "latitude"),
        ("-47.3,-23.4,-47.4,-23.3", "xmin tem que ser menor que xmax"),
        ("-47.4,-23.4,-47.4,-23.3", "xmin tem que ser menor que xmax"),
        ("-47.4,-23.3,-47.3,-23.4", "ymin tem que ser menor que ymax"),
    ],
)
def test_bbox_invalido_explica_o_motivo(texto, motivo):
    with pytest.raises(BboxInvalido, match=motivo):
        ler_bbox(texto)
