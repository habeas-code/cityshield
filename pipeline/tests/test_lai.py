"""Testes do terceiro teste (registros oficiais LAI 2026): CSV público e soma por via.

Só leem docs/dados/lai_defesa_civil.csv; não baixam nada.
"""

import csv

from pipeline import lai

COLUNAS = ["data", "via_planilha", "bairro", "tipo", "registros", "via_osm", "lon", "lat", "no_relatorio_2022_23"]


def _csv():
    with open(lai.ENTRADA, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_csv_publico_sem_numero_de_casa_nem_guia():
    with open(lai.ENTRADA, encoding="utf-8", newline="") as f:
        assert next(csv.reader(f)) == COLUNAS


def test_csv_soma_os_365_registros_da_planilha():
    assert sum(int(linha["registros"]) for linha in _csv()) == 365


def test_ruas_soma_por_via_e_respeita_o_filtro():
    linhas = [
        {"data": "2026-03-11", "via_osm": "Rua A", "bairro": "X", "registros": "2", "lon": "-47.5", "lat": "-23.5", "no_relatorio_2022_23": "sim"},
        {"data": "2026-11-08", "via_osm": "Rua A", "bairro": "X", "registros": "3", "lon": "-47.5", "lat": "-23.5", "no_relatorio_2022_23": "sim"},
        {"data": "2026-11-09", "via_osm": "", "bairro": "Y", "registros": "4", "lon": "", "lat": "", "no_relatorio_2022_23": ""},
    ]
    todas = lai.ruas(linhas, lai.FILTROS["todas"])
    assert [(f["properties"]["rua"], f["properties"]["registros"]) for f in todas] == [("Rua A", 5)]
    depois = lai.ruas(linhas, lai.FILTROS["depois_do_mapa"])
    assert depois[0]["properties"]["registros"] == 3
    assert lai.ruas(linhas, lai.FILTROS["novas"]) == []


def test_regiao_cobre_todas_as_vias_com_ponto():
    from shapely.geometry import Point

    linhas = _csv()
    area = lai.regiao(linhas)
    assert all(area.contains(Point(float(x["lon"]), float(x["lat"]))) for x in linhas if x["lon"])
