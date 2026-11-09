"""Preparação comum dos testes.

As variáveis são definidas ANTES de importar a API, porque ela lê o
CORS_ORIGINS e cria a conexão com o banco no momento em que é importada.

O banco aponta para a porta 1 de propósito: lá nunca há banco, então o
SELECT 1 falha na hora. Assim o teste do 503 é real, sem truque.
"""

import os

os.environ["DATABASE_URL"] = "postgresql+psycopg://teste:teste@127.0.0.1:1/teste"
os.environ["CORS_ORIGINS"] = "http://localhost:5173,https://habeas-code.github.io"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def cliente():
    """Um "navegador de mentira" que chama a API sem precisar subir o servidor."""
    return TestClient(app)
