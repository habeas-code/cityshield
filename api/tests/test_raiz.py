"""Testes da rota / (#23): o health check do Render e o alvo do ping."""

from app import banco


def test_raiz_responde_nome_versao_e_docs(cliente):
    resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "nome": "CityShield API",
        "versao": "0.1.0",
        "docs": "/docs",
        "saude": "/saude",
    }


def test_raiz_nao_toca_no_banco(cliente, monkeypatch):
    # Qualquer tentativa de abrir conexão faria o teste falhar.
    def proibido(*args, **kwargs):
        raise AssertionError("a rota / não pode abrir conexão com o banco")

    monkeypatch.setattr(banco.engine, "connect", proibido)

    assert cliente.get("/").status_code == 200


def test_raiz_responde_mesmo_com_banco_fora(cliente):
    # O banco dos testes não existe (conftest.py): a / continua 200 e a /saude, 503.
    assert cliente.get("/").status_code == 200
    assert cliente.get("/saude").status_code == 503


def test_raiz_aparece_no_openapi(cliente):
    assert "/" in cliente.get("/openapi.json").json()["paths"]
