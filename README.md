# CityShield

**Onde Sorocaba alaga e onde soluções verdes podem segurar essa água.**

Projeto do time **Habeas Code** para o [Hack Brasil 2026](https://hackbrasil.com), trilha **Meio ambiente**.

🌐 Página do projeto: https://habeas-code.github.io/cityshield/  
🗺️ Plataforma (protótipo): https://habeas-code.github.io/cityshield/mapa.html

---

## O problema

Sorocaba (SP) alaga todo verão, e quase sempre nos mesmos lugares. Os relatórios da Defesa Civil de 2022 e 2023 registram mais de 250 ocorrências de alagamento e inundação em 89 ruas. Algumas aparecem em quase todos os relatórios, como a Av. Dom Aguirre e a Rua XV de Agosto.

A cidade já discute soluções baseadas na natureza ("cidade-esponja"): jardins de chuva, piso permeável, telhados verdes, parques que podem alagar. Mas falta responder uma pergunta prática: **em qual terreno vale a pena estudar qual solução primeiro?**

## O que estamos construindo

Um mapa interativo para a Defesa Civil, a prefeitura e moradores que:

1. **Mostra o risco**: calcula, a partir do relevo, a altura de cada ponto em relação ao rio mais próximo (método HAND).
2. **Cruza com o histórico**: agrupa as ocorrências da Defesa Civil por rua (sem endereço exato de ninguém).
3. **Encontra áreas candidatas**: praças, estacionamentos, terrenos e telhados grandes do OpenStreetMap perto dos pontos críticos.
4. **Recomenda e estima**: sugere uma solução verde para cada área, dá uma nota de prioridade (risco × ocorrências × área disponível) e calcula quanto de água ela poderia reter numa chuva escolhida, sempre com a fonte do número.
5. **Testa o próprio método**: mostra que porcentagem das ocorrências reais caiu nas faixas de risco alto e médio.

**Piloto:** núcleo Norte (Parque das Águas, Jd. Maria do Carmo, Abaeté), raio de 800 m. O Centro vem depois.

> As áreas são **candidatas a estudo**, não obras aprovadas. O CityShield ajuda a escolher onde olhar primeiro.

## Arquitetura

O cálculo pesado roda uma vez no pipeline. O site só mostra o resultado.

```
Fontes (relevo ANADEM, OpenStreetMap, Defesa Civil, IBGE)
        │
        ▼
pipeline/ (Python: pysheds, GeoPandas, OSMnx)
        │
        ▼
PostGIS ──► api/ (FastAPI) ──► web/ (React + MapLibre)
        └──── GeoJSON estático (plano B, se a API cair) ──┘
```

| Pasta | O que tem |
|---|---|
| `pipeline/` | Scripts Python que geram as camadas (risco, áreas, notas, volumes, validação) |
| `api/` | API FastAPI: camadas, ficha da área, cenário antes/depois, fontes |
| `db/init/` | SQL rodado na primeira vez que o banco sobe (PostGIS) |
| `web/` | Site React + Vite + TypeScript + MapLibre |
| `docs/` | Página pública do projeto e documentação |

## Como rodar (local)

Requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env              # e troque a senha
docker compose up                 # sobe PostGIS + API
```

- API: http://localhost:8000/docs
- Pipeline (quando existir): `docker compose run --rm pipeline`

## Dados e privacidade

O relatório da Defesa Civil tem endereços de pessoas. Ele fica só na pasta `dados_privados/`, que **nunca vai para o GitHub** (está no `.gitignore`). O repositório e o site só usam dados agregados por rua.

## Status

🚧 Em construção (Hack Brasil 2026, de 04/11 a 30/11/2026).

## Time Habeas Code

Lucas, Enzo, Rafael e Nicollas, de Sorocaba/SP.

## Licença

[MIT](LICENSE)
