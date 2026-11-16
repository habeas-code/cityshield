<img src="docs/logo.svg" alt="" width="56">

# CityShield

**Onde Sorocaba alaga e onde soluções verdes podem segurar essa água.**

[![CI](https://github.com/habeas-code/cityshield/actions/workflows/ci.yml/badge.svg)](https://github.com/habeas-code/cityshield/actions/workflows/ci.yml)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE)

Projeto do time **Habeas Code** para o [Hack Brasil 2026](https://hackbrasil.com), trilha **Meio Ambiente**.

🗺️ **[Abrir a plataforma](https://habeas-code.github.io/cityshield/mapa.html)** · 🌐 [Página do projeto](https://habeas-code.github.io/cityshield/) · 📋 [Quadro de tarefas](https://github.com/orgs/habeas-code/projects/1) · 📅 [Cronograma](docs/CRONOGRAMA.md) · 🧭 [Decisões](docs/decisoes.md) · ✅ [Validação](docs/validacao.md) · 🌱 [Recomendações](docs/recomendacoes.md)

> **🇬🇧 In English**
>
> **CityShield shows where Sorocaba (Brazil) floods and where nature-based solutions could hold that water.** The city's Civil Defense logged 250+ flooding events on 89 streets in 2022–2023, mostly on the same streets every year. The city already discusses "sponge city" measures, but lacks a practical answer to *which solution to study first, and where*.
>
> **Working today:** flood risk computed from the terrain for the whole city (HAND method on the ANADEM 30 m terrain model), tested three times against reality:
>
> - **2022–2023 Civil Defense records:** 74% fall in the high-risk zones, which hold only 12% of the city's streets (6× chance).
> - **Floods that happened after the map was finished:** official Civil Defense data, obtained through a freedom-of-information request, list 102 flood calls between 8 and 12 Nov 2026, the days right after the map was built. **89% of them fell in high or medium risk zones (30% of the streets); the official 2015 flood map covered 33%.**
> - **Streets the map had never seen** (not in the 2022–2023 reports): 72% of their official records fall in the high-risk zones (5.8× chance).
>
> In the pilot area, the platform ranks 48 candidate sites (parks, green areas, parking lots, large roofs), recommends a nature-based solution for each with a priority score, and estimates how much water each could hold for a chosen rainfall, always with a source. It is a screening tool to decide where to study first, not a hydraulic model.
>
> **For:** Civil Defense and city departments deciding where to invest; it directly benefits residents of streets that flood every year. **Stack:** Python pipeline (rasterio, pysheds, shapely) → static GeoJSON + PostGIS → FastAPI; map with MapLibre on GitHub Pages. Team docs are in Portuguese.

---

## O problema

Sorocaba (SP) alaga todo verão, e quase sempre nos mesmos lugares. Os relatórios da Defesa Civil de 2022 e 2023 registram **mais de 250 ocorrências de alagamento e inundação em 89 ruas**. A **Av. Dom Aguirre** aparece 23 vezes; a **Av. XV de Agosto** está em 10 dos 15 relatórios. Em 20/01/2024, a água arrastou um carro até a Av. Juvenal de Campos. E continua: em **2026**, a XV de Agosto foi interditada por alagamento em setembro e em outubro, e a Dom Aguirre em outubro.

A cidade já discute soluções baseadas na natureza (a "cidade-esponja"): jardins de chuva, piso permeável, telhados verdes, parques que podem alagar. Há até um projeto de lei sobre isso na Câmara (2024). Mas falta responder uma pergunta prática: **em qual terreno vale a pena estudar qual solução primeiro?**

Sorocaba já tem mapa de suscetibilidade a inundação (IPT e Serviço Geológico do Brasil, 2015). Ele mostra **onde** é perigoso, mas não diz **o que fazer** em cada lugar. É essa lacuna que o CityShield ocupa.

## O que o CityShield faz

| | O quê | Situação |
|---|---|---|
| 1 | **Mostra o risco pelo relevo:** para cada ponto da cidade, quantos metros ele está acima do córrego mais próximo (método HAND). Quanto mais baixo, mais fácil a água chegar. | ✅ pronto |
| 2 | **Testa o próprio mapa** contra as ocorrências reais da Defesa Civil. | ✅ pronto |
| 3 | **Encontra áreas candidatas** perto dos pontos críticos: parques, praças, estacionamentos e telhados grandes do OpenStreetMap, com o risco de cada uma. | ✅ pronto no piloto |
| 4 | **Recomenda uma solução** para cada área e dá uma **nota de prioridade** (risco × ocorrências × área). [Como funciona](docs/recomendacoes.md) | ✅ pronto no piloto |
| 5 | **Estima quanta água** cada solução seguraria numa chuva escolhida, com a fonte de cada número. [Como funciona](docs/recomendacoes.md#quanta-água-cada-solução-segura-17) | ✅ pronto no piloto |

**Piloto:** núcleo Norte (Parque das Águas, Jd. Maria do Carmo, Abaeté), raio de 800 m, onde se concentram 41 registros. O Centro vem depois.

> As áreas são **candidatas a estudo**, não obras aprovadas. O CityShield ajuda a escolher onde olhar primeiro.

## Resultados até agora

### O mapa bate com a realidade: três testes

Fizemos **a mesma conta** três vezes, com dados diferentes ([método e limitações](docs/validacao.md)). Em cada uma, os registros de cada rua são divididos pelo comprimento dela em cada faixa de risco e comparados com **todas as ruas da cidade** (12% delas estão no risco alto, 30% no alto ou médio).

| Teste | Dados | No risco **alto** | Vezes o acaso | Alto + médio | Carta oficial (qualquer classe) |
|---|---|---|---|---|---|
| **1. Registros da Defesa Civil, 2022–2023** | 223 registros em 75 ruas, cidade inteira | **74%** | **6,0×** | 88% | 45% |
| **2. Notícias de 2024–2026**, só vias novas | 49 eventos em 34 vias que não estavam nos relatórios | 34% | 2,7× | 55% | 15% |
| **3. Registros oficiais 2021–2026** (Bacia do Itanguá, via Lei de Acesso à Informação) | | | | | |
| ↳ **depois de o mapa ficar pronto** (8–12/11/2026) | 102 chamados em 11 ruas | 47% | 3,8× | **89%** | 33% |
| ↳ só vias novas | 106 registros em 35 vias | **72%** | **5,8×** | 82% | 18% |

- **O teste mais honesto é o 3.** O mapa ficou pronto em 07/11/2026. De 8 a 12 de novembro, uma chuva gerou 102 chamados à Defesa Civil, a maioria na Vila Mineirão: **89% caíram no risco alto ou médio; a carta oficial marcou 33%**. Os dados vieram da Prefeitura pelo pedido Fala.BR nº 03959.2026.000348-13 ([detalhes](docs/validacao.md#terceiro-teste-registros-oficiais-de-2021-a-2026)).
- **É associação, não previsão.** O mapa mostra onde o relevo favorece o acúmulo de água; ele coincide com onde alagou. Nenhum parâmetro foi ajustado para melhorar os números.
- **E o mapa oficial?** A carta de inundação do IPT e do Serviço Geológico (2015) marca 6% da cidade. Onde marca alta, acerta muito (24% dos registros em 2% das ruas, 15× o acaso), mas **55% dos registros ficam fora dela**. Os dois se completam: a carta é precisa nas várzeas largas; o relevo pega também os vales estreitos ([comparação](docs/validacao.md#comparação-com-a-carta-oficial)).
- **Cuidados:** o teste 3 cobre uma bacia só, e os chamados de depois do mapa vêm quase todos de uma chuva e de três ruas. Notícias mostram só o que virou notícia. Todos os limites estão em [docs/validacao.md](docs/validacao.md#limitações).

**Por que os totais mudam:** os relatórios de 2022–2023 têm **253 registros** em 89 ruas. **240** têm a rua localizada no mapa (os pontos que aparecem na plataforma). **223** tiveram o traçado da rua achado no OpenStreetMap e entram no teste 1.

### Onde agir no piloto

**48 áreas candidatas, somando 58 ha**, cada uma com uma solução recomendada e uma nota de prioridade ([regras](docs/recomendacoes.md)):

| Solução | Áreas | Quando é recomendada |
|---|---|---|
| Parque inundável | 4 | área verde de 1 ha ou mais, com metade ou mais no risco alto |
| Jardim de chuva | 31 | as outras áreas verdes |
| Piso permeável | 7 | estacionamentos abertos |
| Telhado verde | 6 | telhados grandes |

As 35 áreas verdes (parques + jardins) somam 53,6 ha; é esse recorte que a plataforma mostra no resumo do Diagnóstico. Os três maiores parques junto ao rio (Porto das Águas, Parque das Águas do Abaeté e Parque Linear do Rio Sorocaba, ~44 ha) estão inteiros no risco alto.

**Quanta água seguram:** numa chuva de 50 mm (como a de 16/10/2026), as soluções do piloto retêm cerca de **44%** da água que chega a elas, e os quatro parques têm, juntos, capacidade para guardar cerca de **131 mil m³**. São estimativas com valores publicados, cada um com a fonte, para comparar opções. **Não é uma simulação do caminho da água na cidade nem projeto de obra.**

## Para quem

- **Usa:** Defesa Civil de Sorocaba, secretarias de Meio Ambiente e de Obras/Planejamento, Câmara de Vereadores. Quem decide onde investir.
- **Se beneficia:** os moradores das ruas que alagam todo ano.
- **Também pode usar:** universidades, ONGs ambientais e imprensa.

Detalhes em [D13](docs/decisoes.md#d13-público-quem-decide-onde-investir-contra-enchentes).

## Como funciona

O cálculo pesado roda uma vez no pipeline. O site só mostra o resultado, por isso é rápido e funciona em hospedagem gratuita.

```
Fontes: relevo ANADEM 30 m · OpenStreetMap · registros da Defesa Civil · carta IPT/SGB · notícias
        │
        ▼
pipeline/  (Python: rasterio, pysheds, shapely, pyproj)
  relevo → HAND e córregos → validação (3 testes + carta oficial)
         → áreas candidatas → solução, nota e volumes → sensibilidade da nota
        │
        ├──► camadas GeoJSON ──► plataforma (MapLibre, GitHub Pages)
        └──► PostGIS (Neon) ──► api/ (FastAPI, Render)
```

A plataforma lê os arquivos GeoJSON publicados; se a API sair do ar, o site continua funcionando ([D10](docs/decisoes.md#d10-plano-b-geojson-estático)). A API serve as mesmas camadas para quem quiser integrar: `/camadas/risco`, `/camadas/registros`, `/areas`, `/areas/{id}` e `/cenario` ([documentação ao vivo](https://cityshield-s2lq.onrender.com/docs); no plano gratuito, a primeira chamada pode demorar enquanto o servidor acorda).

| Pasta | O que tem |
|---|---|
| `pipeline/` | Os passos que geram as camadas: `relevo`, `hand`, `validacao`, `carta`, `noticias`, `lai`, `areas`, `recomendacoes`, `sensibilidade` |
| `docs/` | Plataforma e página pública (GitHub Pages), dados publicados e documentação |
| `api/` | API FastAPI: camadas, áreas, ficha de cada área e cenário de chuva |
| `db/` | Tabelas do PostGIS (`db/init/`) e a carga dos arquivos do pipeline no banco |
| `web/` | Saída do pipeline (`web/public/dados/`); o site fica em `docs/`, em HTML puro ([D14](docs/decisoes.md#d14-site-em-html-css-e-javascript-puros-sem-react)) |

As decisões de projeto e o porquê de cada uma estão em [docs/decisoes.md](docs/decisoes.md).

## Como rodar

Requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env                           # e troque a senha
docker compose run --rm pipeline               # roda o pipeline inteiro (~3 min na 1ª vez)
docker compose up                              # sobe PostGIS + API em http://localhost:8000/docs
```

Cada passo também roda sozinho: `docker compose run --rm pipeline python -m pipeline hand` (ou qualquer outro da lista acima, como `validacao` ou `lai`). Para ver a plataforma localmente: `python -m http.server 8765` dentro de `docs/` e abrir `http://localhost:8765/mapa.html`.

O pipeline é reproduzível: rodando do zero num clone limpo, gera exatamente os mesmos arquivos que estão no repositório.

**Testes automáticos:** a cada PR, o [CI](https://github.com/habeas-code/cityshield/actions/workflows/ci.yml) confere o padrão do time (e bloqueia dados privados), roda o lint, os testes da API, da carga e das contas do pipeline, abre o site num navegador de verdade (Playwright, no computador e no celular) e testa a carga e a API contra um PostGIS de verdade.

## Dados, fontes e privacidade

| Dado | Fonte | Licença / uso |
|---|---|---|
| Relevo (modelo de terreno, 30 m) | ANADEM v1, [Laipelt et al., 2024](https://doi.org/10.3390/rs16132321) | download público (UFRGS/ANA); citar o artigo |
| Método HAND e faixas de risco | [Nobre et al., 2011](https://doi.org/10.1016/j.jhydrol.2011.03.051) | artigo científico |
| Ruas, parques, estacionamentos, prédios | OpenStreetMap | ODbL |
| Ocorrências de alagamento 2022–2023 | Defesa Civil de Sorocaba (relatórios anexos ao TCC de M. C. Vargem, Unesp, 2024) | agregados por rua |
| Ocorrências 2021–2026, Bacia do Itanguá | Defesa Civil de Sorocaba, pedido pela Lei de Acesso à Informação (Fala.BR nº 03959.2026.000348-13, 16/11/2026) | agregados por rua, bairro e data |
| Carta de suscetibilidade a inundações | IPT e Serviço Geológico do Brasil, 2015 | usada só para comparação; só os números são publicados |
| Notícias de alagamento 2024–2026 | G1, Cruzeiro do Sul, Agência de Notícias da Prefeitura e outros | só data, via, veículo e link ([lista](docs/dados/noticias.csv)) |
| Chuva de projeto (tempo de retorno) | Plano Diretor de Macrodrenagem, SAAE Sorocaba, 2025 | equação publicada |
| Fotos das soluções | Wikimedia Commons | ver [créditos](docs/img/CREDITOS.md) |

**Baixar os dados:** na plataforma, aba **Sobre → Baixar os dados**, ou direto em [`docs/dados/`](docs/dados/). São arquivos GeoJSON que abrem no QGIS e no ArcGIS. O que significa cada campo das áreas está em [`docs/recomendacoes.md`](docs/recomendacoes.md#o-que-o-arquivo-traz).

**Privacidade:** os relatórios e a planilha da Defesa Civil têm endereços de pessoas. Ele fica só na pasta `dados_privados/`, que **nunca vai para o GitHub** (está no `.gitignore` e o CI bloqueia). O repositório e o site usam apenas dados **agregados por rua**.

## Time Habeas Code

De Sorocaba/SP.

| Pessoa | Frente |
|---|---|
| Lucas | Mapas e dados, Site · líder do time |
| Enzo | Produto e apresentação · dados, fontes e Defesa Civil |
| Nicollas | Produto e apresentação · textos e vídeo |
| Rafael | Backend (API e banco) · advogado, consultoria jurídica |

Como trabalhamos: [CONTRIBUTING.md](CONTRIBUTING.md) (padrão de commits, revisão cruzada, reuniões) e [quadro de tarefas](https://github.com/orgs/habeas-code/projects/1).

## Licença

Código sob [MIT](LICENSE). Os dados de terceiros seguem as licenças de cada fonte (tabela acima).
