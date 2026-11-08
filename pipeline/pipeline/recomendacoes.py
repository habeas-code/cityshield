"""Passo 5: solução verde e nota de prioridade para cada área candidata (#16).

Lê as áreas candidatas (passo 4) e os registros por rua, escolhe uma solução para cada
área e calcula uma nota de 0 a 100 para dizer por onde começar. As regras e o porquê de
cada número estão em docs/recomendacoes.md.

    solução   depende do tipo da área, do tamanho e do risco (HAND)
    nota      = 100 × risco × registros × tamanho   (cada fator vai de 0 a 1)

Saída: web/public/dados/recomendacoes.geojson (as mesmas áreas, com solução, nota e volume)
"""

import json
import math

import rasterio
from shapely.geometry import shape
from shapely.ops import transform

from pipeline import areas, relevo, volumes
from pipeline.caminhos import SAIDA
from pipeline.validacao import PARA_UTM, RUAS

SAIDA_GEOJSON = SAIDA / "recomendacoes.geojson"

# Parque inundável: área verde grande, quase toda no risco alto (várzea).
PARQUE_AREA_MINIMA_M2 = 10_000   # 1 ha
PARQUE_FRACAO_ALTO_MINIMA = 0.5

# Registros "perto" da área: ruas com registro até esta distância da borda.
# Os pontos das ruas são aproximados (um ponto por rua), por isso uma faixa folgada.
RAIO_REGISTROS_M = 300

# Abaixo disso a área está praticamente no nível do córrego: o lençol freático pode
# estar raso e a infiltração, limitada. Critério nosso, para alertar, não para excluir.
HAND_ALERTA_M = 1.0

SOLUCOES = {
    "parque_inundavel": "Parque inundável",
    "jardim_chuva": "Jardim de chuva",
    "piso_permeavel": "Piso permeável",
    "telhado_verde": "Telhado verde",
}

MOTIVOS = {
    "parque_inundavel": "Área verde grande na várzea: pode guardar água na chuva forte e devolver devagar.",
    "jardim_chuva": "Área verde: um canteiro rebaixado recebe a água das calçadas e ruas em volta.",
    "piso_permeavel": "Estacionamento aberto: trocar o asfalto por piso que deixa a água passar.",
    "telhado_verde": "Prédio grande: a cobertura vegetal segura parte da chuva antes de ela descer.",
}


def _solucao(p):
    if p["tipo"] == "estacionamento":
        return "piso_permeavel"
    if p["tipo"] == "telhado":
        return "telhado_verde"
    if p["area_m2"] >= PARQUE_AREA_MINIMA_M2 and p["fracao_alto"] >= PARQUE_FRACAO_ALTO_MINIMA:
        return "parque_inundavel"
    return "jardim_chuva"


def _alerta(p, solucao):
    infiltra = solucao in ("jardim_chuva", "piso_permeavel")
    if infiltra and p["hand_min_m"] < HAND_ALERTA_M:
        return "Área no nível do córrego: conferir a profundidade do lençol freático antes de projetar."
    return None


def _ruas():
    dados = json.loads(RUAS.read_text(encoding="utf-8"))
    return [(transform(PARA_UTM, shape(f["geometry"])), f["properties"]["registros"]) for f in dados["features"]]


def recomendar(refazer=False):
    areas.extrair()  # garante as áreas candidatas
    if SAIDA_GEOJSON.exists() and not refazer:
        print(f"recomendacoes: já existe {SAIDA_GEOJSON} (use --refazer para refazer)")
        return

    colecao = json.loads(areas.SAIDA_GEOJSON.read_text(encoding="utf-8"))
    ruas = _ruas()

    linhas = []
    for f in colecao["features"]:
        p = f["properties"]
        geom = transform(PARA_UTM, shape(f["geometry"]))
        perto = sum(n for ponto, n in ruas if geom.distance(ponto) <= RAIO_REGISTROS_M)
        linhas.append((f, p, perto, shape(f["geometry"])))

    max_registros = max(perto for _, _, perto, _ in linhas) or 1
    max_area = max(p["area_m2"] for _, p, _, _ in linhas)
    fonte_relevo = rasterio.open(relevo.SAIDA)

    for f, p, perto, poligono in linhas:
        risco = p["fracao_alto"] + 0.5 * p["fracao_medio"]
        registros = perto / max_registros
        # Tamanho em escala logarítmica: um parque de 15 ha não vale 700 praças pequenas.
        tamanho = math.log(p["area_m2"] / areas.AREA_MINIMA_M2) / math.log(max_area / areas.AREA_MINIMA_M2)
        tamanho = min(max(tamanho, 0.0), 1.0)
        solucao = _solucao(p)
        # A nota sai dos fatores já arredondados a 2 casas: a conta que o site mostra
        # (100 × risco × ocorrências × tamanho) tem que dar exatamente a nota.
        risco, registros, tamanho = round(risco, 2), round(registros, 2), round(tamanho, 2)
        p.update({
            # Id fixo para a API (/areas/{id}): vem do OpenStreetMap, não muda quando a fila muda.
            # Hífen no lugar da barra ("way/123" -> "way-123") para caber numa URL.
            "id": p["osm"].replace("/", "-"),
            "solucao": solucao,
            "solucao_rotulo": SOLUCOES[solucao],
            "motivo": MOTIVOS[solucao],
            "alerta": _alerta(p, solucao),
            "registros_perto": perto,
            "fator_risco": risco,
            "fator_registros": registros,
            "fator_tamanho": tamanho,
            "nota": round(100 * risco * registros * tamanho),
        })
        p.update(volumes.estimar(p, poligono, fonte_relevo))
    fonte_relevo.close()

    colecao["features"].sort(key=lambda f: -f["properties"]["nota"])
    for posicao, f in enumerate(colecao["features"], start=1):
        f["properties"]["posicao"] = posicao
        f["id"] = f["properties"]["id"]
    ids = [f["id"] for f in colecao["features"]]
    assert len(ids) == len(set(ids)), "id repetido nas áreas"
    colecao["metodo"] = "docs/recomendacoes.md"
    colecao["parametros"] = {
        "parque_area_minima_m2": PARQUE_AREA_MINIMA_M2,
        "parque_fracao_alto_minima": PARQUE_FRACAO_ALTO_MINIMA,
        "raio_registros_m": RAIO_REGISTROS_M,
        "hand_alerta_m": HAND_ALERTA_M,
        "chuva_ref_mm": volumes.CHUVA_REF_MM,
        "jardim_fracao_da_area": volumes.JARDIM_FRACAO_DA_AREA,
        "jardim_lamina_m": volumes.JARDIM_LAMINA_M,
        "jardim_area_que_escoa": volumes.JARDIM_AREA_QUE_ESCOA,
        "piso_capacidade_mm": volumes.PISO_CAPACIDADE_MM,
        "telhado_retencao": volumes.TELHADO_RETENCAO,
        "parque_lamina_m": volumes.PARQUE_LAMINA_M,
        "fontes": volumes.FONTES,
    }
    SAIDA_GEOJSON.write_text(json.dumps(colecao, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    for solucao, rotulo in SOLUCOES.items():
        doTipo = [f["properties"] for f in colecao["features"] if f["properties"]["solucao"] == solucao]
        area = sum(p["area_m2"] for p in doTipo)
        volume = sum(p.get("volume_m3", 0) for p in doTipo)
        volume_txt = f"{volume:,}".replace(",", ".")
        print(f"recomendacoes: {rotulo}: {len(doTipo)} áreas, {area / 10_000:.1f} ha, {volume_txt} m³")
    print("recomendacoes: as 5 primeiras na fila:")
    for f in colecao["features"][:5]:
        p = f["properties"]
        print(f"  {p['posicao']}. nota {p['nota']:3d}  {p['solucao_rotulo']:17s} {p['nome'] or p['rotulo']}")
    print(f"recomendacoes: {len(colecao['features'])} áreas -> {SAIDA_GEOJSON.name}")
