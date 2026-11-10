# AGENTS.md: como trabalhar no CityShield

Guia para agentes de IA (Devin e outros) que abrem PRs neste repositório. Leia inteiro antes de começar. O guia completo do time está em [CONTRIBUTING.md](CONTRIBUTING.md) e as decisões em [docs/decisoes.md](docs/decisoes.md).

## Regras que não podem ser quebradas

1. **Nunca faça push na `main`.** Trabalhe numa branch `tipo/descricao-curta` criada a partir da `main` atualizada e abra um Pull Request. A `main` exige 1 aprovação humana.
2. **Título do PR e commits no padrão** (o CI recusa outro formato): `tipo(escopo): descrição em português, no presente`. Tipos: `feat fix docs style refactor test data chore`. Escopos: `pipeline api web docs db infra`. Exemplo: `test(web): teste de fumaça das quatro abas da plataforma`.
3. **Ligue o PR à issue** com `Closes #N` na descrição (em inglês: `Closes`, `Fixes` ou `Resolves`).
4. **Peça revisão** de `LucasAmadoS` (site e pipeline) ou `rafaelsiverisaugusto` (`api/` e `db/`).
5. **Não adicione linhas de autoria de IA**: nada de `Co-Authored-By` de bot, "Generated with..." ou links de sessão em commits e PRs.
6. **Nada privado no repositório:** nunca crie nem leia `dados_privados/`, nunca grave `.env`, senhas ou chaves de API, nunca commite arquivos `.tif`. Os registros da Defesa Civil aparecem **por rua**, nunca por endereço com número.
7. **Todo número tem fonte (D11).** Não invente valores, percentuais nem "índices". Se precisar de um número novo, use uma fonte publicada e escreva a fonte junto, no código e no texto. Se não houver fonte, pergunte no PR.
8. **Não ajuste parâmetros para melhorar a validação.** Os limiares do HAND (0,5 km², 5 m, 15 m) e as premissas de `pipeline/pipeline/volumes.py` são fixos e documentados.
9. **Uma tarefa por PR, pequena.** Se a issue pedir algo ambíguo, faça a menor versão que resolve e explique no PR o que ficou de fora.

## O que é o projeto

CityShield (time Habeas Code, Hack Brasil 2026, trilha Meio Ambiente) mostra **onde Sorocaba (SP) alaga e que solução verde cabe em cada lugar**:
- risco de enchente calculado do relevo (método HAND sobre o ANADEM 30 m), validado com registros da Defesa Civil;
- áreas candidatas na área-piloto (parque inundável, jardim de chuva, piso permeável, telhado verde), com nota de prioridade e volume de água, sempre com fonte;
- simulação de chuva.

É uma **ferramenta de triagem**, não modelagem hidráulica nem projeto de obra. Os textos dizem isso, e não podem dizer o contrário.

Prazos: congelamento em 26/11/2026 e entrega em 29/11/2026. Prefira estabilidade a novidade.

## Estrutura

| Pasta | O que tem | Responsável |
|---|---|---|
| `pipeline/` | Python que gera as camadas (relevo, HAND, validação, áreas, recomendações, sensibilidade, carta). Roda no Docker. | Lucas |
| `docs/` | **O site** publicado no GitHub Pages: `index.html` (página inicial), `mapa.html` (plataforma), `comum.js`, `dados/` (camadas que o site lê), `vendor/` (MapLibre 4.7.1) e documentação (`decisoes.md`, `validacao.md`, `recomendacoes.md`, `CRONOGRAMA.md`) | Lucas |
| `web/public/dados/` | Saída do pipeline. É copiada para `docs/dados/` | Lucas |
| `api/` | FastAPI que lê o PostGIS (`/saude`, `/camadas/...`) | Rafael |
| `db/` | SQL das tabelas (`db/init/`) e carga dos GeoJSON (`db/carga.py`) | Rafael |

## Comandos

```bash
# Tudo (banco + carga + API em http://localhost:8000, docs em /docs)
cp .env.example .env          # só na primeira vez; valores de exemplo, sem segredo
docker compose up --build

# Pipeline (cada passo pula se a saída já existe; --refazer força)
docker compose build pipeline
docker compose run --rm pipeline python -m pipeline <passo> [--refazer]
#   passos: relevo hand validacao carta areas recomendacoes sensibilidade

# Testes e lint (os mesmos do CI)
pip install -r api/requirements-dev.txt
(cd db && python -m pytest -q)
(cd api && python -m pytest -q)
pip install ruff && ruff check pipeline api db --select E9,F63,F7,F82
# Site no navegador (Playwright): quatro abas sem erro no console, também em 390 px
pip install -r tests/site/requirements.txt && python -m playwright install --with-deps chromium
python -m pytest -q tests/site

# Site: HTML puro, sem build. Sirva a pasta docs/ e abra no navegador
python -m http.server 8080 -d docs   # http://localhost:8080/mapa.html
```

O pipeline baixa dados públicos na primeira vez (ANADEM por partes, OpenStreetMap pela Overpass, carta do SGB por partes) e guarda em `pipeline/dados/`, que fica fora do git.

## Site (`docs/`)

- **HTML, CSS e JavaScript puros**, sem framework e sem passo de build (D14). Não adicione React, bundler ou npm ao site.
- O site lê só arquivos de `docs/dados/`. Quando o pipeline muda uma saída, copie de `web/public/dados/` para `docs/dados/` no mesmo PR.
- O `mapa.html` tem muito código num `<script>` só. **Cuidado com nomes:** uma função nova com o nome de uma variável que já existe quebra a página (já aconteceu com `lista`). Procure o nome no arquivo antes de criar.
- **Teste no navegador** toda mudança: abra as quatro abas (Diagnóstico, Oportunidades, Simulação, Sobre), clique numa área da lista e confira que **não há erro no console**. Confira também numa tela de 390 px de largura (celular).
- **Visual:** discreto, no estilo de CARTO, ArcGIS e Mapbox. Nada de vidro fosco, brilho, gradiente, texto mono em maiúsculas ou cards coloridos. **Não mude as cores do mapa** (risco em vermelho, áreas e pontos): o time já escolheu.
- Textos do site em **português do Brasil, frases curtas e simples**, para quem não é da área.

## Pipeline (`pipeline/`)

- Python 3.12 no Docker (`pipeline/Dockerfile`). As versões ficam fixas em `pipeline/requirements.txt` (`numpy` < 2.4 por causa do pysheds).
- Cada passo é uma função `passo(refazer=False)` registrada em `pipeline/pipeline/__main__.py`.
- As premissas e as fontes dos volumes ficam no começo de `volumes.py` e saem no campo `parametros` de `recomendacoes.geojson`, que o site lê. Não duplique números no site: leia de `parametros`.
- Depois de mudar um passo, rode de novo e confira o diff das saídas: só pode mudar o que você pretendia.

## API e banco (`api/`, `db/`)

- A API devolve **o mesmo conteúdo** dos arquivos de `docs/dados/`, para o site poder trocar um pelo outro (plano B, D10).
- SQL sempre parametrizado. Erro do banco vira 503 sem detalhe técnico na resposta.
- Os testes não precisam de banco (o `conftest.py` aponta para uma porta vazia).

## Antes de abrir o PR

- [ ] CI local: `ruff` e os dois `pytest` passam
- [ ] site testado no navegador, sem erro no console, também em 390 px (se mexeu em `docs/`)
- [ ] números novos têm fonte escrita junto
- [ ] documentação atualizada se algo mudou para quem usa (`README.md`, `docs/*.md`)
- [ ] descrição do PR em português: **o que muda**, **como testei** e o que ficou de fora
