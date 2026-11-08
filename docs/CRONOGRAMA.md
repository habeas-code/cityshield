# Cronograma até a entrega

Fase online do Hack Brasil: **até 30/11 (seg), às 23h59**. Nossa meta é entregar **um dia antes**, em 29/11, para ter folga se algo quebrar.

O time trabalha meio período (estágio e faculdade), então cada semana tem **uma meta só**. O que não couber vai para a lista "se sobrar tempo", no fim desta página.

## Visão geral

| Semana | Datas | Meta | Pronto quando |
|---|---|---|---|
| 0 | 07–08/11 | Rascunho enviado | vídeo gravado, rascunho enviado no painel, frentes divididas |
| 1 | 09–15/11 | **Mapa de risco real** | o mapa mostra o HAND da área piloto e o "X% dos registros" calculado |
| 2 | 16–22/11 | **Recomendações** | cada área candidata tem solução, nota de prioridade e volume retido, com fonte |
| 3 | 23–29/11 | **No ar e entregue** | site público com dados reais, vídeo final gravado, submissão feita |

## Semana 0: rascunho (07–08/11)

- [ ] Roteiro do vídeo com os nomes de cada um
- [ ] Gravar o vídeo (≤ 3 min, os 4 aparecendo) e subir no YouTube como não listado
- [ ] Enviar o rascunho no painel (trilha Meio Ambiente + repo + página + vídeo)
- [ ] Definir quem fica com cada frente e atualizar o `CONTRIBUTING.md`
- [ ] Combinar dia e horário fixos da reunião semanal

## Semana 1: mapa de risco real (09–15/11)

| Frente | Entregas |
|---|---|
| Mapas e dados | baixar o relevo ANADEM 30 m da área piloto; calcular o HAND; rede de drenagem; validação: % dos registros nas faixas de risco alto e médio (piloto e cidade) |
| Backend | **Rafael:** carregar no PostGIS as camadas de risco e os registros por rua (#10); endpoints `/camadas/risco` e `/camadas/registros` (#11); CORS e `/saude` testando o banco (#56) |
| Site | projeto React + Vite + MapLibre rodando, mostrando as camadas da API (ou do GeoJSON do plano B) |
| Produto | **Enzo:** pedir à Defesa Civil os relatórios de 2024–2026 (protocolo de pesquisa acadêmica) (#13). **Nicollas:** revisar textos de risco com linguagem simples (#14) |

**Revisão de fim de semana (15/11):** o número "X% dos registros caem em risco alto/médio" existe e está certo?

## Semana 2: recomendações (16–22/11)

| Frente | Entregas |
|---|---|
| Mapas e dados | áreas candidatas do OSM (estacionamentos, praças, telhados grandes) no raio de 800 m; regra de qual solução cabe em cada área; nota = risco × registros × área; volume retido com as fontes já escolhidas |
| Backend | **Rafael:** endpoints `/areas`, `/areas/{id}` (ficha) e `/cenario` (antes/depois para uma chuva escolhida) (#18); preparar o deploy (#23) |
| Site | ficha da área ao clicar; painel antes/depois; lista ordenada por nota |
| Produto | **Enzo:** conferir cada número com a fonte e ligar ao PL Cidade-Esponja, com consultoria do Rafael (#21). **Nicollas:** rascunho do roteiro do vídeo final (#22) |

**Revisão de fim de semana (22/11):** dá para abrir o site, clicar numa área e entender o que fazer ali e por quê?

## Semana 3: no ar e entregue (23–29/11)

| Dia | O quê |
|---|---|
| 23–25/11 | deploy (Rafael, #23): banco no Neon e API no Render (o site segue no GitHub Pages); plano B com GeoJSON estático (Lucas, #24); testar no celular |
| 26/11 | **congelar funcionalidades**: daqui em diante, só correção de bug e texto |
| 27/11 | gravar o vídeo final (Nicollas, #25) (≤ 3 min, produto funcionando, de preferência em inglês) |
| 28/11 | README final (Enzo, #26), conferir licença, links e créditos das imagens |
| 29/11 | **enviar a submissão** |
| 30/11 | folga para emergência (prazo às 23h59) |

## Depois da entrega

| Data | O quê |
|---|---|
| 02/12 | finalistas anunciados |
| até 04/12, 23h59 | confirmar presença na final |
| 12/12 | final presencial no Google for Startups, em São Paulo (os 4 juntos) |

## Datas do evento para não esquecer

- Lives opcionais: 09, 16, 23 e 27/11
- A demo precisa continuar no ar durante a avaliação

## Se sobrar tempo

- Segunda área: núcleo Centro (Lions, Bandeira, Afonso Vergueiro)
- Moradores afetados por área (Censo 2022, IBGE)
- Registros de 2024–2026, se a Defesa Civil responder a tempo
- Versão do site em inglês
