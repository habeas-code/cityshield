"""Passo 2: drenagem e HAND (altura acima da drenagem mais próxima).

Para cada célula de 30 m, o HAND diz quantos metros ela está acima do córrego para
onde a água dela escorre. Quanto menor, mais fácil a água chegar ali. Ver
docs/decisoes.md, D6.

Método: Nobre et al. (2011), "Height Above the Nearest Drainage – a hydrologically
relevant new terrain model", Journal of Hydrology 404, 13–29.
https://doi.org/10.1016/j.jhydrol.2011.03.051

Faixas de risco (as mesmas classes do artigo):
    alto   0–5 m   (áreas encharcáveis, junto da drenagem)
    médio  5–15 m  (transição)
    baixo  > 15 m  (terreno alto)

Saídas:
    pipeline/dados/risco/hand.tif          raster com o HAND em metros (fora do git)
    web/public/dados/drenagem.geojson      córregos e rios calculados, no município
    web/public/dados/risco_hand.geojson    áreas de risco alto e médio, no município
"""

import json

import numpy as np
import rasterio
from pysheds.grid import Grid
from rasterio.features import shapes
from shapely import set_precision
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

from pipeline import relevo
from pipeline.caminhos import DADOS, REFERENCIA, SAIDA

# A partir de quanta área drenada uma célula vira córrego. 0,5 km² é um valor usual
# para córregos urbanos; ajustar só com justificativa, nunca para "melhorar" a validação.
LIMIAR_KM2 = 0.5

FAIXAS = [  # (classe, de, até) em metros de HAND
    ("alto", 0.0, 5.0),
    ("medio", 5.0, 15.0),
]

HAND_TIF = DADOS / "risco" / "hand.tif"
DRENAGEM = SAIDA / "drenagem.geojson"
RISCO = SAIDA / "risco_hand.geojson"
LIMITE = REFERENCIA / "limite_sorocaba.geojson"

SIMPLIFICAR = 0.00008  # graus (~8 m): deixa o GeoJSON leve sem mudar o desenho
PRECISAO = 0.00001     # graus (~1 m): arredonda as coordenadas
MENOR_MANCHA_GRAUS2 = 1500 / (102_000 * 110_600)  # ~1.500 m² (um lote) em Sorocaba


def _area_celula_m2(transform, lat):
    dx = abs(transform.a) * 111_320 * np.cos(np.radians(lat))
    dy = abs(transform.e) * 110_574
    return dx * dy


def _limite():
    with open(LIMITE, encoding="utf-8") as f:
        dados = json.load(f)
    return unary_union([shape(ft["geometry"]) for ft in dados["features"]])


def _gravar(caminho, features, fonte):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    colecao = {"type": "FeatureCollection", "fonte": fonte, "features": features}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(colecao, f, ensure_ascii=False, separators=(",", ":"))


def calcular(refazer=False):
    dem_tif = relevo.recortar()  # garante que o relevo existe
    if HAND_TIF.exists() and DRENAGEM.exists() and RISCO.exists() and not refazer:
        print(f"hand: já existe {HAND_TIF} (use --refazer para calcular de novo)")
        return

    # 1. Relevo hidrologicamente corrigido: tira poços e áreas planas que prendem a água
    grid = Grid.from_raster(str(dem_tif))
    dem = grid.read_raster(str(dem_tif))
    corrigido = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem)))

    # 2. Para onde a água escorre e quanta água passa em cada célula
    direcao = grid.flowdir(corrigido)
    acumulado = grid.accumulation(direcao)

    lat_media = (grid.extent[2] + grid.extent[3]) / 2
    celulas = LIMIAR_KM2 * 1e6 / _area_celula_m2(grid.affine, lat_media)
    rede = acumulado > celulas
    print(f"hand: córrego = mais de {LIMIAR_KM2} km² drenados ({celulas:.0f} células)")

    # 3. HAND: altura de cada célula acima da drenagem para onde ela escorre
    hand = np.asarray(grid.compute_hand(direcao, corrigido, rede), dtype="float32")
    hand[~np.isfinite(hand)] = -9999

    HAND_TIF.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dem_tif) as ref:
        perfil = ref.profile.copy()
    with rasterio.open(HAND_TIF, "w", **perfil) as destino:
        destino.write(hand, 1)
        destino.update_tags(METODO="HAND (Nobre et al., 2011)", LIMIAR_KM2=str(LIMIAR_KM2))

    municipio = _limite()

    # 4. Drenagem em linhas, recortada no município
    linhas = grid.extract_river_network(direcao, rede)
    trechos = []
    for ft in linhas["features"]:
        geom = shape(ft["geometry"]).intersection(municipio)
        if not geom.is_empty:
            trechos.append({"type": "Feature", "properties": {},
                            "geometry": mapping(set_precision(geom.simplify(SIMPLIFICAR), PRECISAO))})
    _gravar(DRENAGEM, trechos, f"Calculado do ANADEM v1; córrego > {LIMIAR_KM2} km² drenados")

    # 5. Faixas de risco em polígonos, recortadas no município
    valido = hand >= 0
    feicoes = []
    area_mun = municipio.area
    for classe, de, ate in FAIXAS:
        mascara = (valido & (hand >= de) & (hand < ate)).astype("uint8")
        partes = [shape(g) for g, v in shapes(mascara, mask=mascara == 1, transform=grid.affine) if v == 1]
        geom = set_precision(unary_union(partes).intersection(municipio).simplify(SIMPLIFICAR), PRECISAO)
        fracao = geom.area / area_mun
        # Uma feição por mancha: o mapa fatia e desenha aos poucos, em vez de um polígono gigante.
        # Manchas menores que um lote somem do desenho (a fração acima já foi calculada com elas).
        manchas = [p for p in getattr(geom, "geoms", [geom])
                   if p.geom_type == "Polygon" and p.area >= MENOR_MANCHA_GRAUS2]
        for mancha in manchas:
            feicoes.append({"type": "Feature",
                            "properties": {"classe": classe, "hand_min_m": de, "hand_max_m": ate},
                            "geometry": mapping(mancha)})
        print(f"hand: risco {classe} ({de:g}–{ate:g} m) = {fracao:.1%} do município, {len(manchas)} manchas")
    _gravar(RISCO, feicoes, "HAND (Nobre et al., 2011) sobre ANADEM v1")

    km = sum(shape(t["geometry"]).length for t in trechos) * 111.32 * np.cos(np.radians(lat_media))
    print(f"hand: ~{km:.0f} km de drenagem no município -> {DRENAGEM.name}, {RISCO.name}")
