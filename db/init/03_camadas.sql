-- Tabelas das camadas do mapa (#10).
--
-- Cada feição dos GeoJSON de docs/dados/ vira uma linha:
--   geom         a geometria, em lon/lat (SRID 4326), com o tipo original
--   propriedades TODAS as propriedades da feição, em JSONB, para a API
--                devolver o mesmo conteúdo dos arquivos
--   colunas      só o que a API filtra ou ordena (classe, rua, nota...)
--
-- Toda geometria tem índice GIST: é ele que deixa rápida a pergunta
-- "o que aparece na área visível do mapa?" (geom && ST_MakeEnvelope(...)).
--
-- Pode rodar quantas vezes quiser (IF NOT EXISTS). No Docker roda sozinho
-- quando o banco é criado; a carga (db/carga.py) também roda este arquivo
-- antes de inserir, para funcionar num banco que já existia e no Neon.

-- Manchas de risco pelo HAND (risco_hand.geojson). Hoje são todas Polygon,
-- mas uma mancha em vários pedaços viria como MultiPolygon: as duas entram.
CREATE TABLE IF NOT EXISTS risco (
    id           serial PRIMARY KEY,  -- ordem do arquivo
    classe       text NOT NULL,       -- alto, medio...
    propriedades jsonb NOT NULL,
    geom         geometry(Geometry, 4326) NOT NULL
        CHECK (GeometryType(geom) IN ('POLYGON', 'MULTIPOLYGON'))
);
CREATE INDEX IF NOT EXISTS risco_geom_idx ON risco USING gist (geom);

-- Córregos calculados do relevo (drenagem.geojson). O arquivo mistura
-- LineString e MultiLineString, e o tipo original é mantido.
CREATE TABLE IF NOT EXISTS drenagem (
    id           serial PRIMARY KEY,
    propriedades jsonb NOT NULL,
    geom         geometry(Geometry, 4326) NOT NULL
        CHECK (GeometryType(geom) IN ('LINESTRING', 'MULTILINESTRING'))
);
CREATE INDEX IF NOT EXISTS drenagem_geom_idx ON drenagem USING gist (geom);

-- Registros da Defesa Civil agregados por rua (ruas.geojson): concentração
-- por rua, nunca endereço. Os dados com endereço ficam em dados_privados/
-- e não entram no banco.
CREATE TABLE IF NOT EXISTS ruas (
    id           serial PRIMARY KEY,
    rua          text NOT NULL UNIQUE,
    registros    integer NOT NULL,
    propriedades jsonb NOT NULL,
    geom         geometry(Point, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS ruas_geom_idx ON ruas USING gist (geom);

-- Áreas candidatas a solução verde (recomendacoes.geojson). Polygon ou
-- MultiPolygon (no OSM, uma área pode ter vários pedaços).
CREATE TABLE IF NOT EXISTS areas (
    id           text PRIMARY KEY,         -- ex.: way-48448685 (do OSM)
    solucao      text NOT NULL,            -- parque_inundavel, jardim_chuva...
    nota         integer NOT NULL,
    posicao      integer NOT NULL UNIQUE,  -- 1 = mais indicada
    propriedades jsonb NOT NULL,
    geom         geometry(Geometry, 4326) NOT NULL
        CHECK (GeometryType(geom) IN ('POLYGON', 'MULTIPOLYGON'))
);
CREATE INDEX IF NOT EXISTS areas_geom_idx ON areas USING gist (geom);

-- O que vem no topo de cada arquivo, fora as feições: fonte, area, aviso,
-- metodo, parametros. A API devolve junto, para a fonte nunca se perder (D11).
CREATE TABLE IF NOT EXISTS camadas_meta (
    camada text PRIMARY KEY,   -- risco, drenagem, ruas, areas
    meta   jsonb NOT NULL
);
