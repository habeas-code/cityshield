"""Testes do cache em memória das respostas inteiras (#109).

Sem banco: a consulta é trocada por uma de mentira que conta as chamadas. O
relógio do cache também é trocado, para simular a passagem do tempo.
"""

import json
import threading

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


MUNDO = "-180,-90,180,90"
# Cobre quase tudo, mas deixa de fora uma tira de 0,01° no oeste do município.
QUASE = "-47.81,-23.84,-47.05,-23.10"


@pytest.mark.parametrize("rota", ROTAS_INTEIRAS)
def test_bbox_do_mundo_usa_o_cache(cliente, banco, rota):
    primeira = cliente.get(rota, params={"bbox": MUNDO})
    segunda = cliente.get(rota, params={"bbox": MUNDO})

    assert len(banco.chamadas) == 1
    assert primeira.text == segunda.text == GRANDE


def test_bbox_do_mundo_e_sem_bbox_dividem_o_mesmo_lugar(cliente, banco):
    cliente.get("/camadas/risco")
    cliente.get("/camadas/risco", params={"bbox": MUNDO})
    cliente.get("/camadas/risco", params={"bbox": "-47.82,-23.84,-47.05,-23.10"})

    assert len(banco.chamadas) == 1
    # O que foi ao banco foi a camada inteira, não o bbox pedido.
    _, parametros = banco.chamadas[0]
    assert parametros["xmin"] == -180.0 and parametros["ymax"] == 90.0


@pytest.mark.parametrize("rota", ROTAS_INTEIRAS)
def test_bbox_quase_do_municipio_vai_ao_banco(cliente, banco, rota):
    cliente.get(rota, params={"bbox": QUASE})
    cliente.get(rota, params={"bbox": QUASE})

    assert len(banco.chamadas) == 2
    assert banco.chamadas[0][1]["xmin"] == -47.81


def test_areas_com_solucao_e_bbox_do_mundo_vai_ao_banco(cliente, banco):
    for _ in range(2):
        cliente.get("/areas", params={"bbox": MUNDO, "solucao": "jardim_chuva"})

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


# ---------------------------------------------------------------- travas


def test_dois_pedidos_juntos_na_mesma_chave_vao_ao_banco_uma_vez():
    entrou = threading.Event()
    soltar = threading.Event()
    idas = []

    def buscar_devagar():
        idas.append(1)
        entrou.set()
        soltar.wait(5)  # o banco "acordando"
        return GRANDE

    respostas = []
    primeiro = threading.Thread(target=lambda: respostas.append(cache.lembrar("risco", buscar_devagar)))
    primeiro.start()
    assert entrou.wait(5)
    # O segundo chega enquanto o primeiro ainda está no banco.
    segundo = threading.Thread(target=lambda: respostas.append(cache.lembrar("risco", buscar_devagar)))
    segundo.start()
    segundo.join(0.2)
    assert segundo.is_alive()  # esperando o primeiro, não foi ao banco

    soltar.set()
    primeiro.join(5)
    segundo.join(5)

    assert len(idas) == 1
    assert respostas == [GRANDE, GRANDE]


def test_chave_diferente_nao_espera_a_outra():
    entrou = threading.Event()
    soltar = threading.Event()

    def risco_devagar():
        entrou.set()
        soltar.wait(5)
        return GRANDE

    preso = threading.Thread(target=lambda: cache.lembrar("risco", risco_devagar))
    preso.start()
    try:
        assert entrou.wait(5)
        respostas = []
        outra = threading.Thread(target=lambda: respostas.append(cache.lembrar("registros", lambda: "ok")))
        outra.start()
        outra.join(1)

        assert not outra.is_alive(), "registros ficou esperando risco"
        assert respostas == ["ok"]
    finally:
        soltar.set()
        preso.join(5)
