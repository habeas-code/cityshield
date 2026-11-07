"""Ponto de entrada do pipeline.

    python -m pipeline            roda todos os passos
    python -m pipeline relevo     roda só o passo do relevo
    python -m pipeline relevo --refazer
"""

import argparse

from pipeline import relevo

PASSOS = {
    "relevo": relevo.recortar,
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
