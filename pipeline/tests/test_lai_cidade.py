"""Testes do quarto teste (LAI, cidade inteira): CSV público, total e grupos.

Só leem docs/dados/lai_defesa_civil_cidade.csv; não baixam nada.
"""

import csv

from pipeline import lai, lai_cidade

COLUNAS = ["data", "via_planilha", "bairro", "tipo", "registros", "via_osm", "lon", "lat", "no_relatorio_2022_23"]


def _csv():
    with open(lai_cidade.ENTRADA, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_csv_publico_sem_numero_de_casa_nem_guia():
    with open(lai_cidade.ENTRADA, encoding="utf-8", newline="") as f:
        assert next(csv.reader(f)) == COLUNAS


def test_csv_soma_os_1494_registros_sem_repetir_o_itangua():
    # 1360 (município) + 365 (Itanguá) - 230 iguais nas duas - 1 repetida na quebra de página
    assert sum(int(linha["registros"]) for linha in _csv()) == 1494


def test_cheia_pega_20_a_31_de_janeiro_e_janeiro_sem_dia():
    cheia = lai_cidade.FILTROS["cheia_jan_2024"]
    assert cheia({"data": "2024-01-20"}) and cheia({"data": "2024-01-31"}) and cheia({"data": "2024-01"})
    assert not cheia({"data": "2024-01-19"}) and not cheia({"data": "2024-02-01"}) and not cheia({"data": "2024"})


def test_novas_da_cheia_respeitam_os_dois_filtros():
    linhas = [
        {"data": "2024-01-25", "via_osm": "Rua A", "bairro": "X", "registros": "2", "lon": "-47.5", "lat": "-23.5", "no_relatorio_2022_23": "nao"},
        {"data": "2024-01-25", "via_osm": "Rua B", "bairro": "X", "registros": "3", "lon": "-47.4", "lat": "-23.5", "no_relatorio_2022_23": "sim"},
        {"data": "2026-03-11", "via_osm": "Rua A", "bairro": "X", "registros": "4", "lon": "-47.5", "lat": "-23.5", "no_relatorio_2022_23": "nao"},
    ]
    feats = lai.ruas(linhas, lai_cidade.FILTROS["novas_cheia_jan_2024"])
    assert [(f["properties"]["rua"], f["properties"]["registros"]) for f in feats] == [("Rua A", 2)]
