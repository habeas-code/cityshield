"""Declividade do terreno em cada área candidata, para avisar onde a solução pede cuidado.

A declividade (%) é quanto o terreno sobe a cada 100 m na horizontal. Sai do mesmo relevo
do HAND (ANADEM, 30 m): para cada célula, a inclinação em relação às vizinhas. Em cada área
usamos a mediana das células que ela toca.

Com células de 30 m, um estacionamento pequeno tem poucas células e o número é indicativo:
serve para avisar "conferir em campo", nunca para excluir uma área.
"""

import math

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.mask import mask

from pipeline import relevo


class Declividade:
    """Mapa de declividade calculado uma vez e consultado por área."""

    def __init__(self):
        with rasterio.open(relevo.recortar()) as fonte:
            z = fonte.read(1).astype("float64")
            z[z < -100] = np.nan
            lat = (fonte.bounds.top + fonte.bounds.bottom) / 2
            dx = fonte.res[0] * 111_320 * math.cos(math.radians(lat))
            dy = fonte.res[1] * 110_574
            gy, gx = np.gradient(z, dy, dx)
            pct = np.nan_to_num(np.hypot(gx, gy) * 100, nan=-1).astype("float32")
            perfil = fonte.profile.copy()
        perfil.update(dtype="float32", count=1, nodata=-1)
        self._memoria = MemoryFile()
        self._raster = self._memoria.open(**perfil)
        self._raster.write(pct, 1)

    def mediana_pct(self, geometria):
        """Declividade mediana (%) dentro da área, ou None se ela não cair no relevo."""
        try:
            recorte, _ = mask(self._raster, [geometria], crop=True, all_touched=True, filled=False)
        except ValueError:
            return None
        valores = recorte[0].compressed()
        valores = valores[valores >= 0]
        return round(float(np.median(valores)), 1) if valores.size else None

    def fechar(self):
        self._raster.close()
        self._memoria.close()
