# Deploy

Banco no **Neon**, API no **Render**, ping no **GitHub Actions**. O site continua no GitHub Pages (#23).

```
navegador ──► site (GitHub Pages)
     └──────► API (Render, Virginia) ──► banco (Neon, AWS US East 1, Virginia)
GitHub Actions ──► GET / a cada 10 min · GET /saude a cada 6 h
```

API e banco ficam na mesma região (leste dos EUA) para cada consulta não atravessar o continente.

**Nenhuma senha vai para o git.** As URLs do banco ficam só no painel do Render e no terminal na hora da carga. O endereço público da API não é segredo.

## As contas: por que o ping chama a `/` e não a `/saude`

Os dois serviços são gratuitos e **dormem** quando ninguém usa:

| | Limite do plano gratuito | Fonte |
|---|---|---|
| **Neon** (banco) | **100 CU-horas** por mês. O banco gratuito roda com **0,25 CU** e **desliga depois de 5 min parado** (não dá para mudar). Acorda sozinho na próxima consulta, em menos de 1 s. **5 GB de transferência** por mês. Se as CU-horas **ou** a transferência acabarem, o banco fica **suspenso até o mês seguinte**. | [Neon, planos](https://neon.com/docs/introduction/plans); [Neon, limites do plano gratuito](https://neon.com/faqs/free-plan-limits-and-quotas) |
| **Render** (API) | **Dorme depois de 15 min sem acesso** e leva **cerca de 1 min** para acordar. **750 horas** por mês por workspace; se acabarem, todos os serviços gratuitos ficam suspensos até o mês seguinte. | [Render, plano gratuito](https://render.com/docs/free) |

**CU-hora** é o tamanho do banco vezes o tempo ligado. Pela conta do Neon, 0,25 CU por 4 horas = 1 CU-hora. Então:

- **100 CU-horas ≈ 400 horas de banco ligado no mês** (100 ÷ 0,25).
- Se o banco **nunca desligasse**: 30 dias × 24 h × 0,25 CU = **180 CU-horas**. As 100 acabariam em **cerca de 16 dias** (400 h ÷ 24 h), no meio da avaliação.

É isso que aconteceria se o ping ou o health check do Render chamassem a `/saude`, que consulta o banco: ele seria acordado a cada poucos minutos e nunca desligaria. Por isso:

- **`GET /`** (não toca no banco) é o health check do Render e o ping a cada 10 min. Mantém a **API** acordada e deixa o **banco** desligar.
- **`GET /saude`** (testa o banco) roda só **a cada 6 h**: 4 vezes por dia × ~5 min ligado = ~10 h por mês = **~2,5 CU-horas**. Sobra quase tudo para as visitas de verdade.

O health check do Render é um **`GET /`** a cada poucos segundos ([Render, health checks](https://render.com/docs/health-checks)); como a `/` não toca no banco, ele também não acorda o Neon.

No Render, o ping a cada 10 min deixa a API **quase sempre** acordada: 30 × 24 = **720 horas** (744 num mês de 31 dias), dentro das 750, **desde que seja o único serviço gratuito do workspace**. "Quase" porque o GitHub pode atrasar ou pular agendamentos: se passarem 15 min sem nenhum acesso, o Render dorme, e a próxima visita espera **cerca de 1 min**.

### Transferência: 5 GB por mês

O Neon também conta o que **sai do banco**. A `/camadas/risco` sem bbox tira **~1,8 MB** do banco por chamada (a camada inteira), então **~2.800 chamadas** (5.000 MB ÷ 1,8 MB) gastam os 5 GB do mês. O GZip da API não ajuda aqui: ele comprime a resposta para o navegador, mas o que conta no Neon é o que vai do banco para a API. Com bbox (a área visível do mapa), cada chamada tira bem menos. O site lê os arquivos estáticos de `docs/dados/` (D10), então as visitas ao site não gastam essa transferência; só quem chama a API.

## 1. Neon: projeto e extensão

1. Em [console.neon.tech](https://console.neon.tech), **New Project**:
   - nome: `cityshield`;
   - Postgres: **16** (o mesmo do `docker-compose.yml`);
   - região: **AWS US East 1 (N. Virginia)**.
2. Anote o **nome do banco** e o **usuário dono** (o que nasce com o projeto, algo como `neondb_owner`). A carga usa esse usuário.
3. No **SQL Editor**, conectado com o usuário dono:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   SELECT postgis_version();
   ```
   Tem que mostrar a versão do PostGIS. (A carga também cria a extensão se faltar; rodar aqui confirma que o projeto aceita.)
4. Mantenha o tamanho do banco em **0,25 CU**. Com um tamanho maior, as CU-horas acabam mais rápido na mesma proporção.

## 2. Carga do seu computador para o Neon

A carga é o mesmo `db/carga.py` do Docker: cria as tabelas se faltarem, apaga o conteúdo antigo e grava as camadas de `docs/dados/` numa transação só. Rodar de novo dá o mesmo resultado. **Rode de novo sempre que `docs/dados/` mudar na main.**

1. No Neon, **Connect** → escolha o usuário **dono** e a conexão **direta** (desligue *Connection pooling*; o endereço fica **sem** `-pooler`). Copie a URL. Ela começa com `postgresql://` e tem a senha.
2. No PowerShell, na pasta do projeto:
   ```powershell
   $env:DATABASE_URL = Read-Host "URL do Neon (dono, conexão direta)"
   docker compose run --rm --no-deps -e DATABASE_URL carga
   Remove-Item Env:DATABASE_URL
   ```
   (No Git Bash: `read -rs DATABASE_URL && export DATABASE_URL`, o mesmo `docker compose run` e depois `unset DATABASE_URL`.)
3. Tem que aparecer `Carga ok: risco 777, drenagem 543, ruas 79, areas 48.` (os números acompanham os arquivos).

Por que assim:

- **A senha não vai para nenhum arquivo.** Ela fica só na variável do terminal e some no `Remove-Item`. O que você cola no `Read-Host` não entra no histórico do PowerShell. **Não** coloque a URL do Neon no `.env` nem em outro arquivo do projeto.
- `-e DATABASE_URL` sem valor passa a variável do terminal para o container e vale mais que o `.env`; `--no-deps` não sobe o banco local.
- A carga aceita a URL como o Neon mostra (`postgresql://`) e garante a conexão criptografada (`sslmode=require`). Se algo der errado, a mensagem de erro **não mostra a senha**.

## 3. Neon: usuário só de leitura para a API

A API só lê (D7), então ela entra com um usuário que **só pode fazer SELECT**. Se alguém achar uma falha na API, não consegue apagar nem mudar nada no banco.

**Crie esse usuário por SQL, e não pelo painel.** Usuários criados pelo painel do Neon ganham o papel `neon_superuser` (podem gravar em tudo, criar bancos e usuários). Criados por SQL, começam só com o básico, e damos apenas leitura ([Neon, usuários](https://neon.com/docs/manage/roles)).

1. Gere uma senha forte (o Neon exige pelo menos 60 bits de entropia):
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Ela só tem letras, números, `-` e `_`, então entra na URL sem precisar de ajuste.
2. No **SQL Editor**, conectado com o usuário **dono**, troque `SENHA-GERADA` e `NOME-DO-BANCO`:
   ```sql
   CREATE ROLE cityshield_api WITH LOGIN PASSWORD 'SENHA-GERADA';
   GRANT CONNECT ON DATABASE "NOME-DO-BANCO" TO cityshield_api;
   GRANT USAGE ON SCHEMA public TO cityshield_api;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO cityshield_api;
   -- tabelas que a carga criar no futuro também ficam legíveis
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO cityshield_api;
   ALTER ROLE cityshield_api SET statement_timeout = '5s';
   ```
   Rode depois da carga (passo 2), para as tabelas já existirem.

**Por que 5 s (`statement_timeout`):** uma consulta presa é cancelada em 5 s em vez de travar a API. O limite fica no usuário, e não na conexão, porque o endereço com pooler do Neon recusa o parâmetro `options` (erro *unsupported startup parameter*, [Neon, erros de conexão](https://neon.com/docs/connect/connection-errors)). No Docker, isso já acontece sozinho pelo `db/init/02_statement_timeout.sql`.

**Conferir**, no SQL Editor (que roda como o dono; o `cityshield_api` não aparece na lista de usuários do Neon):

```sql
SELECT
    has_table_privilege('cityshield_api', 'areas', 'SELECT')    AS pode_ler,
    has_table_privilege('cityshield_api', 'areas', 'DELETE')    AS pode_apagar,
    has_table_privilege('cityshield_api', 'risco', 'INSERT')    AS pode_gravar,
    pg_has_role('cityshield_api', 'neon_superuser', 'MEMBER')   AS e_superusuario,
    (SELECT rolconfig FROM pg_roles WHERE rolname = 'cityshield_api') AS config;
```

Resultado esperado:

| pode_ler | pode_apagar | pode_gravar | e_superusuario | config |
|---|---|---|---|---|
| `t` | `f` | `f` | `f` | `{statement_timeout=5s}` |

Ou seja: lê, não apaga, não grava, não é `neon_superuser` e tem o limite de 5 s.

## 4. Render: a API

1. **Monte a `DATABASE_URL` do `cityshield_api`.** O *Connect* do Neon não lista usuários criados por SQL, então:
   - no Neon, **Connect** → usuário **dono**, com **Connection pooling** ligado (o endereço tem `-pooler`) → copie a URL;
   - troque o **usuário** e a **senha** do dono por `cityshield_api` e a senha gerada no passo 3;
   - mantenha o final `?sslmode=require&channel_binding=require`;
   - troque o começo `postgresql://` por **`postgresql+psycopg://`** (o driver que a API usa; a carga faz isso sozinha, a API não).

   Fica assim: `postgresql+psycopg://cityshield_api:SENHA@HOST-pooler/NOME-DO-BANCO?sslmode=require&channel_binding=require`
2. Em [dashboard.render.com](https://dashboard.render.com), **New** → **Web Service** → **Public Git Repository** → `https://github.com/habeas-code/cityshield`.
3. Preencha:

   | Campo | Valor |
   |---|---|
   | Language | **Docker** |
   | Branch | `main` (para testar uma branch antes do PR, escolha a branch e volte para `main` depois do merge) |
   | Root Directory | **`api`** |
   | Dockerfile Path | **`./Dockerfile`** (dentro de `api/`) |
   | Region | **Virginia (US East)** |
   | Instance Type | **Free** |
   | Health Check Path (em *Advanced*) | **`/`** (nunca `/saude`: veja "As contas" acima). O health check é `GET`; a `/` também aceita `HEAD`, para monitores e para o `HEAD` que aparece no log no início do deploy |
   | Auto-Deploy | **Off** |

4. **Environment Variables**:

   | Nome | Valor |
   |---|---|
   | `DATABASE_URL` | a URL do passo 1 |
   | `CORS_ORIGINS` | `http://localhost:5173,https://habeas-code.github.io` |

   **Não** crie `PORT`: o Render define sozinho, e a API escuta nela (`api/Dockerfile`).
5. **Create Web Service**. O primeiro build leva alguns minutos.

**Atualizar a API:** com o Auto-Deploy desligado, um merge na `main` **não** publica sozinho. Depois do merge, no Render: **Manual Deploy** → **Deploy latest commit**. Assim nada muda no ar sem alguém decidir (por exemplo, perto da avaliação).

**Conferir** (o endereço da API é `https://cityshield-s2lq.onrender.com`):

```powershell
curl.exe -s https://cityshield-s2lq.onrender.com/                     # nome e versão
curl.exe -s https://cityshield-s2lq.onrender.com/saude                # {"status":"ok","banco":"ok"}
curl.exe -s "https://cityshield-s2lq.onrender.com/cenario?chuva_mm=50" # chega_m3, retida_m3...
curl.exe -s -D - -o NUL -H "Origin: https://habeas-code.github.io" https://cityshield-s2lq.onrender.com/
#   tem que ter: access-control-allow-origin: https://habeas-code.github.io
```

Também dá para abrir `https://cityshield-s2lq.onrender.com/docs` no navegador.

## 5. Ping no GitHub Actions

O `.github/workflows/ping.yml` já aponta para a API (`API_URL: https://cityshield-s2lq.onrender.com`). Se o endereço mudar, troque ali num PR.

Depois do merge: aba **Actions** → **Ping da API** → **Run workflow**. Os dois jobs têm que ficar verdes.

O que ele faz:

- **a cada 10 min, `GET /`**: mantém a API quase sempre acordada, sem acordar o banco. Tenta de novo até 4 vezes (20 s entre elas, até 60 s cada) enquanto o Render acorda.
- **a cada 6 h, `GET /saude`**: acorda o banco e confere. Se não vier 200, o job fica vermelho e o GitHub manda e-mail.

Não precisa de segredo no GitHub: o endereço da API é público. Os agendamentos só rodam a partir da `main`, podem atrasar ou ser pulados (aí a API pode dormir e a próxima visita espera ~1 min), e o GitHub desliga agendamentos de repositórios públicos sem atividade por 60 dias.

## Onde fica cada coisa

| O quê | Onde | No git? |
|---|---|---|
| URL do Neon com o usuário dono | só no terminal, na hora da carga | não |
| URL do Neon com `cityshield_api` | painel do Render (`DATABASE_URL`) | não |
| `CORS_ORIGINS` | painel do Render | não (o valor está neste guia, não é segredo) |
| Endereço público da API | `.github/workflows/ping.yml` | sim (não é segredo) |
| `.env` do Docker local | seu computador (`.gitignore`) | não |

## Checklist (#23)

- [ ] Neon: projeto na AWS US East 1, PostGIS ativo, carga com `Carga ok`
- [ ] Neon: `cityshield_api` criado por SQL, com `SELECT` e `statement_timeout` de 5 s
- [ ] Render: Docker, raiz `api`, `./Dockerfile`, Virginia, health check em `/`, Auto-Deploy Off
- [ ] Render: `DATABASE_URL` do `cityshield_api` e `CORS_ORIGINS` com `http://localhost:5173,https://habeas-code.github.io`
- [ ] Render: Branch `main` depois do merge
- [ ] `/`, `/saude` e o CORS conferidos no endereço do Render
- [ ] `ping.yml` com o endereço real e os dois jobs verdes
