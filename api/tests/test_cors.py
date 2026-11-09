"""Testes do CORS (#56): quem pode chamar a API pelo navegador."""

from app.config import origens_cors

SITE = "https://habeas-code.github.io"


def test_site_do_time_recebe_permissao(cliente):
    resposta = cliente.get("/saude", headers={"Origin": SITE})

    assert resposta.headers["access-control-allow-origin"] == SITE


def test_site_desconhecido_nao_recebe_permissao(cliente):
    resposta = cliente.get("/saude", headers={"Origin": "https://site-estranho.com"})

    assert "access-control-allow-origin" not in resposta.headers


def test_preflight_so_aceita_get(cliente):
    # Antes de alguns pedidos, o navegador pergunta (OPTIONS) se pode fazer.
    pode_get = cliente.options(
        "/saude", headers={"Origin": SITE, "Access-Control-Request-Method": "GET"}
    )
    pode_post = cliente.options(
        "/saude", headers={"Origin": SITE, "Access-Control-Request-Method": "POST"}
    )

    assert pode_get.status_code == 200
    assert pode_post.status_code == 400


def test_origens_ignora_asterisco_espacos_e_barra_final(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", " http://localhost:5173 , https://habeas-code.github.io/ ,*,")

    assert origens_cors() == ["http://localhost:5173", "https://habeas-code.github.io"]


def test_origens_vazio_nao_libera_ninguem(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert origens_cors() == []
