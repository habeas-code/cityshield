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
> **Working today:** flood risk computed from the terrain for the whole city (HAND method on the ANADEM 30 m terrain model) and tested against reality: **74% of the Civil Defense records fall in the high-risk zones, which hold only 12% of the city's streets (6× chance)**. In 2026, the two streets with most records flooded again, both mapped as high risk. The map also shows 48 candidate sites (parks, parking lots, large roofs) in the pilot area. **Next:** a recommended solution and priority score per site, and how much water each could retain, always with a source.
>
> **For:** Civil Defense and city departments deciding where to invest; it directly benefits residents of streets that flood every year. **Stack:** Python pipeline (rasterio, pysheds, shapely) → PostGIS → FastAPI; map with MapLibre. Team docs are in Portuguese.

---

## O problema

Sorocaba (SP) alaga todo verão, e quase sempre nos mesmos lugares. Os relatórios da Defesa Civil de 2022 e 2023 registram **mais de 250 ocorrências de alagamento e inundação em 89 ruas**. A **Av. Dom Aguirre** aparece 23 vezes; a **Av. XV de Agosto** está em 10 dos 15 relatórios. Em 20/01/2024, a água arrastou um carro até a Av. Juvenal de Campos. E continua: em **2026**, a XV de Agosto foi interditada por alagamento em setembro e em outubro, e a Dom Aguirre em outubro.

A cidade já discute soluções baseadas na natureza (a "cidade-esponja"): jardins de chuva, piso permeável, telhados verdes, parques que podem alagar. Há até um projeto de lei sobre isso na Câmara (2024). Mas falta responder uma pergunta prática: **em qual terreno vale a pena estudar qual solução primeiro?**

Sorocaba já tem mapa de suscetibilidade a inundação (Serviço Geológico, 2014). Ele mostra **onde** é perigoso, mas não diz **o que fazer** em cada lugar. É essa lacuna que o CityShield ocupa.

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

**O mapa acerta.** Testamos o risco calculado contra os registros da Defesa Civil de 2022–2023 ([método e limitações](docs/validacao.md)):

| Faixa de risco | Registros da Defesa Civil | Ruas da cidade | |
|---|---|---|---|
| **Alto** (até 5 m acima do córrego) | **74%** | 12% | **6× o acaso** |
| Alto + médio (até 15 m) | 88% | 30% | 2,9× o acaso |

- A comparação é com **todas as ruas da cidade**, não com a área total, para não inflar o resultado (ruas tendem a ficar nos vales).
- Nenhum parâmetro foi ajustado para melhorar o número.
- **Eventos de 2026, que o mapa nunca viu:** as avenidas interditadas por alagamento em setembro e outubro (XV de Agosto e Dom Aguirre) estão 90% e 99,8% no risco alto.

**Onde agir no piloto:** 48 áreas candidatas, somando 58 ha. Os três maiores parques junto ao rio (Porto das Águas, Parque das Águas do Abaeté e Parque Linear do Rio Sorocaba, ~44 ha) estão inteiros no risco alto: candidatos naturais a **parque inundável**.

## Para quem

- **Usa:** Defesa Civil de Sorocaba, secretarias de Meio Ambiente e de Obras/Planejamento, Câmara de Vereadores. Quem decide onde investir.
- **Se beneficia:** os moradores das ruas que alagam todo ano.
- **Também pode usar:** universidades, ONGs ambientais e imprensa.

Detalhes em [D13](docs/decisoes.md#d13-público-quem-decide-onde-investir-contra-enchentes).

## Como funciona

O cálculo pesado roda uma vez no pipeline. O site só mostra o resultado, por isso é rápido e funciona em hospedagem gratuita.

```
Fontes: relevo ANADEM 30 m · OpenStreetMap · registros da Defesa Civil
        │
        ▼
pipeline/  (Python: rasterio, pysheds, shapely, pyproj)
  relevo → HAND e córregos → validação → áreas candidatas
        │
        ├──► camadas GeoJSON ──► plataforma (MapLibre, GitHub Pages)
        └──► PostGIS ──► api/ (FastAPI)     [em construção]
```

| Pasta | O que tem |
|---|---|
| `pipeline/` | Os passos que geram as camadas: `relevo`, `hand`, `validacao`, `areas` |
| `docs/` | Plataforma e página pública (GitHub Pages), dados publicados e documentação |
| `api/` | API FastAPI (hoje: `/saude`; camadas e fichas em construção) |
| `db/init/` | SQL rodado na primeira vez que o banco sobe (PostGIS) |
| `web/` | Saída do pipeline (`web/public/dados/`); o site em React vem depois |

As decisões de projeto e o porquê de cada uma estão em [docs/decisoes.md](docs/decisoes.md).

## Como rodar

Requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env                           # e troque a senha
docker compose run --rm pipeline               # roda o pipeline inteiro (~3 min na 1ª vez)
docker compose up                              # sobe PostGIS + API em http://localhost:8000/docs
```

Cada passo também roda sozinho: `docker compose run --rm pipeline python -m pipeline hand` (ou `relevo`, `validacao`, `areas`). Para ver a plataforma localmente: `python -m http.server 8765` dentro de `docs/` e abrir `http://localhost:8765/mapa.html`.

O pipeline é reproduzível: rodando do zero num clone limpo, gera exatamente os mesmos arquivos que estão no repositório.

## Dados, fontes e privacidade

| Dado | Fonte | Licença / uso |
|---|---|---|
| Relevo (modelo de terreno, 30 m) | ANADEM v1, [Laipelt et al., 2024](https://doi.org/10.3390/rs16132321) | download público (UFRGS/ANA); citar o artigo |
| Método HAND e faixas de risco | [Nobre et al., 2011](https://doi.org/10.1016/j.jhydrol.2011.03.051) | artigo científico |
| Ruas, parques, estacionamentos, prédios | OpenStreetMap | ODbL |
| Ocorrências de alagamento 2022–2023 | Defesa Civil de Sorocaba (relatórios anexos ao TCC de M. C. Vargem, Unesp, 2024) | agregados por rua |
| Fotos das soluções | Wikimedia Commons | ver [créditos](docs/img/CREDITOS.md) |

**Privacidade:** o relatório da Defesa Civil tem endereços de pessoas. Ele fica só na pasta `dados_privados/`, que **nunca vai para o GitHub** (está no `.gitignore` e o CI bloqueia). O repositório e o site usam apenas dados **agregados por rua**.

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
