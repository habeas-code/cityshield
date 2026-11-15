"""Testes do cache em memória das respostas inteiras (#109).

Sem banco: a consulta é trocada por uma de mentira que conta as chamadas. O
relógio do cache também é trocado, para simular a passagem do tempo.
"""

import json

import pytest

from app import areas, cache, camadas

PILOTO = "-47.455,-23.478,-47.439,-23.463"
GRANDE = json.dumps({"type": "FeatureCollection", "features": [{"x": "a" * 5000}]})


@pytest.fixture
def banco(monkeypatch):
    """Consulta de mentira: anota cada ida ao banco e devolve `banco.texto`."""

    class Banco:
        chamadas: list = []
        texto = GRANDE
        fora = False

        def consultar(self, sql, parametros, nome):
            self.chamadas.append((nome, dict(parametros)))
            if self.fora:
                raise camadas.CamadaIndisponivel(nome)
            return self.texto

    falso = Banco()
    falso.chamadas = []
    monkeypatch.setattr(camadas, "consultar", falso.consultar)
    monkeypatch.setattr(areas, "consultar", falso.consultar)
    return falso


@pytest.fixture
def relogio(monkeypatch):
    """Relógio de mentira do cache: `relogio.agora` é o momento atual, em segundos."""

    class Relogio:
        agora = 1000.0

    r = Relogio()
    monkeypatch.setattr(cache.time, "monotonic", lambda: r.agora)
    return r


ROTAS_INTEIRAS = ["/camadas/risco", "/camadas/registros", "/areas"]


@pytest.mark.parametrize("rota", ROTAS_INTEIRAS)
def test_segunda_chamada_inteira_nao_vai_ao_banco(cliente, banco, rota):
    primeira = cliente.get(rota)
    segunda = cliente.get(rota)

    assert len(banco.chamadas) == 1
    assert primeira.status_code == segunda.status_code == 200
    assert segunda.text == primeira.text == GRANDE


def test_cada_camada_tem_seu_lugar_no_cache(cliente, banco):
    for rota in ROTAS_INTEIRAS * 2:
        cliente.get(rota)

    assert [nome for nome, _ in banco.chamadas] == ["risco", "registros", "areas"]


@pytest.mark.parametrize(
    ("rota", "params"),
    [
        ("/camadas/risco", {"bbox": PILOTO}),
        ("/camadas/registros", {"bbox": PILOTO}),
        ("/areas", {"bbox": PILOTO}),
        ("/areas", {"solucao": "jardim_chuva"}),
    ],
)
def test_com_filtro_vai_sempre_ao_banco(cliente, banco, rota, params):
    cliente.get(rota, params=params)
    cliente.get(rota, params=params)

    assert len(banco.chamadas) == 2


def test_filtro_nao_usa_nem_estraga_a_resposta_inteira(cliente, banco):
    cliente.get("/camadas/risco")
    banco.texto = '{"type": "FeatureCollection", "features": []}'
    filtrada = cliente.get("/camadas/risco", params={"bbox": PILOTO})
    inteira = cliente.get("/camadas/risco")

    assert filtrada.text == banco.texto
    assert inteira.text == GRANDE
    assert len(banco.chamadas) == 2


def test_carga_nova_aparece_depois_de_30_minutos(cliente, banco, relogio):
    cliente.get("/camadas/risco")
    banco.texto = '{"type": "FeatureCollection", "features": [], "carga": "nova"}'

    relogio.agora += 30 * 60 - 1  # ainda dentro da validade
    assert cliente.get("/camadas/risco").text == GRANDE

    relogio.agora += 1  # venceu
    assert cliente.get("/camadas/risco").text == banco.texto
    assert len(banco.chamadas) == 2


def test_erro_do_banco_nao_fica_guardado(cliente, banco):
    banco.fora = True
    assert cliente.get("/camadas/risco").status_code == 503

    banco.fora = False
    resposta = cliente.get("/camadas/risco")

    assert resposta.status_code == 200
    assert resposta.text == GRANDE
    assert len(banco.chamadas) == 2


def test_banco_cai_depois_do_cache_cheio_e_a_resposta_continua(cliente, banco):
    cliente.get("/camadas/risco")
    banco.fora = True

    assert cliente.get("/camadas/risco").status_code == 200


def test_503_real_sem_banco_nao_fica_guardado(cliente):
    # Sem truque: o banco dos testes não existe (conftest.py).
    for _ in range(2):
        resposta = cliente.get("/camadas/risco")
        assert resposta.status_code == 503
        assert resposta.headers["cache-control"] == "no-store"
    assert cache._guardado == {}


@pytest.mark.parametrize("rota", ROTAS_INTEIRAS)
def test_resposta_do_cache_igual_a_de_hoje(cliente, banco, rota):
    cliente.get(rota)
    resposta = cliente.get(rota, headers={"Accept-Encoding": "gzip"})

    assert resposta.headers["content-type"] == "application/geo+json"
    assert resposta.headers["cache-control"] == "public, max-age=300"
    assert resposta.headers["content-encoding"] == "gzip"
    assert resposta.text == GRANDE


def test_ficha_e_cenario_nao_usam_o_cache(cliente, banco):
    banco.texto = None  # a ficha procurada não existe
    cliente.get("/areas/way-1")
    cliente.get("/areas/way-1")

    assert len(banco.chamadas) == 2
    assert cache._guardado == {}
