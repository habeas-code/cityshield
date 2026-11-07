"""Onde o pipeline lê e grava arquivos.

No Docker, o compose monta:
    /app         -> pipeline/            (código e pipeline/dados/, fora do git)
    /saida       -> web/public/dados/    (camadas que o site lê)
    /referencia  -> docs/dados/          (limite do município etc., só leitura)

Fora do Docker, os mesmos caminhos são achados a partir da pasta do repositório.
"""

import os
from pathlib import Path

PIPELINE = Path(__file__).resolve().parent.parent
REPO = PIPELINE.parent


def _pasta(variavel, no_docker, local):
    if os.environ.get(variavel):
        return Path(os.environ[variavel])
    return Path(no_docker) if Path(no_docker).is_dir() else local


DADOS = PIPELINE / "dados"
SAIDA = _pasta("CITYSHIELD_SAIDA", "/saida", REPO / "web" / "public" / "dados")
REFERENCIA = _pasta("CITYSHIELD_REFERENCIA", "/referencia", REPO / "docs" / "dados")
