"""Passo 4: áreas candidatas a soluções verdes na área piloto.

Busca no OpenStreetMap os lugares onde uma solução verde poderia ser estudada, no raio
da área piloto (docs/decisoes.md, D3):

    estacionamento  pátios e estacionamentos abertos   (piso permeável, jardim de chuva)
    area_verde      parques, praças, jardins, gramados (jardim de chuva, parque inundável)
    telhado         prédios com mais de 1.000 m²        (telhado verde)

Para cada área calcula o tamanho e quanto dela está em cada faixa de risco do HAND.
A escolha da solução e a nota de prioridade são o próximo passo (#16).

Áreas do OSM são CANDIDATAS A ESTUDO, não terrenos disponíveis: o mapeamento de prédios
em Sorocaba é parcial e uma praça pode já ter outro uso.

Saída: web/public/dados/areas_candidatas.geojson
"""

import json
import time
import urllib.parse
import urllib.request

import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import LineString, Point, mapping
from shapely.ops import polygonize, transform, unary_union

from pipeline import hand
from pipeline.caminhos import DADOS, SAIDA
from pipeline.validacao import OVERPASS, PARA_GRAUS, PARA_UTM, PILOTO, RAIO_PILOTO_M

CACHE = DADOS / "osm" / "areas_piloto.json"
SAIDA_GEOJSON = SAIDA / "areas_candidatas.geojson"

TELHADO_MINIMO_M2 = 1000
AREA_MINIMA_M2 = 200         # menor que isso não comporta uma solução útil
SOBREPOSICAO_MAXIMA = 0.8    # área verde 80% dentro de outra maior é a mesma área (gramado dentro do parque)

ROTULOS = {"estacionamento": "Estacionamento", "area_verde": "Área verde", "telhado": "Telhado"}


def _consulta():
    lon, lat = PILOTO
    perto = f"(around:{RAIO_PILOTO_M},{lat},{lon})"
    return f"""[out:json][timeout:120];
(
  nwr["amenity"="parking"]["parking"!~"underground|multi-storey"]{perto};
  nwr["leisure"~"^(park|garden|recreation_ground)$"]{perto};
  nwr["landuse"~"^(grass|recreation_ground|village_green)$"]{perto};
  nwr["place"="square"]{perto};
  way["building"]{perto};
  relation["building"]{perto};
);
out geom tags;"""


def _baixar(refazer):
    if CACHE.exists() and not refazer:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    print("areas: baixando áreas do OpenStreetMap no raio do piloto")
    corpo = urllib.parse.urlencode({"data": _consulta()}).encode()
    pedido = urllib.request.Request(OVERPASS, data=corpo, headers={"User-Agent": "cityshield-pipeline/0.1"})
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(pedido, timeout=180) as resposta:
                dados = json.load(resposta)
            break
        except OSError:
            if tentativa == 2:
                raise
            time.sleep(15)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(dados), encoding="utf-8")
    return dados


def _poligono(el):
    """Polígono (em graus) de um way fechado ou de um multipolygon do OSM."""
    if el["type"] == "way":
        pts = [(p["lon"], p["lat"]) for p in el.get("geometry", [])]
        if len(pts) >= 4 and pts[0] == pts[-1]:
            return unary_union(list(polygonize([LineString(pts)])))
        return None
    if el["type"] == "relation":
        linhas = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                  for m in el.get("members", [])
                  if m.get("role") in ("outer", "") and len(m.get("geometry", [])) >= 2]
        partes = list(polygonize(unary_union(linhas))) if linhas else []
        return unary_union(partes) if partes else None
    return None


def _tipo(tags):
    if tags.get("amenity") == "parking":
        return "estacionamento"
    if "building" in tags:
        return "telhado"
    return "area_verde"


def _faixas(fonte, poligono):
    """Fração da área em cada faixa de HAND e o HAND mínimo (ponto mais baixo)."""
    try:
        recorte, _ = mask(fonte, [mapping(poligono)], crop=True, all_touched=True, filled=False)
    except ValueError:
        return None
    valores = recorte[0].compressed()
    valores = valores[valores >= 0]
    if valores.size == 0:
        return None
    total = valores.size
    return {
        "fracao_alto": round(float((valores < 5).sum()) / total, 3),
        "fracao_medio": round(float(((valores >= 5) & (valores < 15)).sum()) / total, 3),
        "fracao_baixo": round(float((valores >= 15).sum()) / total, 3),
        "hand_min_m": round(float(valores.min()), 1),
    }


def extrair(refazer=False):
    hand.calcular()  # garante relevo e HAND
    if SAIDA_GEOJSON.exists() and not refazer:
        print(f"areas: já existe {SAIDA_GEOJSON} (use --refazer para refazer)")
        return

    centro_utm = transform(PARA_UTM, Point(PILOTO))
    candidatas = []
    for el in _baixar(refazer)["elements"]:
        tags = el.get("tags", {})
        poligono = _poligono(el)
        if poligono is None or poligono.is_empty:
            continue
        geom_utm = transform(PARA_UTM, poligono).buffer(0)
        area = geom_utm.area
        tipo = _tipo(tags)
        if area < AREA_MINIMA_M2 or (tipo == "telhado" and area < TELHADO_MINIMO_M2):
            continue
        if geom_utm.centroid.distance(centro_utm) > RAIO_PILOTO_M:
            continue
        candidatas.append({"tipo": tipo, "tags": tags, "osm": f"{el['type']}/{el['id']}",
                           "geom_utm": geom_utm, "area": area})

    # Tira duplicadas: gramado dentro de parque, praça mapeada duas vezes etc.
    candidatas.sort(key=lambda c: -c["area"])
    mantidas = []
    for c in candidatas:
        repetida = any(
            m["tipo"] == c["tipo"] and m["geom_utm"].intersection(c["geom_utm"]).area >= SOBREPOSICAO_MAXIMA * c["area"]
            for m in mantidas
        )
        if not repetida:
            mantidas.append(c)

    feicoes = []
    with rasterio.open(hand.HAND_TIF) as fonte:
        for c in mantidas:
            poligono = transform(PARA_GRAUS, c["geom_utm"])
            faixas = _faixas(fonte, poligono)
            if faixas is None:
                continue
            nome = c["tags"].get("name")
            feicoes.append({
                "type": "Feature",
                "properties": {
                    "tipo": c["tipo"],
                    "rotulo": ROTULOS[c["tipo"]],
                    "nome": nome,
                    "area_m2": round(c["area"]),
                    **faixas,
                    "osm": c["osm"],
                },
                "geometry": mapping(poligono.simplify(0.000005)),
            })

    SAIDA_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    colecao = {
        "type": "FeatureCollection",
        "fonte": "OpenStreetMap (ODbL) via Overpass API; risco: HAND sobre ANADEM v1",
        "area": f"raio de {RAIO_PILOTO_M} m em torno de {PILOTO[1]}, {PILOTO[0]}",
        "aviso": "Áreas candidatas a estudo, não terrenos disponíveis. Mapeamento de prédios no OSM é parcial.",
        "features": feicoes,
    }
    SAIDA_GEOJSON.write_text(json.dumps(colecao, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    for tipo, rotulo in ROTULOS.items():
        doTipo = [f["properties"] for f in feicoes if f["properties"]["tipo"] == tipo]
        if not doTipo:
            print(f"areas: {rotulo}: nenhuma")
            continue
        area = sum(p["area_m2"] for p in doTipo)
        em_alto = sum(1 for p in doTipo if p["fracao_alto"] >= 0.5)
        print(f"areas: {rotulo}: {len(doTipo)} áreas, {area / 10_000:.1f} ha, {em_alto} com metade ou mais no risco alto")
    print(f"areas: {len(feicoes)} áreas candidatas -> {SAIDA_GEOJSON.name}")
    return np.array([f["properties"]["area_m2"] for f in feicoes])
