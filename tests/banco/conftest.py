"""Preparação dos testes contra um PostGIS de verdade (#108).

Rodam no job "Banco de verdade (PostGIS)" do CI, depois da carga e da criação
do cityshield_api (tests/banco/usuario_api.py). Precisam de duas variáveis:

  - URL_API: o banco com o usuário cityshield_api (só leitura), que a API usa;
  - URL_DONO: o banco com o usuário dono, só para conferir as permissões.

Sem URL_API, os testes que usam o banco são pulados: o pytest de sempre
continua sem precisar de banco.

A API lê a DATABASE_URL quando é importada, por isso ela é definida aqui,
antes do import.
"""

import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "api"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

URL_API = os.environ.get("URL_API")
URL_DONO = os.environ.get("URL_DONO")


@pytest.fixture(scope="session")
def cliente():
    if not URL_API:
        pytest.skip("sem URL_API: estes testes precisam de um PostGIS de verdade")
    os.environ["DATABASE_URL"] = URL_API
    os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest.fixture(scope="session")
def banco_api():
    """Conexão direta com o usuário cityshield_api, para tentar gravar."""
    if not URL_API:
        pytest.skip("sem URL_API")
    from sqlalchemy import create_engine

    return create_engine(URL_API)


@pytest.fixture(scope="session")
def banco_dono():
    if not URL_DONO:
        pytest.skip("sem URL_DONO")
    from sqlalchemy import create_engine

    return create_engine(URL_DONO)
