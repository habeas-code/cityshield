"""Passo 5: solução verde e nota de prioridade para cada área candidata (#16).

Lê as áreas candidatas (passo 4) e os registros por rua, escolhe uma solução para cada
área e calcula uma nota de 0 a 100 para dizer por onde começar. As regras e o porquê de
cada número estão em docs/recomendacoes.md.

    solução   depende do tipo da área, do tamanho e do risco (HAND)
    nota      = 100 × risco × registros × tamanho   (cada fator vai de 0 a 1)

Saída: web/public/dados/recomendacoes.geojson (as mesmas áreas, com solução e nota)
"""

import json
import math

from shapely.geometry import shape
from shapely.ops import transform

from pipeline import areas
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
        linhas.append((f, p, perto))

    max_registros = max(perto for _, _, perto in linhas) or 1
    max_area = max(p["area_m2"] for _, p, _ in linhas)

    for f, p, perto in linhas:
        risco = p["fracao_alto"] + 0.5 * p["fracao_medio"]
        registros = perto / max_registros
        # Tamanho em escala logarítmica: um parque de 15 ha não vale 700 praças pequenas.
        tamanho = math.log(p["area_m2"] / areas.AREA_MINIMA_M2) / math.log(max_area / areas.AREA_MINIMA_M2)
        tamanho = min(max(tamanho, 0.0), 1.0)
        solucao = _solucao(p)
        p.update({
            "solucao": solucao,
            "solucao_rotulo": SOLUCOES[solucao],
            "motivo": MOTIVOS[solucao],
            "alerta": _alerta(p, solucao),
            "registros_perto": perto,
            "fator_risco": round(risco, 3),
            "fator_registros": round(registros, 3),
            "fator_tamanho": round(tamanho, 3),
            "nota": round(100 * risco * registros * tamanho),
        })

    colecao["features"].sort(key=lambda f: -f["properties"]["nota"])
    for posicao, f in enumerate(colecao["features"], start=1):
        f["properties"]["posicao"] = posicao
    colecao["metodo"] = "docs/recomendacoes.md"
    colecao["parametros"] = {
        "parque_area_minima_m2": PARQUE_AREA_MINIMA_M2,
        "parque_fracao_alto_minima": PARQUE_FRACAO_ALTO_MINIMA,
        "raio_registros_m": RAIO_REGISTROS_M,
        "hand_alerta_m": HAND_ALERTA_M,
    }
    SAIDA_GEOJSON.write_text(json.dumps(colecao, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    for solucao, rotulo in SOLUCOES.items():
        doTipo = [f["properties"] for f in colecao["features"] if f["properties"]["solucao"] == solucao]
        area = sum(p["area_m2"] for p in doTipo)
        print(f"recomendacoes: {rotulo}: {len(doTipo)} áreas, {area / 10_000:.1f} ha")
    print("recomendacoes: as 5 primeiras na fila:")
    for f in colecao["features"][:5]:
        p = f["properties"]
        print(f"  {p['posicao']}. nota {p['nota']:3d}  {p['solucao_rotulo']:17s} {p['nome'] or p['rotulo']}")
    print(f"recomendacoes: {len(colecao['features'])} áreas -> {SAIDA_GEOJSON.name}")
