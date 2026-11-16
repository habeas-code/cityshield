"""Terceiro teste: registros oficiais da Defesa Civil de 2021 a 2026 (Bacia do Itanguá).

Fonte: resposta ao pedido de acesso à informação Fala.BR nº 03959.2026.000348-13
(Prefeitura de Sorocaba, SEMOB / Coordenadoria Municipal de Proteção e Defesa Civil,
16/11/2026). A planilha veio só com a Bacia do Itanguá.

Pergunta: o mapa acerta registros que ele nunca viu? O teste mais limpo é o dos
registros de DEPOIS de o mapa ficar pronto (HAND e validação juntados em 07/11/2026).

Método (ver docs/validacao.md, "Terceiro teste"):
1. docs/dados/lai_defesa_civil.csv tem uma linha por data, via, bairro e tipo, com o
   número de registros e o ponto aproximado da via (sem nº de casa, guia ou origem).
2. "registros" de uma via = soma dos registros dela no grupo. Cada chamado conta, como
   nos relatórios de 2022–2023 (validacao.py).
3. A conta é a mesma da validação (validacao.medir).
4. Quatro grupos: todas; só depois do mapa pronto; só 2024–2026; só as vias NOVAS
   (que não estão nos relatórios de 2022–2023).

Entrada pública: docs/dados/lai_defesa_civil.csv. Saída: web/public/dados/lai_defesa_civil.json
"""

import csv
import json
from collections import defaultdict

from pipeline import carta, hand, validacao
from pipeline.caminhos import REFERENCIA, SAIDA

ENTRADA = REFERENCIA / "lai_defesa_civil.csv"
SAIDA_JSON = SAIDA / "lai_defesa_civil.json"
MAPA_PRONTO = "2026-11-08"  # registros a partir desta data vieram depois do mapa
PEDIDO = "Fala.BR nº 03959.2026.000348-13 (Prefeitura de Sorocaba, SEMOB/Defesa Civil, 16/11/2026)"

FILTROS = {
    "todas": lambda linha: True,
    "depois_do_mapa": lambda linha: linha["data"] >= MAPA_PRONTO,
    "2024_a_2026": lambda linha: linha["data"] >= "2024",
    "novas": lambda linha: linha["no_relatorio_2022_23"] == "nao",
}


def _linhas():
    with open(ENTRADA, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ruas(linhas, filtro):
    """Uma Feature por via localizada, com a soma dos registros que passam no filtro."""
    soma, pontos = defaultdict(int), {}
    for linha in linhas:
        if not linha["lon"] or not filtro(linha):
            continue
        chave = (linha["via_osm"], linha["bairro"])
        soma[chave] += int(linha["registros"])
        pontos[chave] = (float(linha["lon"]), float(linha["lat"]))
    return [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": pontos[c]},
         "properties": {"rua": c[0], "bairro": c[1], "registros": soma[c]}}
        for c in sorted(soma)
    ]


def _resumo(medido):
    return {k: medido[k] for k in ("ruas_total", "ruas_localizadas", "registros_total", "nao_localizadas", "cidade")}


def testar(refazer=False):
    hand.calcular()
    if SAIDA_JSON.exists() and not refazer:
        print(f"lai: já existe {SAIDA_JSON} (use --refazer para refazer)")
        return

    linhas = _linhas()
    amostradores = {"hand": validacao.Amostrador(), "carta": carta.AmostradorCarta(carta.baixar())}
    total = sum(int(linha["registros"]) for linha in linhas)
    sem_ponto = sum(int(linha["registros"]) for linha in linhas if not linha["lon"])
    resultado = {
        "metodo": "docs/validacao.md#terceiro-teste-registros-oficiais-de-2021-a-2026",
        "fonte_registros": f"Defesa Civil de Sorocaba, Bacia do Itanguá, 2021–2026. Pedido {PEDIDO}",
        "fonte_ruas": "OpenStreetMap (ODbL)",
        "mapa_pronto_em": MAPA_PRONTO,
        "registros_na_planilha": total,
        "registros_sem_via_localizada": sem_ponto,
        "grupos": {},
    }
    for grupo, filtro in FILTROS.items():
        lista = ruas(linhas, filtro)
        resultado["grupos"][grupo] = {}
        for nome, amostrador in amostradores.items():
            medido = validacao.medir(amostrador, refazer, ruas=lista)
            resultado["grupos"][grupo][nome] = medido if (grupo == "todas" and nome == "hand") else _resumo(medido)

    SAIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_JSON.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"lai: {total} registros na planilha, {sem_ponto} sem via localizada")
    for grupo, por_mapa in resultado["grupos"].items():
        h, c = por_mapa["hand"]["cidade"], por_mapa["carta"]["cidade"]
        print(f"lai: {grupo}: {h['registros_considerados']:.0f} registros; HAND alto {h['fracao_registros']['alto']:.0%} "
              f"em {h['fracao_ruas']['alto']:.0%} das ruas ({h['vezes_acima_do_acaso_alto']}x), alto+médio "
              f"{h['fracao_registros']['alto'] + h['fracao_registros']['medio']:.0%}; carta alta "
              f"{c['fracao_registros']['alta']:.0%} ({c['vezes_acima_do_acaso_alta']}x), qualquer classe "
              f"{1 - c['fracao_registros'].get('fora', 0):.0%}")
