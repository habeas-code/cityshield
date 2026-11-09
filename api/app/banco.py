"""Conexão da API com o banco (PostGIS).

A API inteira usa um único "motor" (engine) do SQLAlchemy. Ele mantém algumas
conexões abertas (o pool) e empresta uma a cada pedido, em vez de abrir uma
conexão nova toda vez, o que seria lento.

A API só LÊ o banco (D7). Quem grava as camadas é a carga (#10).

O limite de 5 s por consulta (statement_timeout) não fica aqui, e sim no
próprio banco (db/init/02_statement_timeout.sql e docs/deploy.md): o endereço
com pooler do Neon recusa esse parâmetro na hora de conectar.
"""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.config import url_do_banco

log = logging.getLogger(__name__)

engine = create_engine(
    url_do_banco(),
    pool_size=2,  # poucas conexões: a API é pequena e o Neon gratuito tem limite
    max_overflow=3,  # até 3 a mais num pico de acessos
    pool_pre_ping=True,  # testa a conexão antes de usar: o Neon fecha as que ficam paradas
    connect_args={"connect_timeout": 5},  # desiste de conectar depois de 5 s
)


def banco_responde() -> bool:
    """Faz a menor consulta possível (SELECT 1) e diz se o banco respondeu."""
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as erro:
        # O detalhe vai só para o log do servidor, nunca para quem chamou a API.
        log.warning("Banco não respondeu ao SELECT 1: %s", erro.__class__.__name__)
        return False
