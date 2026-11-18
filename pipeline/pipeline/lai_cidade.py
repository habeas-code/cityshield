"""Quarto teste: registros oficiais da Defesa Civil da CIDADE INTEIRA, 2021 a 2026.

Fonte: anexo da decisão do recurso em 1ª instância do pedido de acesso à informação
Fala.BR nº 03959.2026.000348-13 (Prefeitura de Sorocaba, Coordenadoria Municipal de
Proteção e Defesa Civil, 17/11/2026). A resposta inicial (16/11, terceiro teste, lai.py)
veio só com a Bacia do Itanguá; no recurso veio a planilha complementar do município.

Pergunta: o mapa acerta registros de ruas e anos que ele nunca viu? O mapa foi conferido
com os relatórios COMPDEC de 2022–2023 (validacao.py). Aqui entram 2024–2026, a cheia de
janeiro de 2024 e as vias que não estão naqueles relatórios.

Método (ver docs/validacao.md, "Quarto teste"):
1. docs/dados/lai_defesa_civil_cidade.csv junta a planilha do município e a do Itanguá,
   sem contar duas vezes (230 linhas vinham nas duas). Uma linha por data, via, bairro e
   tipo, com o número de registros e o ponto aproximado da via (sem nº de casa, guia ou
   origem).
2. Mesma conta da validação (validacao.medir) e do terceiro teste (lai.ruas).
3. Grupos: todas; cheia de janeiro de 2024 (20 a 31/01, mais os de "janeiro" sem dia);
   2024–2026; vias NOVAS (fora dos relatórios 2022–2023); novas só na cheia.
4. Comparação local (teste mais duro): ruas a até 1 km de alguma via da planilha.

Entrada pública: docs/dados/lai_defesa_civil_cidade.csv.
Saída: web/public/dados/lai_defesa_civil_cidade.json
"""

import csv
import json

from pipeline import carta, hand, lai, validacao
from pipeline.caminhos import REFERENCIA, SAIDA

ENTRADA = REFERENCIA / "lai_defesa_civil_cidade.csv"
SAIDA_JSON = SAIDA / "lai_defesa_civil_cidade.json"
PEDIDO = ("Fala.BR nº 03959.2026.000348-13, recurso em 1ª instância "
          "(Prefeitura de Sorocaba, Defesa Civil, 17/11/2026)")


def _cheia(linha):
    return "2024-01-20" <= linha["data"] <= "2024-01-31" or linha["data"] == "2024-01"


def _nova(linha):
    return linha["no_relatorio_2022_23"] == "nao"


FILTROS = {
    "todas": lambda linha: True,
    "cheia_jan_2024": _cheia,
    "2024_a_2026": lambda linha: linha["data"] >= "2024",
    "novas": _nova,
    "novas_cheia_jan_2024": lambda linha: _nova(linha) and _cheia(linha),
}
GRUPOS_LOCAIS = ("todas", "2024_a_2026", "cheia_jan_2024", "novas")


def _linhas():
    with open(ENTRADA, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def testar(refazer=False):
    hand.calcular()
    if SAIDA_JSON.exists() and not refazer:
        print(f"lai_cidade: já existe {SAIDA_JSON} (use --refazer para refazer)")
        return

    linhas = _linhas()
    amostradores = {"hand": validacao.Amostrador(), "carta": carta.AmostradorCarta(carta.baixar())}
    total = sum(int(linha["registros"]) for linha in linhas)
    sem_ponto = sum(int(linha["registros"]) for linha in linhas if not linha["lon"])
    resultado = {
        "metodo": "docs/validacao.md#quarto-teste-a-cidade-inteira-2021-a-2026",
        "fonte_registros": f"Defesa Civil de Sorocaba, município inteiro, 2021–2026. Pedido {PEDIDO}",
        "fonte_ruas": "OpenStreetMap (ODbL)",
        "registros_na_planilha": total,
        "registros_sem_via_localizada": sem_ponto,
        "registros_por_ano": {},
        "grupos": {},
    }
    for linha in linhas:
        ano = linha["data"][:4]
        resultado["registros_por_ano"][ano] = resultado["registros_por_ano"].get(ano, 0) + int(linha["registros"])
    resultado["registros_por_ano"] = dict(sorted(resultado["registros_por_ano"].items()))

    for grupo, filtro in FILTROS.items():
        lista = lai.ruas(linhas, filtro)
        resultado["grupos"][grupo] = {}
        for nome, amostrador in amostradores.items():
            medido = validacao.medir(amostrador, refazer, ruas=lista)
            resultado["grupos"][grupo][nome] = lai._resumo(medido)

    limite = lai.regiao(linhas)
    local = {"raio_regiao_m": lai.RAIO_REGIAO_M, "regiao": {}}
    for grupo in GRUPOS_LOCAIS:
        lista = lai.ruas(linhas, FILTROS[grupo])
        local["regiao"][grupo] = {}
        for nome, amostrador in amostradores.items():
            medido = validacao.medir(amostrador, refazer, ruas=lista, limite=limite)
            local["regiao"][grupo][nome] = {
                **lai._resumo(medido), "registros_fora_do_limite": medido["registros_fora_do_limite"]}
    resultado["comparacao_local"] = local

    SAIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_JSON.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"lai_cidade: {total} registros na planilha, {sem_ponto} sem via localizada")
    for grupo, por_mapa in resultado["grupos"].items():
        h, c = por_mapa["hand"]["cidade"], por_mapa["carta"]["cidade"]
        print(f"lai_cidade: {grupo}: {h['registros_considerados']:.0f} registros; HAND alto "
              f"{h['fracao_registros']['alto']:.0%} em {h['fracao_ruas']['alto']:.0%} das ruas "
              f"({h['vezes_acima_do_acaso_alto']}x), alto+médio "
              f"{h['fracao_registros']['alto'] + h['fracao_registros']['medio']:.0%}; carta alta "
              f"{c['fracao_registros']['alta']:.0%} ({c['vezes_acima_do_acaso_alta']}x), qualquer classe "
              f"{1 - c['fracao_registros'].get('fora', 0):.0%}")
    for grupo, por_mapa in local["regiao"].items():
        h = por_mapa["hand"]["cidade"]
        print(f"lai_cidade: local {grupo}: {h['registros_considerados']:.0f} registros; HAND alto "
              f"{h['fracao_registros']['alto']:.0%} em {h['fracao_ruas']['alto']:.0%} das ruas "
              f"({h['vezes_acima_do_acaso_alto']}x), alto+médio "
              f"{h['fracao_registros']['alto'] + h['fracao_registros']['medio']:.0%} em "
              f"{h['fracao_ruas']['alto'] + h['fracao_ruas']['medio']:.0%} "
              f"({h['vezes_acima_do_acaso_alto_medio']}x)")
