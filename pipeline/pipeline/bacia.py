"""Bacia do Córrego Itanguá desenhada pelo relevo.

Para que serve: o terceiro teste da validação (lai.py) usa registros da Defesa Civil
só da "Bacia do Itanguá". Comparar esses registros com as ruas da cidade inteira pode
inflar o resultado, porque uma bacia de vale tem mais ruas baixas que a média da
cidade. Com a bacia desenhada, a comparação também é feita só com as ruas de dentro
dela (o teste mais duro).

Como desenhamos, sobre o mesmo relevo do HAND (ANADEM, 30 m):

1. relevo corrigido, direção da água e água acumulada, como em hand.py;
2. a foz: o ponto mais abaixo do Córrego Itanguá no OpenStreetMap (way 1081818781),
   onde ele chega ao Rio Sorocaba. Usamos um ponto ~300 m antes da foz, para não
   cair no próprio rio, e encostamos na célula de drenagem mais próxima que não é
   o rio (entre LIMIAR_MIN_KM2 e LIMIAR_MAX_KM2 drenados);
3. a bacia: todas as células cuja água passa por esse ponto (pysheds, catchment).

A "Bacia do Itanguá" da Defesa Civil é a divisão de trabalho deles; pode não ser
igual à bacia do relevo. Por isso o teste conta também quantos registros caem fora.

Saída: web/public/dados/bacia_itangua.geojson (cópia em docs/dados/)
"""

import json

import numpy as np
from pysheds.grid import Grid
from rasterio.features import shapes
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

from pipeline import hand, relevo
from pipeline.caminhos import SAIDA

SAIDA_GEOJSON = SAIDA / "bacia_itangua.geojson"

# ~300 m antes da foz do Córrego Itanguá no Rio Sorocaba (OSM way 1081818781, que
# termina em -47.5233302, -23.4288418).
PERTO_DA_FOZ = (-47.5228, -23.4315)
LIMIAR_MIN_KM2 = 5      # é córrego de verdade, não enxurrada de rua
LIMIAR_MAX_KM2 = 200    # não é o Rio Sorocaba (centenas de km² drenados)


def _celula_km2(grid):
    lat = (grid.extent[2] + grid.extent[3]) / 2
    return hand._area_celula_m2(grid.affine, lat) / 1e6


def desenhar(refazer=False):
    """Desenha a bacia e grava o GeoJSON. Devolve a geometria (shapely, em graus)."""
    if SAIDA_GEOJSON.exists() and not refazer:
        print(f"bacia: já existe {SAIDA_GEOJSON} (use --refazer para refazer)")
        return carregar()

    dem_tif = str(relevo.recortar())
    grid = Grid.from_raster(dem_tif)
    dem = grid.read_raster(dem_tif)
    corrigido = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem)))
    direcao = grid.flowdir(corrigido)
    acumulado = grid.accumulation(direcao)

    km2 = np.asarray(acumulado) * _celula_km2(grid)
    alvo = (km2 > LIMIAR_MIN_KM2) & (km2 < LIMIAR_MAX_KM2)
    # célula de córrego (não rio) mais perto do ponto escolhido, pelo centro da célula
    linhas, colunas = np.nonzero(alvo)
    a = grid.affine
    xs, ys = a.c + (colunas + 0.5) * a.a, a.f + (linhas + 0.5) * a.e
    i = int(np.argmin((xs - PERTO_DA_FOZ[0]) ** 2 + (ys - PERTO_DA_FOZ[1]) ** 2))
    x, y = float(xs[i]), float(ys[i])
    drenado = float(km2[linhas[i], colunas[i]])

    # pelo índice da célula: pela coordenada, o pysheds pode arredondar para a vizinha
    # (fora do córrego) e devolver uma bacia de uma célula só
    bacia = grid.catchment(x=int(colunas[i]), y=int(linhas[i]), fdir=direcao, xytype="index")
    mascara = np.asarray(bacia).astype("uint8")
    pedacos = [shape(g) for g, v in shapes(mascara, mask=mascara.astype(bool), transform=grid.affine) if v]
    geometria = unary_union(pedacos)
    # fica só o maior pedaço (o resto são células soltas na borda)
    if geometria.geom_type == "MultiPolygon":
        geometria = max(geometria.geoms, key=lambda g: g.area)

    colecao = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": mapping(geometria), "properties": {
            "nome": "Bacia do Córrego Itanguá (pelo relevo)",
            "foz_usada": [round(x, 6), round(y, 6)],
            "area_km2": round(drenado, 2),
            "fonte": "ANADEM v1 (30 m) + direção da água (pysheds); foz pelo OpenStreetMap",
        }}],
    }
    SAIDA_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_GEOJSON.write_text(json.dumps(colecao, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"bacia: Itanguá com {drenado:.1f} km² drenados na foz -> {SAIDA_GEOJSON.name}")
    return geometria


def carregar():
    colecao = json.loads(SAIDA_GEOJSON.read_text(encoding="utf-8"))
    return shape(colecao["features"][0]["geometry"])
