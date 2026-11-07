"""Passo 1: recorta o relevo ANADEM da área de estudo.

O ANADEM é um modelo digital de TERRENO (sem prédios e sem árvores) feito a partir
do Copernicus GLO-30, com 30 m de resolução. Ver docs/decisoes.md, D5.

Fonte: Laipelt et al. (2024), "ANADEM: A Digital Terrain Model for South America",
Remote Sensing 16(13), 2321. https://doi.org/10.3390/rs16132321
Download: https://www.ufrgs.br/hge/download-anadem/ (tiles MGRS hospedados pela ANA)

O tile inteiro tem ~2 GB, mas é dividido em blocos. O GDAL lê pela internet só os
blocos que cobrem a área de estudo (~9 MB), sem baixar o arquivo todo.
"""

from pathlib import Path

import rasterio
from rasterio.windows import from_bounds

# Sorocaba fica na zona UTM 23, faixa de latitude K.
URL_TILE = "https://metadados.snirh.gov.br/files/anadem_v1_tiles/anadem_v1_23K.tif"

# Município de Sorocaba com margem, para incluir o Rio Sorocaba desde a represa de
# Itupararanga e os córregos que chegam à cidade (oeste, sul, leste, norte).
AREA_ESTUDO = (-47.75, -23.75, -47.20, -23.25)

SAIDA = Path(__file__).resolve().parent.parent / "dados" / "relevo" / "anadem_sorocaba.tif"

OPCOES_GDAL = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",  # não lista a pasta remota
    "GDAL_HTTP_MULTIRANGE": "YES",                # pede vários blocos por requisição
    "GDAL_HTTP_MAX_RETRY": "3",
    "GDAL_HTTP_RETRY_DELAY": "2",
}


def recortar(url=URL_TILE, area=AREA_ESTUDO, saida=SAIDA, refazer=False):
    """Lê só a janela da área de estudo e grava um GeoTIFF local."""
    saida = Path(saida)
    if saida.exists() and not refazer:
        print(f"relevo: já existe {saida} (use --refazer para baixar de novo)")
        return saida

    saida.parent.mkdir(parents=True, exist_ok=True)
    print(f"relevo: lendo a área {area} de {url}")

    with rasterio.Env(**OPCOES_GDAL):
        with rasterio.open(f"/vsicurl/{url}") as fonte:
            janela = from_bounds(*area, transform=fonte.transform)
            janela = janela.round_offsets().round_lengths()
            dados = fonte.read(1, window=janela, masked=True)
            perfil = fonte.profile.copy()
            perfil.update(
                width=dados.shape[1],
                height=dados.shape[0],
                transform=fonte.window_transform(janela),
                tiled=True,
                blockxsize=256,
                blockysize=256,
                compress="deflate",
            )

    vazios = float(dados.mask.mean()) if dados.mask.any() else 0.0
    if vazios > 0.01:
        raise RuntimeError(f"relevo: {vazios:.1%} da área sem dado; confira o tile e a área")

    with rasterio.open(saida, "w", **perfil) as destino:
        destino.write(dados.filled(perfil["nodata"]), 1)
        destino.update_tags(
            FONTE="ANADEM v1 (Laipelt et al., 2024, doi:10.3390/rs16132321)",
            URL=url,
            AREA=",".join(str(v) for v in area),
        )

    print(
        f"relevo: {dados.shape[1]} x {dados.shape[0]} px, "
        f"altitude {float(dados.min()):.0f}–{float(dados.max()):.0f} m -> {saida}"
    )
    return saida
