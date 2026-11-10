"""Carga das camadas do mapa no PostGIS (#10).

Lê os GeoJSON públicos de docs/dados/ e grava nas tabelas de
db/init/03_camadas.sql. Roda sozinho no "docker compose up" (serviço "carga"),
antes da API subir.

Como funciona:
  1. lê os quatro arquivos e confere que nenhum está vazio;
  2. numa transação só ("tudo ou nada"): cria as tabelas se faltarem, apaga o
     conteúdo antigo (TRUNCATE) e insere o novo;
  3. confere, antes de confirmar, que cada tabela ficou com uma linha por
     feição do arquivo. Se algo não bater, o banco desfaz tudo e as camadas
     antigas continuam lá.

Rodar duas vezes dá o mesmo resultado. Toda consulta é parametrizada: os
valores vão separados do SQL, nunca colados no texto do comando.

Só lê docs/dados/. Nada de dados_privados/ entra no banco público.
"""

import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

PASTA_DB = Path(__file__).resolve().parent
PASTA_DADOS = PASTA_DB.parent / "docs" / "dados"
SQL_TABELAS = PASTA_DB / "init" / "03_camadas.sql"

ARQUIVOS = {
    "risco": "risco_hand.geojson",
    "drenagem": "drenagem.geojson",
    "ruas": "ruas.geojson",
    "areas": "recomendacoes.geojson",
}

# SQL fixo; os valores entram pelos parâmetros (:nome), nunca no texto.
# Geometria: o PostGIS lê o GeoJSON (ST_GeomFromGeoJSON) e marca como
# lon/lat (SRID 4326), mantendo o tipo original.
INSERIR = {
    "risco": """
        INSERT INTO risco (classe, propriedades, geom)
        VALUES (:classe, CAST(:propriedades AS jsonb),
                ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
    """,
    "drenagem": """
        INSERT INTO drenagem (propriedades, geom)
        VALUES (CAST(:propriedades AS jsonb),
                ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
    """,
    "ruas": """
        INSERT INTO ruas (rua, registros, propriedades, geom)
        VALUES (:rua, :registros, CAST(:propriedades AS jsonb),
                ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
    """,
    "areas": """
        INSERT INTO areas (id, solucao, nota, posicao, propriedades, geom)
        VALUES (:id, :solucao, :nota, :posicao, CAST(:propriedades AS jsonb),
                ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
    """,
}

CONTAR = {
    "risco": "SELECT count(*) FROM risco",
    "drenagem": "SELECT count(*) FROM drenagem",
    "ruas": "SELECT count(*) FROM ruas",
    "areas": "SELECT count(*) FROM areas",
}

INSERIR_META = (
    "INSERT INTO camadas_meta (camada, meta) VALUES (:camada, CAST(:meta AS jsonb))"
)

APAGAR = "TRUNCATE risco, drenagem, ruas, areas, camadas_meta RESTART IDENTITY"

# O usuário do banco tem limite de 5 s por consulta (02_statement_timeout.sql),
# pensado para a API. A carga ganha mais folga, só dentro da transação dela.
FOLGA = "SET LOCAL statement_timeout = '60s'"


class ErroCarga(Exception):
    """Algo nos arquivos ou no banco não está como deveria."""


# ---------------------------------------------------------------- arquivos


def caminho_seguro(caminho: Path) -> Path:
    """Garante que o arquivo é público: nada dentro de dados_privados/."""
    real = caminho.resolve()
    if "dados_privados" in real.parts:
        raise ErroCarga(f"Recusado: {real} está em dados_privados/ e não vai para o banco.")
    return real


def ler_geojson(caminho: Path) -> dict:
    """Lê um arquivo e confere se é uma FeatureCollection."""
    caminho = caminho_seguro(caminho)
    if not caminho.is_file():
        raise ErroCarga(f"Arquivo não encontrado: {caminho}")
    colecao = json.loads(caminho.read_text(encoding="utf-8"))
    if colecao.get("type") != "FeatureCollection" or not isinstance(colecao.get("features"), list):
        raise ErroCarga(f"{caminho.name} não é uma FeatureCollection.")
    return colecao


def meta_do_topo(colecao: dict) -> dict:
    """Tudo o que vem no topo do arquivo, menos as feições (fonte, aviso...)."""
    return {chave: valor for chave, valor in colecao.items() if chave not in ("type", "features")}


def _base(feicao: dict) -> dict:
    """O que toda linha tem: propriedades e geometria, como texto JSON."""
    if not feicao.get("geometry"):
        raise ErroCarga("Feição sem geometria.")
    return {
        "propriedades": json.dumps(feicao.get("properties") or {}, ensure_ascii=False),
        "geom": json.dumps(feicao["geometry"]),
    }


def linha_risco(feicao: dict) -> dict:
    return {**_base(feicao), "classe": feicao["properties"]["classe"]}


def linha_drenagem(feicao: dict) -> dict:
    return _base(feicao)


def linha_ruas(feicao: dict) -> dict:
    p = feicao["properties"]
    return {**_base(feicao), "rua": p["rua"], "registros": p["registros"]}


def linha_areas(feicao: dict) -> dict:
    p = feicao["properties"]
    # O arquivo repete o id no topo da feição; os dois têm que ser iguais.
    if "id" in feicao and feicao["id"] != p["id"]:
        raise ErroCarga(f"Área com dois ids diferentes: {feicao['id']} e {p['id']}.")
    return {
        **_base(feicao),
        "id": p["id"],
        "solucao": p["solucao"],
        "nota": p["nota"],
        "posicao": p["posicao"],
    }


MONTAR = {
    "risco": linha_risco,
    "drenagem": linha_drenagem,
    "ruas": linha_ruas,
    "areas": linha_areas,
}


def conferir_arquivo(arquivo: str, feicoes: int) -> None:
    """Um arquivo sem feições apagaria a camada do mapa: quase sempre é erro."""
    if feicoes < 1:
        raise ErroCarga(f"{arquivo} não tem nenhuma feição. Rode o pipeline de novo.")


def conferir_banco(camada: str, no_banco: int, no_arquivo: int) -> None:
    """O banco tem que ter uma linha por feição do arquivo: nem menos, nem mais.

    Não há número fixo: se o pipeline gerar mais ou menos feições, a carga
    acompanha o arquivo.
    """
    if no_banco != no_arquivo:
        raise ErroCarga(
            f"Camada {camada}: o arquivo tem {no_arquivo} feições, "
            f"mas o banco ficou com {no_banco} linhas."
        )


def montar_camadas(pasta: Path = PASTA_DADOS) -> dict:
    """Lê os arquivos e monta as linhas de cada tabela, sem tocar no banco.

    Devolve {camada: {"linhas": [...], "meta": {...}}}.
    """
    camadas = {}
    for camada, arquivo in ARQUIVOS.items():
        colecao = ler_geojson(pasta / arquivo)
        try:
            linhas = [MONTAR[camada](f) for f in colecao["features"]]
        except KeyError as falta:
            raise ErroCarga(f"{arquivo}: falta a propriedade {falta} numa feição.") from None
        conferir_arquivo(arquivo, len(linhas))
        camadas[camada] = {"linhas": linhas, "meta": meta_do_topo(colecao)}
    return camadas


# ---------------------------------------------------------------- banco


def gravar(conexao, camadas: dict) -> dict:
    """Grava tudo numa transação já aberta e devolve as contagens do banco."""
    conexao.execute(text(FOLGA))
    conexao.exec_driver_sql(SQL_TABELAS.read_text(encoding="utf-8"))
    conexao.execute(text(APAGAR))
    for camada, dados in camadas.items():
        conexao.execute(text(INSERIR[camada]), dados["linhas"])
        conexao.execute(
            text(INSERIR_META),
            {"camada": camada, "meta": json.dumps(dados["meta"], ensure_ascii=False)},
        )
    contagens = {}
    for camada in camadas:
        contagens[camada] = conexao.execute(text(CONTAR[camada])).scalar_one()
        conferir_banco(camada, contagens[camada], len(camadas[camada]["linhas"]))
    return contagens


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Falta a variável DATABASE_URL. Copie o .env.example para .env.", file=sys.stderr)
        return 1

    try:
        camadas = montar_camadas()
        engine = create_engine(url, connect_args={"connect_timeout": 10})
        with engine.begin() as conexao:  # sai com COMMIT; com erro, ROLLBACK
            contagens = gravar(conexao, camadas)
    except ErroCarga as erro:
        print(f"Carga cancelada: {erro}", file=sys.stderr)
        return 1
    except SQLAlchemyError as erro:
        # Só o tipo e a primeira linha: o endereço do banco não vai para o log.
        motivo = str(getattr(erro, "orig", erro)).splitlines()[0]
        print(f"Carga cancelada: erro no banco ({erro.__class__.__name__}): {motivo}", file=sys.stderr)
        return 1

    resumo = ", ".join(f"{camada} {n}" for camada, n in contagens.items())
    print(f"Carga ok: {resumo}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
