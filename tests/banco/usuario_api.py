"""Cria o usuário só de leitura da API (cityshield_api) com o SQL do guia (#108).

Lê o bloco SQL da seção 3 do docs/deploy.md ("Neon: usuário só de leitura para
a API"), troca SENHA-GERADA e NOME-DO-BANCO e roda no banco como o dono. O SQL
não é copiado para cá: se o guia mudar, o CI testa o guia novo.

Uso (no CI, depois da carga):
    DATABASE_URL=<dono>  SENHA_API=<senha>  python tests/banco/usuario_api.py

Se o bloco não for encontrado, ou não tiver SENHA-GERADA e NOME-DO-BANCO, sai
com erro e diz o que faltou.
"""

import os
import re
import sys
from pathlib import Path

GUIA = Path(__file__).resolve().parents[2] / "docs" / "deploy.md"
TITULO_SECAO = "## 3."
MARCAS = ("SENHA-GERADA", "NOME-DO-BANCO")


class GuiaMudou(Exception):
    """O docs/deploy.md não tem mais o SQL no formato que o CI espera."""


def sql_do_guia(texto: str) -> str:
    """O bloco ```sql da seção 3 que cria o cityshield_api, ainda com as marcas."""
    inicio = texto.find("\n" + TITULO_SECAO)
    if inicio == -1:
        raise GuiaMudou(f'docs/deploy.md: não achei a seção que começa com "{TITULO_SECAO}".')
    fim = texto.find("\n## ", inicio + 1)
    secao = texto[inicio : fim if fim != -1 else len(texto)]

    for bloco in re.findall(r"```sql\n(.*?)```", secao, flags=re.DOTALL):
        if "CREATE ROLE cityshield_api" in bloco:
            break
    else:
        raise GuiaMudou(
            "docs/deploy.md: não achei, na seção 3, o bloco ```sql com "
            '"CREATE ROLE cityshield_api".'
        )

    faltam = [marca for marca in MARCAS if marca not in bloco]
    if faltam:
        raise GuiaMudou(
            "docs/deploy.md: o bloco SQL da seção 3 não tem "
            + " nem ".join(faltam)
            + ". O CI troca essas marcas pela senha e pelo nome do banco de teste."
        )
    # O guia é lido com recuo de lista (3 espaços); o SQL não liga, mas fica limpo.
    return "\n".join(linha.strip() for linha in bloco.splitlines())


def preencher(sql: str, senha: str, banco: str) -> str:
    return sql.replace("SENHA-GERADA", senha).replace("NOME-DO-BANCO", banco)


def main() -> int:
    from sqlalchemy import create_engine, make_url

    url = make_url(os.environ["DATABASE_URL"])
    try:
        sql = sql_do_guia(GUIA.read_text(encoding="utf-8"))
    except GuiaMudou as erro:
        print(f"Usuário da API não criado: {erro}", file=sys.stderr)
        return 1

    engine = create_engine(url)
    with engine.begin() as conexao:
        # Sem parâmetros, o psycopg roda os vários comandos do bloco de uma vez.
        conexao.exec_driver_sql(preencher(sql, os.environ["SENHA_API"], url.database))
    print("Usuário cityshield_api criado com o SQL de docs/deploy.md (seção 3).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
