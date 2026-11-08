"""Configurações da API, lidas das variáveis de ambiente.

No computador elas vêm do arquivo .env (o docker compose lê sozinho). No Render,
vêm do painel de variáveis de ambiente. Nenhuma senha fica no código.
"""

import os


def url_do_banco() -> str:
    """Endereço do banco, com usuário e senha (DATABASE_URL)."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Falta a variável DATABASE_URL. Copie o .env.example para .env.")
    return url

