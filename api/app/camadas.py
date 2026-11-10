"""Leitura das camadas do mapa no banco (#11).

O próprio PostGIS monta o GeoJSON, já no formato dos arquivos de docs/dados/
(plano B, D10):

  - cada linha vira uma feição: json_build_object com as propriedades (JSONB
    gravado pela carga, db/carga.py) e a geometria (ST_AsGeoJSON);
  - json_agg junta as feições na ordem do arquivo (ORDER BY id);
  - o topo leva "type", as chaves de camadas_meta (fonte...) e "features",
    nessa ordem. A fonte vai junto em toda resposta (D11).

O Python só repassa o texto, sem remontar a geometria.

O filtro pela área visível do mapa é "geom && ST_MakeEnvelope(...)": o &&
pergunta se o retângulo da geometria encosta no retângulo pedido, e é essa
pergunta que o índice GIST responde rápido. Sem bbox, o retângulo é o mundo
inteiro: a mesma consulta devolve a camada toda.

SQL fixo; os quatro números do retângulo vão como parâmetros.
"""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.banco import engine

log = logging.getLogger(__name__)

# xmin, ymin, xmax, ymax em lon/lat: sem bbox, pede o mundo inteiro.
MUNDO = (-180.0, -90.0, 180.0, 90.0)

CONSULTAS = {
    # Manchas de risco pelo HAND (tabela risco).
    "risco": """
        SELECT json_object_agg(chave, valor ORDER BY ordem, chave)::text
        FROM (
            SELECT 0 AS ordem, 'type' AS chave, to_json('FeatureCollection'::text) AS valor
            UNION ALL
            SELECT 1, m.chave, m.valor::json
            FROM camadas_meta, jsonb_each(meta) AS m(chave, valor)
            WHERE camada = 'risco'
            UNION ALL
            SELECT 2, 'features', COALESCE(
                (SELECT json_agg(
                            json_build_object(
                                'type', 'Feature',
                                'properties', propriedades,
                                'geometry', ST_AsGeoJSON(geom)::json
                            ) ORDER BY id)
                 FROM risco
                 WHERE geom && ST_MakeEnvelope(:xmin, :ymin, :xmax, :ymax, 4326)),
                '[]'::json)
        ) AS partes
    """,
    # Registros da Defesa Civil por rua (tabela ruas): concentração por rua,
    # nunca endereço.
    "registros": """
        SELECT json_object_agg(chave, valor ORDER BY ordem, chave)::text
        FROM (
            SELECT 0 AS ordem, 'type' AS chave, to_json('FeatureCollection'::text) AS valor
            UNION ALL
            SELECT 1, m.chave, m.valor::json
            FROM camadas_meta, jsonb_each(meta) AS m(chave, valor)
            WHERE camada = 'ruas'
            UNION ALL
            SELECT 2, 'features', COALESCE(
                (SELECT json_agg(
                            json_build_object(
                                'type', 'Feature',
                                'properties', propriedades,
                                'geometry', ST_AsGeoJSON(geom)::json
                            ) ORDER BY id)
                 FROM ruas
                 WHERE geom && ST_MakeEnvelope(:xmin, :ymin, :xmax, :ymax, 4326)),
                '[]'::json)
        ) AS partes
    """,
}


class CamadaIndisponivel(Exception):
    """O banco não respondeu (fora do ar, lento demais ou sem as tabelas)."""


def consultar(sql: str, parametros: dict, nome: str):
    """Roda uma consulta que devolve um valor só (ou nada, se não houver linha).

    Qualquer falha do banco vira CamadaIndisponivel, que a rota transforma em
    503. Usada pelas camadas e pelas áreas (app/areas.py).
    """
    try:
        with engine.connect() as conexao:
            return conexao.execute(text(sql), parametros).scalar_one_or_none()
    except SQLAlchemyError as erro:
        # O detalhe vai só para o log do servidor, nunca para quem chamou a API.
        log.warning("%s indisponível: %s", nome, erro.__class__.__name__)
        raise CamadaIndisponivel(nome) from None


def parametros_bbox(bbox: tuple[float, float, float, float] | None) -> dict:
    """Os quatro números do retângulo; sem bbox, o mundo inteiro."""
    xmin, ymin, xmax, ymax = bbox or MUNDO
    return {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}


def camada_geojson(nome: str, bbox: tuple[float, float, float, float] | None = None) -> str:
    """Devolve a camada como texto GeoJSON, inteira ou só dentro do bbox."""
    return consultar(CONSULTAS[nome], parametros_bbox(bbox), nome)
