"""Passo 3: testa o mapa de risco contra os registros reais da Defesa Civil.

Pergunta: os lugares que alagaram em 2022–2023 caem nas faixas de risco do HAND?

Método (ver docs/validacao.md):
1. Cada rua com registro é localizada no OpenStreetMap pelo nome. Se o nome existe em
   mais de um lugar, ficam só os trechos a até RAIO_BUSCA_M do ponto geocodificado.
2. A rua é amostrada a cada PASSO_M metros e cada ponto recebe a faixa do HAND.
3. Os registros da rua são divididos entre as faixas na proporção do comprimento.
   (O relatório diz a rua, não o ponto exato: supomos que o alagamento pode ter
   acontecido em qualquer trecho dela.)
4. Comparação justa: a mesma conta para TODAS as ruas do município. Ruas tendem a
   seguir os vales, então comparar com a área da cidade inflaria o resultado.

Entrada pública: docs/dados/ruas.geojson (registros agregados por rua, sem endereço).
Saída: web/public/dados/validacao.json
"""

import difflib
import json
import time
import unicodedata
import urllib.parse
import urllib.request

import numpy as np
import rasterio
from pyproj import Transformer
from shapely import segmentize
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform, unary_union

from pipeline import hand
from pipeline.caminhos import DADOS, REFERENCIA, SAIDA

OVERPASS = "https://overpass-api.de/api/interpreter"
CACHE_OSM = DADOS / "osm" / "vias_sorocaba.json"
RUAS = REFERENCIA / "ruas.geojson"
SAIDA_JSON = SAIDA / "validacao.json"

PASSO_M = 10
RAIO_BUSCA_M = 3000          # nome igual: aceita trechos até esta distância do ponto
RAIO_PARECIDO_M = 1500       # nome com grafia diferente: só bem perto do ponto
SEMELHANCA_MINIMA = 0.88
PALAVRAS_VAZIAS = {"de", "da", "do", "das", "dos", "e"}
PILOTO = (-47.4472, -23.4702)  # núcleo Norte (docs/decisoes.md, D3)
RAIO_PILOTO_M = 800

# Vias de carro e pedestre urbanas; ficam de fora trilhas, ciclovias e acessos internos.
VIAS = ("motorway|trunk|primary|secondary|tertiary|unclassified|residential|"
        "living_street|pedestrian|primary_link|secondary_link|tertiary_link|trunk_link")

PARA_UTM = Transformer.from_crs("EPSG:4326", "EPSG:31983", always_xy=True).transform  # SIRGAS 2000 / UTM 23S
PARA_GRAUS = Transformer.from_crs("EPSG:31983", "EPSG:4326", always_xy=True).transform


def _normalizar(nome):
    nome = nome.split("(")[0].strip().lower()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    return " ".join("15" if p == "xv" else p for p in nome.split())


def _parecido(do_relatorio, do_osm):
    """Mesma rua com grafia diferente: 'Mota'/'Motta', 'Afonso Vergueiro'/'Doutor Afonso Vergueiro'."""
    palavras = set(do_relatorio.split()) - PALAVRAS_VAZIAS
    if palavras and palavras <= set(do_osm.split()):
        return 1.0
    return difflib.SequenceMatcher(None, do_relatorio, do_osm).ratio()


def _baixar_osm(refazer):
    if CACHE_OSM.exists() and not refazer:
        return json.loads(CACHE_OSM.read_text(encoding="utf-8"))
    oeste, sul, leste, norte = unary_union(hand._limite()).bounds
    caixa = f"{sul},{oeste},{norte},{leste}"
    consulta = f"""[out:json][timeout:180];
(
  way["highway"~"^({VIAS})$"]({caixa});
  way["leisure"~"^(park|garden)$"]["name"]({caixa});
  way["place"="square"]["name"]({caixa});
);
out geom tags;"""
    print("validacao: baixando ruas e praças do OpenStreetMap (pode levar ~1 min)")
    corpo = urllib.parse.urlencode({"data": consulta}).encode()
    pedido = urllib.request.Request(OVERPASS, data=corpo, headers={"User-Agent": "cityshield-pipeline/0.1"})
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(pedido, timeout=240) as resposta:
                dados = json.load(resposta)
            break
        except OSError:
            if tentativa == 2:
                raise
            time.sleep(15)
    CACHE_OSM.parent.mkdir(parents=True, exist_ok=True)
    CACHE_OSM.write_text(json.dumps(dados), encoding="utf-8")
    return dados


def _linhas_osm(dados):
    """Devolve [(nome_normalizado, eh_via, geometria_utm)]."""
    saida = []
    for el in dados["elements"]:
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
        if len(coords) < 2:
            continue
        tags = el.get("tags", {})
        geom = transform(PARA_UTM, LineString(coords))
        saida.append((_normalizar(tags.get("name", "")), "highway" in tags, geom))
    return saida


class Amostrador:
    """Lê a faixa do HAND (alto/medio/baixo) em pontos ao longo de linhas.

    Outro mapa pode ser testado do mesmo jeito (carta.py): basta ter CLASSES, faixa_ponto
    e faixas. A primeira classe é a de maior risco (é ela que vira "vezes o acaso").
    """

    CLASSES = ("alto", "medio", "baixo")

    def __init__(self):
        with rasterio.open(hand.HAND_TIF) as fonte:
            self.hand = fonte.read(1)
            self.inversa = ~fonte.transform

    def faixa_ponto(self, ponto_utm):
        x, y = PARA_GRAUS(ponto_utm.x, ponto_utm.y)
        col, lin = self.inversa * (x, y)
        valor = self.hand[int(lin), int(col)]
        if valor < 0:
            return None
        return "alto" if valor < 5 else "medio" if valor < 15 else "baixo"

    def faixas(self, linha_utm):
        pontos = segmentize(linha_utm, PASSO_M)
        xs, ys = PARA_GRAUS(*np.asarray(pontos.coords).T)
        col, lin = self.inversa * (np.asarray(xs), np.asarray(ys))
        lin, col = np.floor(lin).astype(int), np.floor(col).astype(int)
        dentro = (lin >= 0) & (lin < self.hand.shape[0]) & (col >= 0) & (col < self.hand.shape[1])
        valores = self.hand[lin[dentro], col[dentro]]
        valores = valores[valores >= 0]
        return {
            "alto": int((valores < 5).sum()),
            "medio": int(((valores >= 5) & (valores < 15)).sum()),
            "baixo": int((valores >= 15).sum()),
        }


def _proporcao(contagem):
    total = sum(contagem.values())
    return {k: (v / total if total else 0.0) for k, v in contagem.items()}


def _somar(acumulado, contagem):
    for k, v in contagem.items():
        acumulado[k] += v


def medir(amostrador, refazer=False):
    """Registros e ruas da cidade (e do piloto) por classe do mapa que o amostrador lê."""
    municipio_utm = transform(PARA_UTM, hand._limite())
    piloto_utm = transform(PARA_UTM, Point(PILOTO)).buffer(RAIO_PILOTO_M)
    linhas = _linhas_osm(_baixar_osm(refazer))
    vazio = lambda tipo: {k: tipo() for k in amostrador.CLASSES}  # noqa: E731

    # Comparação justa: todas as vias do município e do piloto
    base_cidade = vazio(int)
    base_piloto = vazio(int)
    for _, eh_via, geom in linhas:
        if not eh_via:
            continue
        no_mun = geom.intersection(municipio_utm)
        if not no_mun.is_empty:
            for parte in getattr(no_mun, "geoms", [no_mun]):
                _somar(base_cidade, amostrador.faixas(parte))
        no_piloto = geom.intersection(piloto_utm)
        if not no_piloto.is_empty:
            for parte in getattr(no_piloto, "geoms", [no_piloto]):
                _somar(base_piloto, amostrador.faixas(parte))

    por_nome = {}
    for nome, _, geom in linhas:
        if nome:
            por_nome.setdefault(nome, []).append(geom)

    with open(RUAS, encoding="utf-8") as f:
        ruas = json.load(f)["features"]

    cidade = vazio(float)
    piloto = vazio(float)
    centroide = vazio(int)
    detalhe, nao_achadas = [], []
    for rua in ruas:
        props = rua["properties"]
        ponto = transform(PARA_UTM, shape(rua["geometry"]))
        nome = _normalizar(props["rua"])
        nome_osm = nome
        candidatas = [g for g in por_nome.get(nome, []) if g.distance(ponto) <= RAIO_BUSCA_M]
        if not candidatas:
            melhor = 0.0
            for outro, geoms in por_nome.items():
                perto = [g for g in geoms if g.distance(ponto) <= RAIO_PARECIDO_M]
                if not perto:
                    continue
                nota = _parecido(nome, outro)
                if nota >= SEMELHANCA_MINIMA and nota > melhor:
                    melhor, nome_osm, candidatas = nota, outro, perto
        if not candidatas:
            nao_achadas.append(props["rua"])
            continue
        geom = unary_union(candidatas)
        # praça ou parque: usa o contorno (a área alagada fica dentro ou em volta)
        contagem = vazio(int)
        for parte in getattr(geom, "geoms", [geom]):
            _somar(contagem, amostrador.faixas(parte))
        prop = _proporcao(contagem)
        for k in cidade:
            cidade[k] += props["registros"] * prop[k]
        if ponto.distance(transform(PARA_UTM, Point(PILOTO))) <= RAIO_PILOTO_M:
            for k in piloto:
                piloto[k] += props["registros"] * prop[k]
        faixa_ponto = amostrador.faixa_ponto(ponto)
        if faixa_ponto:
            centroide[faixa_ponto] += props["registros"]
        detalhe.append({"rua": props["rua"], "nome_osm": nome_osm, "registros": props["registros"],
                        "comprimento_m": round(geom.length),
                        **{f"fracao_{k}": round(v, 3) for k, v in prop.items()}})

    um, dois = amostrador.CLASSES[:2]

    def resumo(registros, base):
        reg = _proporcao(registros)
        bas = _proporcao(base)
        return {
            "registros_considerados": round(sum(registros.values()), 1),
            "registros_por_faixa": {k: round(v, 1) for k, v in registros.items()},
            "fracao_registros": {k: round(v, 3) for k, v in reg.items()},
            "fracao_ruas": {k: round(v, 3) for k, v in bas.items()},
            f"vezes_acima_do_acaso_{um}": round(reg[um] / bas[um], 2) if bas[um] else None,
            f"vezes_acima_do_acaso_{um}_{dois}": round((reg[um] + reg[dois]) / (bas[um] + bas[dois]), 2),
        }

    return {
        "ruas_total": len(ruas),
        "ruas_localizadas": len(detalhe),
        "registros_total": sum(r["properties"]["registros"] for r in ruas),
        "nao_localizadas": nao_achadas,
        "cidade": resumo(cidade, base_cidade),
        "piloto": resumo(piloto, base_piloto),
        "comparacao_ponto_central": {k: round(v / sum(centroide.values()), 3) for k, v in centroide.items()},
        "ruas": sorted(detalhe, key=lambda d: -d["registros"]),
    }


def validar(refazer=False):
    hand.calcular()  # garante HAND (e relevo)
    if SAIDA_JSON.exists() and not refazer:
        print(f"validacao: já existe {SAIDA_JSON} (use --refazer para refazer)")
        return

    medido = medir(Amostrador(), refazer)
    detalhe, ruas_total, nao_achadas = medido["ruas"], medido["ruas_total"], medido["nao_localizadas"]
    resultado = {
        "metodo": "docs/validacao.md",
        "fonte_registros": "Defesa Civil de Sorocaba, relatórios 2022–2023 (agregado por rua)",
        "fonte_ruas": "OpenStreetMap (ODbL)",
        "faixas": {"alto": "HAND 0–5 m", "medio": "HAND 5–15 m", "baixo": "HAND > 15 m"},
        **medido,
    }
    SAIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_JSON.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")

    c, p = resultado["cidade"], resultado["piloto"]
    print(f"validacao: {len(detalhe)}/{ruas_total} ruas localizadas no OSM")
    print(f"validacao: CIDADE {c['fracao_registros']['alto']:.0%} dos registros no risco alto, "
          f"onde estão {c['fracao_ruas']['alto']:.0%} das ruas ({c['vezes_acima_do_acaso_alto']}x o acaso)")
    print(f"validacao: CIDADE alto+médio {c['fracao_registros']['alto'] + c['fracao_registros']['medio']:.0%} "
          f"dos registros em {c['fracao_ruas']['alto'] + c['fracao_ruas']['medio']:.0%} das ruas")
    print(f"validacao: PILOTO {p['fracao_registros']['alto']:.0%} no alto, "
          f"onde estão {p['fracao_ruas']['alto']:.0%} das ruas ({p['vezes_acima_do_acaso_alto']}x)")
    if nao_achadas:
        print(f"validacao: não localizadas: {', '.join(nao_achadas)}")
