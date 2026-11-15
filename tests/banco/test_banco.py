"""A API contra um PostGIS de verdade, com o usuário só de leitura (#108).

Antes destes testes, o CI aplica db/init/, roda a carga duas vezes e cria o
cityshield_api com o SQL do docs/deploy.md (seção 3). Aqui:

  - todas as rotas respondem 200 com o cityshield_api;
  - sem bbox, as camadas e as áreas são iguais aos arquivos de docs/dados/
    (plano B, D10);
  - o cityshield_api não consegue gravar.
"""

import json

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from conftest import RAIZ

DADOS = RAIZ / "docs" / "dados"
PILOTO = "-47.455,-23.478,-47.439,-23.463"


def arquivo(nome: str) -> dict:
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- rotas


def test_raiz(cliente):
    assert cliente.get("/").status_code == 200


def test_saude_com_o_usuario_da_api(cliente):
    resposta = cliente.get("/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


@pytest.mark.parametrize(
    ("rota", "nome"),
    [
        ("/camadas/risco", "risco_hand.geojson"),
        ("/camadas/registros", "ruas.geojson"),
        ("/areas", "recomendacoes.geojson"),
    ],
)
def test_sem_bbox_igual_ao_arquivo(cliente, rota, nome):
    resposta = cliente.get(rota)

    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/geo+json"
    assert resposta.json() == arquivo(nome)


@pytest.mark.parametrize("rota", ["/camadas/risco", "/camadas/registros", "/areas"])
def test_com_bbox_traz_parte_da_camada(cliente, rota):
    inteira = cliente.get(rota).json()["features"]
    resposta = cliente.get(rota, params={"bbox": PILOTO})

    assert resposta.status_code == 200
    parte = resposta.json()["features"]
    assert 0 < len(parte) <= len(inteira)


def test_ficha_de_uma_area(cliente):
    resposta = cliente.get("/areas/way-48448685")

    assert resposta.status_code == 200
    esperada = next(f for f in arquivo("recomendacoes.geojson")["features"] if f["id"] == "way-48448685")
    assert resposta.json() == esperada


def test_cenario_50_mm(cliente):
    resposta = cliente.get("/cenario", params={"chuva_mm": 50})

    assert resposta.status_code == 200
    assert resposta.json()  # a conta em si já é testada em api/tests/test_cenario.py


# ---------------------------------------------------------------- só leitura


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM areas",
        "INSERT INTO risco (classe, propriedades, geom) VALUES ('alto', '{}', NULL)",
        "UPDATE camadas_meta SET meta = '{}'",
        "TRUNCATE ruas",
        "CREATE TABLE intrusa (x int)",
    ],
)
def test_usuario_da_api_nao_grava(banco_api, sql):
    with banco_api.connect() as conexao:
        with pytest.raises(ProgrammingError, match="permission denied"):
            conexao.execute(text(sql))
        conexao.rollback()


def test_permissoes_conferidas_como_no_guia(banco_dono):
    # A consulta "Conferir" do docs/deploy.md (seção 3), sem a coluna do
    # neon_superuser, papel que só existe no Neon.
    with banco_dono.connect() as conexao:
        linha = conexao.execute(
            text("""
                SELECT
                    has_table_privilege('cityshield_api', 'areas', 'SELECT'),
                    has_table_privilege('cityshield_api', 'areas', 'DELETE'),
                    has_table_privilege('cityshield_api', 'risco', 'INSERT'),
                    (SELECT rolsuper FROM pg_roles WHERE rolname = 'cityshield_api'),
                    (SELECT rolconfig FROM pg_roles WHERE rolname = 'cityshield_api')
            """)
        ).one()

    pode_ler, pode_apagar, pode_gravar, superusuario, config = linha
    assert (pode_ler, pode_apagar, pode_gravar, superusuario) == (True, False, False, False)
    assert config == ["statement_timeout=5s"]
