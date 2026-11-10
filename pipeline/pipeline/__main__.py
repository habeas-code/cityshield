"""Ponto de entrada do pipeline.

    python -m pipeline            roda todos os passos
    python -m pipeline relevo     roda só o passo do relevo
    python -m pipeline hand       drenagem e HAND (baixa o relevo se faltar)
    python -m pipeline hand --refazer
    python -m pipeline validacao  testa o HAND contra os registros da Defesa Civil
    python -m pipeline carta      o mesmo teste com a carta oficial de inundação (IPT/SGB, 2015)
    python -m pipeline noticias   segundo teste: ruas noticiadas como alagadas em 2024–2026
    python -m pipeline areas      áreas candidatas a soluções verdes no piloto
    python -m pipeline recomendacoes  solução e nota de prioridade de cada área
    python -m pipeline sensibilidade  a fila muda se a nota usar outra conta (WLC)?
"""

import argparse

from pipeline import areas, carta, hand, noticias, recomendacoes, relevo, sensibilidade, validacao

PASSOS = {
    "relevo": relevo.recortar,
    "hand": hand.calcular,
    "validacao": validacao.validar,
    "carta": carta.comparar,
    "noticias": noticias.testar,
    "areas": areas.extrair,
    "recomendacoes": recomendacoes.recomendar,
    "sensibilidade": sensibilidade.analisar,
}


def main():
    parser = argparse.ArgumentParser(prog="pipeline", description="Gera as camadas do CityShield.")
    parser.add_argument("passo", nargs="?", choices=PASSOS, help="roda só este passo")
    parser.add_argument("--refazer", action="store_true", help="refaz mesmo se o arquivo já existir")
    args = parser.parse_args()

    escolhidos = [args.passo] if args.passo else list(PASSOS)
    for nome in escolhidos:
        PASSOS[nome](refazer=args.refazer)


if __name__ == "__main__":
    main()
