"""Segundo teste: as ruas que a imprensa noticiou como alagadas em 2024–2026.

Pergunta: lugares que alagaram DEPOIS dos relatórios da Defesa Civil (2022–2023)
também caem no risco do HAND? E na carta oficial?

Método (ver docs/validacao.md, "Segundo teste"):
1. docs/dados/noticias.csv tem uma linha por via citada em cada notícia, já com o
   nome limpo, o ponto aproximado e a chuva (evento) a que se refere.
2. Cada via conta UMA vez por evento: a mesma chuva noticiada por cinco veículos
   continua sendo uma chuva. "registros" de uma via = número de eventos.
3. A conta é a mesma da validação (validacao.medir): rua no OpenStreetMap, amostra a
   cada 10 m, divisão pela extensão, comparação com todas as ruas do município.
4. Três grupos: todas as vias; só as NOVAS (que não estão nos relatórios de 2022–2023,
   o teste mais limpo, porque o mapa nunca as viu); só as que já estavam.

Entrada pública: docs/dados/noticias.csv (só data, via, veículo e link; nenhum texto
das notícias). Saída: web/public/dados/noticias.json
"""

import csv
import json
from collections import defaultdict

from pipeline import carta, hand, validacao
from pipeline.caminhos import REFERENCIA, SAIDA

ENTRADA = REFERENCIA / "noticias.csv"
SAIDA_JSON = SAIDA / "noticias.json"


def _ruas():
    """Uma Feature por via, com o número de eventos em que ela foi citada."""
    eventos, pontos, na_dc, noticias = defaultdict(set), {}, {}, defaultdict(set)
    with open(ENTRADA, encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            via = linha["via"]
            if not via or not linha["lon"]:
                continue  # não é via (bairro, prédio, córrego) ou sem ponto
            eventos[via].add(linha["evento"])
            noticias[via].add(linha["link"])
            pontos[via] = (float(linha["lon"]), float(linha["lat"]))
            na_dc[via] = linha["na_defesa_civil_2022_23"] == "sim"
    return [
        {"type": "Feature",
         "geometry": {"type": "Point", "coordinates": pontos[via]},
         "properties": {"rua": via, "registros": len(eventos[via]), "eventos": sorted(eventos[via]),
                        "noticias": len(noticias[via]), "na_defesa_civil": na_dc[via]}}
        for via in sorted(eventos)
    ]


def _total_noticias():
    with open(ENTRADA, encoding="utf-8", newline="") as f:
        return len({linha["link"] for linha in csv.DictReader(f)})


def _resumo(medido):
    """Só o que o texto e o site usam (o detalhe rua por rua fica no grupo 'todas')."""
    return {k: medido[k] for k in ("ruas_total", "ruas_localizadas", "registros_total", "nao_localizadas", "cidade")}


def testar(refazer=False):
    hand.calcular()
    if SAIDA_JSON.exists() and not refazer:
        print(f"noticias: já existe {SAIDA_JSON} (use --refazer para refazer)")
        return

    ruas = _ruas()
    grupos = {
        "todas": ruas,
        "novas": [r for r in ruas if not r["properties"]["na_defesa_civil"]],
        "ja_na_defesa_civil": [r for r in ruas if r["properties"]["na_defesa_civil"]],
    }
    amostradores = {"hand": validacao.Amostrador(), "carta": carta.AmostradorCarta(carta.baixar())}

    resultado = {
        "metodo": "docs/validacao.md#segundo-teste-notícias-de-2024-a-2026",
        "fonte_registros": "Notícias de alagamento em Sorocaba, 2024–2026 (docs/dados/noticias.csv)",
        "fonte_ruas": "OpenStreetMap (ODbL)",
        "registro": "1 registro = 1 via citada em 1 evento de chuva (datas a até 2 dias = mesmo evento)",
        "eventos": len({e for r in ruas for e in r["properties"]["eventos"]}),
        "noticias": _total_noticias(),
        "grupos": {},
    }
    for grupo, lista in grupos.items():
        resultado["grupos"][grupo] = {}
        for nome, amostrador in amostradores.items():
            medido = validacao.medir(amostrador, refazer, ruas=lista)
            resultado["grupos"][grupo][nome] = medido if (grupo == "todas" and nome == "hand") else _resumo(medido)

    SAIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_JSON.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"noticias: {resultado['noticias']} notícias, {resultado['eventos']} eventos, {len(ruas)} vias")
    for grupo, por_mapa in resultado["grupos"].items():
        h, c = por_mapa["hand"]["cidade"], por_mapa["carta"]["cidade"]
        print(f"noticias: {grupo}: HAND alto {h['fracao_registros']['alto']:.0%} em {h['fracao_ruas']['alto']:.0%} "
              f"das ruas ({h['vezes_acima_do_acaso_alto']}x); carta alta {c['fracao_registros']['alta']:.0%} "
              f"em {c['fracao_ruas']['alta']:.0%} ({c['vezes_acima_do_acaso_alta']}x)")
