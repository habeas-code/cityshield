"""Leitura das áreas candidatas no banco (#18).

Mesmo esquema das camadas (app/camadas.py): o PostGIS monta o GeoJSON no
formato do recomendacoes.geojson (plano B, D10), com o topo vindo de
camadas_meta (fonte, area, aviso, metodo, parametros). As áreas saem na ordem
da fila (posicao 1 = mais indicada) e cada feição traz o id também no topo,
como no arquivo.

ST_AsGeoJSON(geom, 15): as coordenadas das áreas vêm do OSM com até 15 casas
decimais. O padrão do PostGIS (9 casas) arredondaria a nona casa (~0,1 mm);
com 15, saem exatamente como no arquivo.

SQL fixo; os valores vão como parâmetros.
"""

import re

from app.camadas import consultar, parametros_bbox

# Códigos das soluções (docs/recomendacoes.md, "O que o arquivo traz").
SOLUCOES = ("parque_inundavel", "jardim_chuva", "piso_permeavel", "telhado_verde")

# id fixo da área, vindo do OpenStreetMap: way-48448685, node-..., relation-...
FORMATO_ID = re.compile(r"(node|way|relation)-[0-9]+")

LISTA = """
    SELECT json_object_agg(chave, valor ORDER BY ordem, chave)::text
    FROM (
        SELECT 0 AS ordem, 'type' AS chave, to_json('FeatureCollection'::text) AS valor
        UNION ALL
        SELECT 1, m.chave, m.valor::json
        FROM camadas_meta, jsonb_each(meta) AS m(chave, valor)
        WHERE camada = 'areas'
        UNION ALL
        SELECT 2, 'features', COALESCE(
            (SELECT json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'properties', propriedades,
                            'geometry', ST_AsGeoJSON(geom, 15)::json,
                            'id', id
                        ) ORDER BY posicao)
             FROM areas
             WHERE geom && ST_MakeEnvelope(:xmin, :ymin, :xmax, :ymax, 4326)
               AND (CAST(:solucao AS text) IS NULL OR solucao = CAST(:solucao AS text))),
            '[]'::json)
    ) AS partes
"""

UMA = """
    SELECT json_build_object(
               'type', 'Feature',
               'properties', propriedades,
               'geometry', ST_AsGeoJSON(geom, 15)::json,
               'id', id
           )::text
    FROM areas
    WHERE id = :id
"""

def areas_geojson(bbox=None, solucao: str | None = None) -> str:
    """Todas as áreas (ou só as do bbox e da solução) como FeatureCollection."""
    return consultar(LISTA, {**parametros_bbox(bbox), "solucao": solucao}, "areas")


def area_geojson(id_area: str) -> str | None:
    """Uma área como Feature, ou None se o id não existe."""
    return consultar(UMA, {"id": id_area}, "areas")

