"""Área de contribuição: quanto de cidade escoa para dentro de cada parque inundável.

Quando chove, a água desce pelo relevo. Um parque recebe a chuva que cai nele e a
enxurrada das ruas, quintais e telhados mais altos em volta. Esse pedaço de cidade é a
área de contribuição (a "microbacia" do parque).

Como calculamos, sobre o mesmo relevo do HAND (ANADEM, 30 m):

1. relevo corrigido e direção da água, como em hand.py;
2. partindo das células do parque, subimos o caminho da água célula por célula;
3. paramos nos córregos e no rio (mais de hand.LIMIAR_KM2 drenados, a mesma regra
   que desenha a drenagem no mapa).

O passo 3 é de propósito. O Parque das Águas do Abaeté fica na beira do Rio Sorocaba:
sem ele, a "área que escoa para o parque" seria a bacia do rio inteira (~470 km², vinda
de outras cidades), e a conta perderia o sentido. Então o número é só a enxurrada das
ruas e encostas em volta. A cheia do rio e dos córregos fica de fora, e o site diz isso.
"""

import math

import numpy as np
from pysheds.grid import Grid
from rasterio.features import rasterize
from shapely.geometry import shape

from pipeline import hand, relevo

# Direções D8 do pysheds (dirmap padrão) -> (linha, coluna) da célula de baixo
D8 = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}


class Drenagem:
    """Caminho da água no relevo, calculado uma vez e usado para todas as áreas."""

    def __init__(self):
        dem_tif = str(relevo.recortar())
        grid = Grid.from_raster(dem_tif)
        dem = grid.read_raster(dem_tif)
        corrigido = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem)))
        direcao = grid.flowdir(corrigido)
        acumulado = np.asarray(grid.accumulation(direcao)).ravel()
        direcao = np.asarray(direcao)

        self.altura, self.largura = direcao.shape
        self.affine = grid.affine
        lat = (grid.extent[2] + grid.extent[3]) / 2
        self.celula_m2 = abs(self.affine.a) * 111_320 * math.cos(math.radians(lat)) * abs(self.affine.e) * 110_574
        # Córregos e rio: onde a subida para (mesma regra de hand.py)
        self.corrego = acumulado > hand.LIMIAR_KM2 * 1e6 / self.celula_m2

        # Para cada célula, a célula para onde a água dela vai (-1 = sai do recorte)
        h, w = direcao.shape
        abaixo = np.full(h * w, -1, dtype=np.int64)
        lin, col = np.indices((h, w))
        for codigo, (dl, dc) in D8.items():
            m = direcao == codigo
            ll, cc = lin[m] + dl, col[m] + dc
            dentro = (ll >= 0) & (ll < h) & (cc >= 0) & (cc < w)
            abaixo[np.flatnonzero(m.ravel())[dentro]] = ll[dentro] * w + cc[dentro]
        # Índice invertido: quem manda água para cada célula (ordenado para busca rápida)
        origem = np.flatnonzero(abaixo >= 0)
        ordem = np.argsort(abaixo[origem], kind="stable")
        self._destino = abaixo[origem][ordem]
        self._origem = origem[ordem]

    def area_m2(self, geometria):
        """Área (m²) que escoa para dentro da geometria, sem passar por córrego ou rio."""
        dentro = rasterize([shape(geometria)], out_shape=(self.altura, self.largura),
                           transform=self.affine, all_touched=True).ravel().astype(bool)
        visto = dentro.copy()
        frente = np.flatnonzero(dentro)
        while frente.size:
            ini = np.searchsorted(self._destino, frente, "left")
            fim = np.searchsorted(self._destino, frente, "right")
            if not (fim > ini).any():
                break
            acima = np.concatenate([self._origem[a:b] for a, b in zip(ini, fim) if b > a])
            acima = acima[~visto[acima] & ~self.corrego[acima]]
            visto[acima] = True
            frente = acima
        return float(visto.sum() * self.celula_m2)
