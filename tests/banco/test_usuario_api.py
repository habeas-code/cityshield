"""O CI tem que falhar com mensagem clara se o SQL do guia mudar de formato (#108).

Não precisam de banco.
"""

import pytest

from usuario_api import GUIA, GuiaMudou, preencher, sql_do_guia

SQL_OK = """
## 3. Neon: usuário só de leitura para a API

   ```sql
   CREATE ROLE cityshield_api WITH LOGIN PASSWORD 'SENHA-GERADA';
   GRANT CONNECT ON DATABASE "NOME-DO-BANCO" TO cityshield_api;
   ```

## 4. Render: a API
"""


def test_guia_de_verdade_tem_o_bloco_com_as_duas_marcas():
    sql = sql_do_guia(GUIA.read_text(encoding="utf-8"))

    assert "CREATE ROLE cityshield_api" in sql
    assert "SENHA-GERADA" in sql and "NOME-DO-BANCO" in sql


def test_preenche_senha_e_banco():
    sql = preencher(sql_do_guia(SQL_OK), "s3nha", "cityshield")

    assert "PASSWORD 's3nha'" in sql
    assert 'DATABASE "cityshield"' in sql


@pytest.mark.parametrize(
    ("texto", "motivo"),
    [
        (SQL_OK.replace("## 3.", "## 9."), 'seção que começa com "## 3."'),
        (SQL_OK.replace("CREATE ROLE", "CRIAR"), "CREATE ROLE cityshield_api"),
        (SQL_OK.replace("```sql", "```"), "CREATE ROLE cityshield_api"),
        (SQL_OK.replace("SENHA-GERADA", "x"), "não tem SENHA-GERADA"),
        (SQL_OK.replace("NOME-DO-BANCO", "x"), "não tem NOME-DO-BANCO"),
        (
            SQL_OK.replace("SENHA-GERADA", "x").replace("NOME-DO-BANCO", "y"),
            "não tem SENHA-GERADA nem NOME-DO-BANCO",
        ),
    ],
)
def test_guia_fora_do_formato_da_erro_claro(texto, motivo):
    with pytest.raises(GuiaMudou, match=motivo):
        sql_do_guia(texto)


def test_bloco_fora_da_secao_3_nao_vale():
    # O bloco certo existe, mas está na seção 4.
    texto = SQL_OK.replace(
        "## 3. Neon: usuário só de leitura para a API\n", "## 3. Neon\n\nnada\n\n## 4. Outra\n"
    )

    with pytest.raises(GuiaMudou, match="CREATE ROLE cityshield_api"):
        sql_do_guia(texto)
