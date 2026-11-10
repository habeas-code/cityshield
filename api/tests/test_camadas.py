"""Testes das rotas /camadas/risco e /camadas/registros (#11).

Sem banco: onde a resposta depende do banco, a leitura é trocada por uma
função de mentira. O 503 é real (o banco dos testes não existe, conftest.py).
"""

import json

import pytest

from app import camadas

ROTAS = {"/camadas/risco": "risco", "/camadas/registros": "registros"}
PILOTO = "-47.455,-23.478,-47.439,-23.463"
VAZIA = '{"type": "FeatureCollection", "features": []}'


@pytest.fixture
def banco_de_mentira(monkeypatch):
    """Troca a leitura do banco e anota com o que ela foi chamada."""
    chamadas = []

    def falsa(nome, bbox=None):
        chamadas.append((nome, bbox))
        return VAZIA

    monkeypatch.setattr(camadas, "camada_geojson", falsa)
    return chamadas


# ---------------------------------------------------------------- 200


@pytest.mark.parametrize(("rota", "camada"), ROTAS.items())
def test_sem_bbox_pede_a_camada_inteira(cliente, banco_de_mentira, rota, camada):
    resposta = cliente.get(rota)

    assert resposta.status_code == 200
    assert banco_de_mentira == [(camada, None)]
    assert resposta.text == VAZIA


@pytest.mark.parametrize(("rota", "camada"), ROTAS.items())
def test_bbox_valido_chega_ao_banco_como_quatro_numeros(cliente, banco_de_mentira, rota, camada):
    resposta = cliente.get(rota, params={"bbox": PILOTO})

    assert resposta.status_code == 200
    assert banco_de_mentira == [(camada, (-47.455, -23.478, -47.439, -23.463))]


def test_resposta_e_geojson_com_cache(cliente, banco_de_mentira):
    resposta = cliente.get("/camadas/risco")

    assert resposta.headers["content-type"] == "application/geo+json"
    assert resposta.headers["cache-control"] == "public, max-age=300"


def test_camada_grande_vem_comprimida(cliente, monkeypatch):
    grande = json.dumps({"type": "FeatureCollection", "features": [{"x": "a" * 5000}]})
    monkeypatch.setattr(camadas, "camada_geojson", lambda nome, bbox=None: grande)

    resposta = cliente.get("/camadas/risco", headers={"Accept-Encoding": "gzip"})

    assert resposta.headers["content-encoding"] == "gzip"
    assert resposta.text == grande  # o TestClient descomprime sozinho


# ---------------------------------------------------------------- 422


@pytest.mark.parametrize("rota", ROTAS)
@pytest.mark.parametrize(
    ("bbox", "motivo"),
    [
        ("-47.4,-23.4,-47.3", "4 números"),
        ("a,b,c,d", "só aceita números"),
        ("-47.4,-95,-47.3,-23.3", "latitude"),
        ("-47.3,-23.4,-47.4,-23.3", "xmin tem que ser menor"),
    ],
)
def test_bbox_invalido_responde_422_sem_ir_ao_banco(cliente, banco_de_mentira, rota, bbox, motivo):
    resposta = cliente.get(rota, params={"bbox": bbox})

    assert resposta.status_code == 422
    assert motivo in resposta.json()["detail"]
    assert banco_de_mentira == []


# ---------------------------------------------------------------- 503


@pytest.mark.parametrize("rota", ROTAS)
def test_banco_fora_responde_503_simples(cliente, rota):
    # Sem truque: o banco dos testes aponta para uma porta sem banco.
    resposta = cliente.get(rota, params={"bbox": PILOTO})

    assert resposta.status_code == 503
    assert resposta.json() == {"erro": "camada indisponível, tente de novo em instantes"}
    assert resposta.headers["cache-control"] == "no-store"


def test_503_nao_mostra_detalhe_do_erro(cliente):
    texto = cliente.get("/camadas/risco").text

    assert "Traceback" not in texto
    assert "127.0.0.1" not in texto
    assert "teste" not in texto  # usuário e nome do banco
    assert "OperationalError" not in texto


# ---------------------------------------------------------------- /docs


def test_rotas_aparecem_documentadas_no_openapi(cliente):
    caminhos = cliente.get("/openapi.json").json()["paths"]

    for rota in ROTAS:
        get = caminhos[rota]["get"]
        bbox = get["parameters"][0]
        assert get["summary"] and get["description"]
        assert bbox["name"] == "bbox" and bbox["required"] is False
        assert "xmin,ymin,xmax,ymax" in bbox["description"]
        assert bbox["schema"]["examples"] == [PILOTO]
        assert {"200", "422", "503"} <= get["responses"].keys()
        assert "application/geo+json" in get["responses"]["200"]["content"]
