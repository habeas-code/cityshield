"""Testes das rotas /areas, /areas/{id} e /cenario (#18).

Sem banco: onde a resposta depende do banco, a leitura é trocada por uma
função de mentira. O 503 é real (o banco dos testes não existe, conftest.py).
"""

import json

import pytest

from app import areas
from test_cenario import AREAS, META

PILOTO = "-47.455,-23.478,-47.439,-23.463"
VAZIA = '{"type": "FeatureCollection", "features": []}'
FEICAO = '{"type": "Feature", "properties": {}, "geometry": null, "id": "way-48448685"}'


@pytest.fixture
def banco_de_mentira(monkeypatch):
    """Troca as leituras do banco e anota com o que foram chamadas."""
    chamadas = []

    def lista(bbox=None, solucao=None):
        chamadas.append(("lista", bbox, solucao))
        return VAZIA

    def uma(id_area):
        chamadas.append(("uma", id_area))
        return FEICAO if id_area == "way-48448685" else None

    def cenario():
        chamadas.append(("cenario",))
        return {"meta": META, "areas": AREAS}

    monkeypatch.setattr(areas, "areas_geojson", lista)
    monkeypatch.setattr(areas, "area_geojson", uma)
    monkeypatch.setattr(areas, "dados_cenario", cenario)
    return chamadas


# ---------------------------------------------------------------- /areas


def test_areas_sem_filtro(cliente, banco_de_mentira):
    resposta = cliente.get("/areas")

    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/geo+json"
    assert resposta.headers["cache-control"] == "public, max-age=300"
    assert banco_de_mentira == [("lista", None, None)]


def test_areas_com_bbox_e_solucao(cliente, banco_de_mentira):
    resposta = cliente.get("/areas", params={"bbox": PILOTO, "solucao": "jardim_chuva"})

    assert resposta.status_code == 200
    assert banco_de_mentira == [("lista", (-47.455, -23.478, -47.439, -23.463), "jardim_chuva")]


@pytest.mark.parametrize(
    ("params", "motivo"),
    [({"solucao": "lago"}, "solucao desconhecida"), ({"bbox": "1,2,3"}, "4 números")],
)
def test_areas_com_filtro_invalido_responde_422(cliente, banco_de_mentira, params, motivo):
    resposta = cliente.get("/areas", params=params)

    assert resposta.status_code == 422
    assert motivo in resposta.json()["detail"]
    assert banco_de_mentira == []


# ---------------------------------------------------------------- /areas/{id}


def test_ficha_de_uma_area(cliente, banco_de_mentira):
    resposta = cliente.get("/areas/way-48448685")

    assert resposta.status_code == 200
    assert resposta.json()["id"] == "way-48448685"
    assert resposta.headers["content-type"] == "application/geo+json"


def test_area_que_nao_existe_responde_404(cliente, banco_de_mentira):
    resposta = cliente.get("/areas/way-1")

    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "área way-1 não encontrada. Veja os ids em /areas."}


@pytest.mark.parametrize("id_area", ["abc", "way-", "way-12x", "rua-1", "WAY-1", "48448685"])
def test_id_em_formato_invalido_responde_422_sem_ir_ao_banco(cliente, banco_de_mentira, id_area):
    resposta = cliente.get(f"/areas/{id_area}")

    assert resposta.status_code == 422
    assert "id inválido" in resposta.json()["detail"]
    assert banco_de_mentira == []


@pytest.mark.parametrize("id_area", ["way-48448685", "node-1", "relation-42"])
def test_id_aceita_os_tres_tipos_do_osm(cliente, banco_de_mentira, id_area):
    assert cliente.get(f"/areas/{id_area}").status_code in (200, 404)


# ---------------------------------------------------------------- /cenario


def test_cenario_50_mm_com_os_dados_do_arquivo(cliente, banco_de_mentira):
    resposta = cliente.get("/cenario", params={"chuva_mm": 50})
    r = resposta.json()

    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "public, max-age=300"
    assert (round(r["chega_m3"]), round(r["retida_m3"])) == (6686, 2937)
    assert r["parques"]["n"] == 4
    assert r["premissas"]["telhado_verde"]["fonte"] == META["parametros"]["fontes"]["telhado_verde"]


def test_cenario_repassa_os_filtros(cliente, banco_de_mentira):
    r = cliente.get(
        "/cenario",
        params={"chuva_mm": 50, "solucoes": "piso_permeavel, jardim_chuva", "nota_minima": 10},
    ).json()

    # A ordem dos códigos segue a lista fixa, e os espaços são ignorados.
    assert r["filtros"] == {"solucoes": ["jardim_chuva", "piso_permeavel"], "nota_minima": 10}


@pytest.mark.parametrize(
    ("params", "mensagem"),
    [
        ({}, "falta o parâmetro obrigatório chuva_mm."),
        ({"chuva_mm": "abc"}, "chuva_mm tem que ser um número."),
        ({"chuva_mm": 0}, "chuva_mm tem que ficar entre 1 e 300 mm."),
        ({"chuva_mm": 300.1}, "chuva_mm tem que ficar entre 1 e 300 mm."),
        ({"chuva_mm": "nan"}, "chuva_mm tem que ficar entre 1 e 300 mm."),
        ({"chuva_mm": 50, "nota_minima": 101}, "nota_minima tem que ficar entre 0 e 100."),
        ({"chuva_mm": 50, "nota_minima": -1}, "nota_minima tem que ficar entre 0 e 100."),
        ({"chuva_mm": 50, "nota_minima": "1.5"}, "nota_minima tem que ser um número inteiro."),
    ],
)
def test_cenario_com_parametro_invalido_responde_422(cliente, banco_de_mentira, params, mensagem):
    resposta = cliente.get("/cenario", params=params)

    assert resposta.status_code == 422
    assert resposta.json() == {"detail": mensagem}
    assert banco_de_mentira == []


@pytest.mark.parametrize("solucoes", ["lago", "jardim_chuva,lago", ",", ""])
def test_cenario_com_solucao_desconhecida_responde_422(cliente, banco_de_mentira, solucoes):
    resposta = cliente.get("/cenario", params={"chuva_mm": 50, "solucoes": solucoes})

    assert resposta.status_code == 422
    assert "solucoes desconhecidas" in resposta.json()["detail"]


def test_cenario_aceita_os_limites_da_chuva(cliente, banco_de_mentira):
    assert cliente.get("/cenario", params={"chuva_mm": 1}).status_code == 200
    assert cliente.get("/cenario", params={"chuva_mm": 300}).status_code == 200


def test_cenario_sem_parametro_no_banco_responde_500_sem_detalhe(cliente, monkeypatch):
    meta = json.loads(json.dumps(META))
    del meta["parametros"]["telhado_retencao"]
    monkeypatch.setattr(areas, "dados_cenario", lambda: {"meta": meta, "areas": AREAS})

    resposta = cliente.get("/cenario", params={"chuva_mm": 50})

    assert resposta.status_code == 500
    assert resposta.json() == {"erro": "cenário indisponível: parâmetros incompletos no banco"}
    assert "telhado_retencao" not in resposta.text
    assert resposta.headers["cache-control"] == "no-store"


# ---------------------------------------------------------------- 503


@pytest.mark.parametrize("rota", ["/areas", "/areas/way-48448685", "/cenario?chuva_mm=50"])
def test_banco_fora_responde_503_simples(cliente, rota):
    # Sem truque: o banco dos testes aponta para uma porta sem banco.
    resposta = cliente.get(rota)

    assert resposta.status_code == 503
    assert resposta.json() == {"erro": "camada indisponível, tente de novo em instantes"}
    assert resposta.headers["cache-control"] == "no-store"
    for detalhe in ("Traceback", "127.0.0.1", "teste", "OperationalError"):
        assert detalhe not in resposta.text


# ---------------------------------------------------------------- /docs


def test_rotas_aparecem_documentadas_no_openapi(cliente):
    caminhos = cliente.get("/openapi.json").json()["paths"]

    for rota in ("/areas", "/areas/{id_area}", "/cenario"):
        get = caminhos[rota]["get"]
        assert get["summary"] and get["description"]
        assert {"200", "422", "503"} <= get["responses"].keys()
    assert "404" in caminhos["/areas/{id_area}"]["get"]["responses"]
    parametros = {p["name"]: p for p in caminhos["/cenario"]["get"]["parameters"]}
    assert parametros["chuva_mm"]["required"] is True
    assert parametros["chuva_mm"]["schema"]["examples"] == [50]
    exemplo = caminhos["/cenario"]["get"]["responses"]["200"]["content"]["application/json"]
    assert exemplo["example"]["chuva_mm"] == 50.0
