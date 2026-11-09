"""Testes da rota /saude (#56)."""

from app import banco


def test_saude_com_banco_no_ar_responde_200(cliente, monkeypatch):
    # Finge que o SELECT 1 deu certo.
    monkeypatch.setattr(banco, "banco_responde", lambda: True)

    resposta = cliente.get("/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


def test_saude_com_banco_fora_responde_503(cliente):
    # Sem truque: o banco dos testes aponta para uma porta sem banco (conftest.py).
    resposta = cliente.get("/saude")

    assert resposta.status_code == 503
    assert resposta.json() == {"status": "erro", "banco": "fora do ar"}


def test_saude_nao_mostra_detalhe_do_erro(cliente):
    # Nada de mensagem técnica (endereço, usuário, stack trace) para quem chamou.
    texto = cliente.get("/saude").text

    assert "Traceback" not in texto
    assert "127.0.0.1" not in texto
    assert "OperationalError" not in texto
