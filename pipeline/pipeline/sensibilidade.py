"""Sensibilidade da nota de prioridade: a fila muda se a conta for outra?

A nota do CityShield multiplica os três fatores (risco × registros × tamanho). Esse é um
jeito de fazer análise multicritério (MCE): a área só sobe se for boa nos três. O jeito
mais comum na literatura é a combinação linear ponderada (WLC, "weighted linear
combination"): soma os fatores, cada um com um peso, e os pesos somam 1.

Aqui refazemos a fila com WLC e quatro conjuntos de pesos (todos iguais e cada fator
pesando o dobro dos outros) e medimos quanto ela muda em relação à nossa:

- quantas áreas do top 10 (e do top 3) continuam lá;
- a correlação de Spearman entre as duas filas inteiras (1 = mesma ordem);
- quantas posições uma área do nosso top 10 cai, no máximo.

Usa os fatores que já estão em recomendacoes.geojson (0 a 1, arredondados a 2 casas),
os mesmos que o site mostra. Não muda nenhuma nota: só testa a fila.

Saída: sensibilidade.json, ao lado de recomendacoes.geojson.
"""

import json

from pipeline import recomendacoes
from pipeline.caminhos import SAIDA

SAIDA_JSON = SAIDA / "sensibilidade.json"

FATORES = ("fator_risco", "fator_registros", "fator_tamanho")

# Pesos de risco, registros e tamanho. Somam 1.
PESOS = {
    "iguais": (1 / 3, 1 / 3, 1 / 3),
    "risco_em_dobro": (0.50, 0.25, 0.25),
    "registros_em_dobro": (0.25, 0.50, 0.25),
    "tamanho_em_dobro": (0.25, 0.25, 0.50),
}

TOPO = 10


def _ordem_wlc(areas, pesos):
    """Ids em ordem de WLC. Empate: fica a ordem da nossa fila (resultado estável)."""
    def chave(p):
        soma = sum(peso * p[fator] for peso, fator in zip(pesos, FATORES))
        return (-round(soma, 6), p["posicao"])
    return [p["id"] for p in sorted(areas, key=chave)]


def _spearman(ordem_a, ordem_b):
    """Correlação de Spearman entre duas ordens dos mesmos ids (sem empates)."""
    n = len(ordem_a)
    pos_b = {i: k for k, i in enumerate(ordem_b)}
    d2 = sum((k - pos_b[i]) ** 2 for k, i in enumerate(ordem_a))
    return 1 - 6 * d2 / (n * (n * n - 1))


def comparar(areas):
    nossa = [p["id"] for p in sorted(areas, key=lambda p: p["posicao"])]
    nomes = {p["id"]: p.get("nome") or f"{p['rotulo']} sem nome" for p in areas}
    cenarios = {}
    for nome, pesos in PESOS.items():
        outra = _ordem_wlc(areas, pesos)
        pos_outra = {i: k for k, i in enumerate(outra)}
        cenarios[nome] = {
            "pesos": {"risco": round(pesos[0], 2), "registros": round(pesos[1], 2), "tamanho": round(pesos[2], 2)},
            "top10_em_comum": len(set(nossa[:TOPO]) & set(outra[:TOPO])),
            "top3_em_comum": len(set(nossa[:3]) & set(outra[:3])),
            "spearman": round(_spearman(nossa, outra), 3),
            "maior_queda_do_top10": max(pos_outra[i] - k for k, i in enumerate(nossa[:TOPO])),
            "top3": [nomes[i] for i in outra[:3]],
        }
    return {
        "metodo": "docs/recomendacoes.md#sensibilidade-da-nota",
        "comparado_com": "nota = 100 × risco × registros × tamanho",
        "areas": len(areas),
        "topo": TOPO,
        "nosso_top3": [nomes[i] for i in nossa[:3]],
        "cenarios": cenarios,
        "resumo": {
            "top10_em_comum_minimo": min(c["top10_em_comum"] for c in cenarios.values()),
            "top3_em_comum_minimo": min(c["top3_em_comum"] for c in cenarios.values()),
            "spearman_minimo": min(c["spearman"] for c in cenarios.values()),
        },
    }


def analisar(refazer=False):
    recomendacoes.recomendar()  # garante a fila
    if SAIDA_JSON.exists() and not refazer:
        print(f"sensibilidade: já existe {SAIDA_JSON} (use --refazer para refazer)")
        return

    colecao = json.loads(recomendacoes.SAIDA_GEOJSON.read_text(encoding="utf-8"))
    resultado = comparar([f["properties"] for f in colecao["features"]])
    SAIDA_JSON.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")

    for nome, c in resultado["cenarios"].items():
        print(f"sensibilidade: {nome:<19} top10 {c['top10_em_comum']}/{TOPO}, top3 {c['top3_em_comum']}/3, "
              f"Spearman {c['spearman']}, maior queda do top10 {c['maior_queda_do_top10']} posições")
    print(f"sensibilidade: -> {SAIDA_JSON.name}")
