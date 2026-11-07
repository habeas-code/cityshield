"""Ponto de entrada do pipeline.

    python -m pipeline            roda todos os passos
    python -m pipeline relevo     roda só o passo do relevo
    python -m pipeline hand       drenagem e HAND (baixa o relevo se faltar)
    python -m pipeline hand --refazer
    python -m pipeline validacao  testa o HAND contra os registros da Defesa Civil
    python -m pipeline areas      áreas candidatas a soluções verdes no piloto
"""

import argparse

from pipeline import areas, hand, relevo, validacao

PASSOS = {
    "relevo": relevo.recortar,
    "hand": hand.calcular,
    "validacao": validacao.validar,
    "areas": areas.extrair,
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
