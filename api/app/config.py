"""Configurações da API, lidas das variáveis de ambiente.

No computador elas vêm do arquivo .env (o docker compose lê sozinho). No Render,
vêm do painel de variáveis de ambiente. Nenhuma senha fica no código.
"""

import logging
import os

log = logging.getLogger(__name__)


def url_do_banco() -> str:
    """Endereço do banco, com usuário e senha (DATABASE_URL)."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Falta a variável DATABASE_URL. Copie o .env.example para .env.")
    return url


def origens_cors() -> list[str]:
    """Sites que o navegador deixa chamar a API, lidos de CORS_ORIGINS.

    Exemplo: CORS_ORIGINS=http://localhost:5173,https://habeas-code.github.io

    "*" (qualquer site) é ignorado de propósito: só entram endereços escritos
    um por um. A barra no fim é tirada, porque o navegador manda o endereço sem
    ela e, com ela, nunca daria igual.
    """
    origens = []
    for item in os.environ.get("CORS_ORIGINS", "").split(","):
        origem = item.strip().rstrip("/")
        if not origem:
            continue
        if origem == "*":
            log.warning("CORS_ORIGINS tem '*': ignorado. Liste os endereços um por um.")
            continue
        origens.append(origem)
    return origens
