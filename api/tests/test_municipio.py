"""Todas as feições das camadas ficam dentro do município (#109).

Um bbox que contém o MUNICIPIO (app/bbox.py) recebe a camada inteira do cache,
sem ir ao banco. Isso só está certo se nenhuma feição sair do MUNICIPIO: se
um dia o pipeline gerar algo fora, este teste falha, em vez de alguém receber
do cache uma camada diferente da que o banco daria.

Lê os mesmos arquivos de docs/dados/ que a carga grava no banco (db/carga.py).
"""

import json
from pathlib import Path

import pytest

from app.bbox import MUNICIPIO

DADOS = Path(__file__).resolve().parents[2] / "docs" / "dados"
ARQUIVOS = ["risco_hand.geojson", "ruas.geojson", "recomendacoes.geojson"]


def pontos(coordenadas):
    """Todos os pares [lon, lat] de uma geometria, em qualquer profundidade."""
    if isinstance(coordenadas[0], (int, float)):
        yield coordenadas
        return
    for parte in coordenadas:
        yield from pontos(parte)


def feicoes_fora(feicoes) -> list[tuple[int, float, float]]:
    """(posição, lon, lat) do primeiro ponto fora do MUNICIPIO de cada feição."""
    xmin, ymin, xmax, ymax = MUNICIPIO
    fora = []
    for i, feicao in enumerate(feicoes):
        for lon, lat, *_ in pontos(feicao["geometry"]["coordinates"]):
            if not (xmin <= lon <= xmax and ymin <= lat <= ymax):
                fora.append((i, lon, lat))
                break
    return fora


@pytest.mark.parametrize("nome", ARQUIVOS)
def test_todas_as_feicoes_dentro_do_municipio(nome):
    feicoes = json.loads((DADOS / nome).read_text(encoding="utf-8"))["features"]
    assert feicoes, f"{nome} sem feições"

    fora = feicoes_fora(feicoes)

    assert not fora, f"{nome}: {len(fora)} feições saem do MUNICIPIO, a 1ª: {fora[0]}"


def test_a_conta_pega_feicao_fora():
    dentro = {"geometry": {"type": "Point", "coordinates": [-47.45, -23.47]}}
    # Polígono com um vértice ao norte do município (lat -22.9).
    vaza = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-47.45, -23.47], [-47.44, -22.9], [-47.43, -23.47], [-47.45, -23.47]]],
        }
    }

    assert feicoes_fora([dentro, vaza]) == [(1, -47.44, -22.9)]
