"""Passo 3b: o mesmo teste da validação, feito com a carta oficial de inundação.

Pergunta: os registros da Defesa Civil caem nas áreas que a carta de suscetibilidade a
inundações (IPT e Serviço Geológico do Brasil, 2015) marca como alta? E como isso se
compara com o nosso mapa de risco (HAND)?

A carta é o mapa oficial que Sorocaba já tem (docs/decisoes.md, D2). Ela foi feita em
escala 1:25.000, com classes alta, média e baixa; fora dos polígonos não há
suscetibilidade a inundação mapeada ("fora").

Método: exatamente o de validacao.py (ruas do OSM amostradas a cada 10 m, registros
divididos pelo comprimento, comparação com todas as ruas da cidade). Só troca o mapa.

Os arquivos da carta vêm do repositório do SGB (RIGEO). O pacote SIG tem 199 MB, mas só
precisamos da camada de inundação: lemos só esses arquivos de dentro do zip, por partes
(HTTP Range), e guardamos em pipeline/dados/sgb/. A geometria da carta não vai para o
repositório nem para o site: só os números da comparação.

Saída: web/public/dados/comparacao_carta.json
"""

import io
import json
import urllib.request
import zipfile

import numpy as np
import rasterio
import shapefile
from pyproj import Transformer
from rasterio.features import geometry_mask, rasterize
from shapely import segmentize
from shapely.geometry import shape
from shapely.ops import transform

from pipeline import hand, validacao
from pipeline.caminhos import DADOS, SAIDA

ZIP_URL = ("https://rigeo.sgb.gov.br/server/api/core/bitstreams/"
           "210a7438-41bd-4a8e-8c54-19f075ee0f08/content")
PAGINA = "https://rigeo.sgb.gov.br/items/cb9a8ac7-dda7-45e0-9dbe-7e8664b6b665"
CAMADA = "12.Suscetibilidade/SuscetibilidadeInundacao"
PASTA = DADOS / "sgb"
SAIDA_JSON = SAIDA / "comparacao_carta.json"
FONTE = ("Instituto de Pesquisas Tecnológicas (IPT) e CPRM/Serviço Geológico do Brasil, Carta de "
         "suscetibilidade a movimentos gravitacionais de massa e inundações: município de Sorocaba - SP, 2015")

# Classe da carta -> código no raster (0 = fora dos polígonos de inundação)
CODIGOS = {"alta": 3, "media": 2, "baixa": 1}   # o arquivo escreve "Media", sem acento
DA_CARTA = Transformer.from_crs("EPSG:31983", "EPSG:4326", always_xy=True).transform  # SIRGAS 2000 / UTM 23S


class _ArquivoRemoto(io.RawIOBase):
    """Arquivo remoto que o zipfile consegue ler por partes, com pedidos HTTP Range."""

    def __init__(self, url):
        self.url, self.pos = url, 0
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as r:
            self.tamanho = int(r.headers["Content-Length"])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, deslocamento, de_onde=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.pos, io.SEEK_END: self.tamanho}[de_onde]
        self.pos = base + deslocamento
        return self.pos

    def read(self, n=-1):
        fim = self.tamanho if n is None or n < 0 else min(self.pos + n, self.tamanho)
        if fim <= self.pos:
            return b""
        pedido = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{fim - 1}"})
        with urllib.request.urlopen(pedido, timeout=120) as r:
            dados = r.read()
        self.pos += len(dados)
        return dados


def baixar(refazer=False):
    """Copia só a camada de inundação de dentro do zip do SGB para pipeline/dados/sgb/."""
    shp = PASTA / "SuscetibilidadeInundacao.shp"
    if shp.exists() and not refazer:
        return shp
    PASTA.mkdir(parents=True, exist_ok=True)
    print("carta: lendo a camada de inundação do pacote SIG do SGB (só os arquivos dela)...")
    with zipfile.ZipFile(_ArquivoRemoto(ZIP_URL)) as z:
        for ext in (".shp", ".shx", ".dbf", ".prj"):
            (PASTA / f"SuscetibilidadeInundacao{ext}").write_bytes(z.read(CAMADA + ext))
    return shp


class AmostradorCarta(validacao.Amostrador):
    """Lê a classe da carta (alta/media/baixa/fora) na mesma grade do HAND."""

    CLASSES = ("alta", "media", "baixa", "fora")
    _POR_CODIGO = {3: "alta", 2: "media", 1: "baixa", 0: "fora"}

    def __init__(self, shp):
        leitor = shapefile.Reader(str(shp), encoding="latin1")
        formas = [(transform(DA_CARTA, shape(r.shape.__geo_interface__)), _codigo(r.record["Classe"]))
                  for r in leitor.iterShapeRecords()]
        leitor.close()
        with rasterio.open(hand.HAND_TIF) as fonte:
            sem_relevo = fonte.read(1) < 0
            # Polígonos de classes diferentes não se sobrepõem; se encostarem, vale a mais alta.
            formas.sort(key=lambda f: f[1])
            self.grade = rasterize(formas, out_shape=fonte.shape, transform=fonte.transform,
                                   fill=0, dtype="int8")
            self.inversa = ~fonte.transform
            self.municipio = _no_municipio(fonte)
        self.grade[sem_relevo] = -1  # mesma regra do HAND

    def faixa_ponto(self, ponto_utm):
        x, y = validacao.PARA_GRAUS(ponto_utm.x, ponto_utm.y)
        col, lin = self.inversa * (x, y)
        return self._POR_CODIGO.get(int(self.grade[int(lin), int(col)]))

    def faixas(self, linha_utm):
        pontos = segmentize(linha_utm, validacao.PASSO_M)
        xs, ys = validacao.PARA_GRAUS(*np.asarray(pontos.coords).T)
        col, lin = self.inversa * (np.asarray(xs), np.asarray(ys))
        lin, col = np.floor(lin).astype(int), np.floor(col).astype(int)
        dentro = (lin >= 0) & (lin < self.grade.shape[0]) & (col >= 0) & (col < self.grade.shape[1])
        valores = self.grade[lin[dentro], col[dentro]]
        return {nome: int((valores == codigo).sum()) for codigo, nome in self._POR_CODIGO.items()}

    def fracao_da_area(self):
        """Parte da área do município em cada classe (por células da grade)."""
        validas = self.grade[(self.grade >= 0) & self.municipio]
        return {nome: round(float((validas == c).sum() / validas.size), 3) for c, nome in self._POR_CODIGO.items()}


def _codigo(classe):
    return CODIGOS[classe.strip().lower().replace("é", "e")]


def _no_municipio(fonte):
    """Máscara das células dentro do limite do município (o raster do HAND é um retângulo maior)."""
    return ~geometry_mask([hand._limite().__geo_interface__], out_shape=fonte.shape, transform=fonte.transform)


def comparar(refazer=False):
    hand.calcular()
    if SAIDA_JSON.exists() and not refazer:
        print(f"carta: já existe {SAIDA_JSON} (use --refazer para refazer)")
        return

    amostrador = AmostradorCarta(baixar(refazer))
    medido = validacao.medir(amostrador)
    medido_hand = json.loads(validacao.SAIDA_JSON.read_text(encoding="utf-8")) if validacao.SAIDA_JSON.exists() \
        else validacao.medir(validacao.Amostrador())
    with rasterio.open(hand.HAND_TIF) as fonte:
        h = fonte.read(1)
        h = h[(h >= 0) & _no_municipio(fonte)]

    resultado = {
        "metodo": "docs/validacao.md#comparação-com-a-carta-oficial",
        "fonte_carta": FONTE,
        "pagina_carta": PAGINA,
        "fonte_registros": "Defesa Civil de Sorocaba, relatórios 2022–2023 (agregado por rua)",
        "classes": {"alta": "suscetibilidade alta", "media": "média", "baixa": "baixa",
                    "fora": "fora das áreas de inundação da carta"},
        "ruas_localizadas": medido["ruas_localizadas"],
        "carta": {
            "cidade": medido["cidade"],
            "piloto": medido["piloto"],
            "fracao_da_area_do_municipio": amostrador.fracao_da_area(),
        },
        "hand": {
            "cidade": medido_hand["cidade"],
            "piloto": medido_hand["piloto"],
            "fracao_da_area_do_municipio": {
                "alto": round(float((h < 5).sum() / h.size), 3),
                "medio": round(float(((h >= 5) & (h < 15)).sum() / h.size), 3),
                "baixo": round(float((h >= 15).sum() / h.size), 3),
            },
        },
    }
    SAIDA_JSON.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")

    c, hc = resultado["carta"]["cidade"], resultado["hand"]["cidade"]
    print(f"carta: CARTA alta tem {c['fracao_registros']['alta']:.0%} dos registros em "
          f"{c['fracao_ruas']['alta']:.0%} das ruas ({c['vezes_acima_do_acaso_alta']}x o acaso)")
    em_alguma = 1 - c["fracao_registros"]["fora"]
    print(f"carta: CARTA alta+média+baixa tem {em_alguma:.0%} dos registros em "
          f"{1 - c['fracao_ruas']['fora']:.0%} das ruas")
    print(f"carta: HAND alto tem {hc['fracao_registros']['alto']:.0%} dos registros em "
          f"{hc['fracao_ruas']['alto']:.0%} das ruas ({hc['vezes_acima_do_acaso_alto']}x o acaso)")
