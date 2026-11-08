# Registro de decisões

Aqui ficam as escolhas importantes do projeto e **por que** foram feitas. Quando alguém (ou o júri) perguntar "por que vocês fizeram assim?", a resposta está aqui.

Cada decisão nova entra no fim, com número, data e as alternativas que consideramos. Se uma decisão mudar, não apague: marque como **substituída** e aponte para a nova.

---

## D1. Trilha Meio Ambiente, foco só em enchentes

**Data:** 05/11/2026

**Decisão:** concorrer na trilha **Meio Ambiente** com um problema só: alagamentos e inundações em Sorocaba.

**Por quê:** enchente é um problema ambiental e urbano com dado público disponível (Defesa Civil, relevo, OpenStreetMap) e impacto fácil de entender. Com um problema só, dá para entregar algo funcionando em 4 semanas.

**Alternativas:** cobrir vários riscos (deslizamento, calor). Ficou de fora porque espalharia o pouco tempo do time. Não existe trilha GovTech no Hack Brasil; o lado público entra como componente dentro da trilha.

## D2. Recomendar soluções verdes, não só mostrar risco

**Data:** 05/11/2026

**Decisão:** a função principal é indicar **onde** e **qual** solução baseada na natureza estudar (jardim de chuva, piso permeável, parque inundável, telhado verde).

**Por quê:** Sorocaba já tem mapa de risco (carta de suscetibilidade do Serviço Geológico, 2014). Mostrar risco de novo não acrescenta. O que falta é sair do "aqui alaga" para o "aqui dá para fazer isso". Também conversa com o PL Cidade-Esponja apresentado na Câmara em 19/11/2024.

## D3. Área piloto: núcleo Norte, raio de 800 m

**Data:** 06/11/2026

**Decisão:** começar pelo núcleo Norte (Parque das Águas, Jd. Maria do Carmo, Abaeté), num raio de 800 m. O Centro é a segunda etapa.

**Por quê:** nos relatórios da Defesa Civil de 2022–2023, o núcleo Norte concentra **41 registros** no raio de 800 m, contra 27 no núcleo Centro. Também tem área livre para soluções (praças, estacionamentos, o próprio parque).

**Alternativas:** corredor Dom Aguirre/Centro (mais registros espalhados, menos área livre); Itapemirim.

## D4. Registros tratados por rua, nunca por endereço

**Data:** 05/11/2026

**Decisão:** os registros da Defesa Civil entram no projeto **agrupados por rua**. Os endereços com número de casa ficam em `dados_privados/`, fora do repositório, e nunca vão para o site.

**Por quê:** privacidade (LGPD) e honestidade com o dado. O relatório informa a rua, não o ponto exato do alagamento, então o mapa mostra **concentração por rua**.

## D5. Relevo ANADEM em vez do Copernicus puro

**Data:** 06/11/2026

**Decisão:** usar o **ANADEM** (30 m) como base de relevo.

**Por quê:** o Copernicus GLO-30 é um modelo de **superfície**: mede o topo de prédios e árvores. Para saber para onde a água escorre, precisamos do **terreno**. O ANADEM é o Copernicus corrigido para tirar a vegetação, feito para a América do Sul (Laipelt et al., 2024).

## D6. Risco calculado pelo método HAND

**Data:** 06/11/2026

**Decisão:** medir o risco pela **HAND** (*Height Above Nearest Drainage*): a altura de cada ponto acima do córrego mais próximo.

**Por quê:** é um método conhecido, simples de explicar ("quanto mais perto da altura do córrego, mais alaga") e que roda com dado aberto. E dá para testar: conferimos que porcentagem dos registros reais caiu nas faixas de risco alto e médio.

## D7. Cálculo pesado roda antes; o site só mostra o resultado

**Data:** 06/11/2026

**Decisão:** um pipeline em Python calcula tudo uma vez (relevo, HAND, áreas, notas, volumes) e grava no banco. A API e o site só leem.

**Por quê:** o cálculo não muda a cada visita. Assim o site fica rápido, a hospedagem gratuita aguenta e não precisamos de filas nem de servidores de processamento.

## D8. FastAPI no backend

**Data:** 06/11/2026

**Decisão:** API em **FastAPI** com SQLAlchemy 2 + GeoAlchemy2 sobre **PostGIS**.

**Por quê:** a API só entrega camadas em GeoJSON e algumas fichas. FastAPI é leve para isso, gera a documentação sozinho (`/docs`) e é Python, igual ao pipeline. PostGIS faz as consultas espaciais (o que está na área visível do mapa).

**Alternativas:** Django + DRF. Bom para sistemas com painel administrativo e muitos cadastros, o que não é o nosso caso.

## D9. Sem login, sem Redis e sem Celery no MVP

**Data:** 06/11/2026

**Decisão:** o MVP não tem login nem fila de tarefas.

**Por quê:** o júri precisa abrir o site e usar na hora, sem cadastro. Como o cálculo pesado já roda antes (D7), não há tarefa demorada para colocar em fila. E um worker separado custa dinheiro na hospedagem.

**Pode voltar:** se o projeto continuar depois do hackathon (por exemplo, a Defesa Civil editando dados).

## D10. Plano B: GeoJSON estático

**Data:** 06/11/2026

**Decisão:** além da API, o pipeline gera os mesmos dados em arquivos GeoJSON que o site consegue ler sozinho.

**Por quê:** hospedagem gratuita dorme e pode cair durante a avaliação. Com o plano B, a demo continua funcionando.

## D11. Toda estimativa com fonte

**Data:** 06/11/2026

**Decisão:** os volumes de água retidos usam valores publicados, sempre citados junto do número:

| Solução | Valor | Fonte |
|---|---|---|
| Piso permeável | 50 mm de chuva | PMSP, ETS-03/2013 (brita 25 cm × 20% de vazios) |
| Jardim de chuva | 150 L/m² | Hinman, WSU, 2007 (lâmina de 15 cm) |
| Telhado verde | 47–62% retido | Vacari et al., 2019, UFMT |
| Parque inundável | volume calculado pelo relevo | ANADEM |

**Por quê:** o projeto é para apoiar decisão pública. Número sem fonte, ou inventado para impressionar, tira a confiança no resto.

## D12. Visual no padrão das ferramentas de mapa profissionais

**Data:** 06/11/2026

**Decisão:** a plataforma segue o estilo de CARTO, ArcGIS Living Atlas e Mapbox: mapa em destaque, camadas com legenda, painéis discretos. Fotos só com licença livre (Wikimedia Commons), com créditos em `docs/img/CREDITOS.md`.

**Por quê:** o público é técnico (Defesa Civil, prefeitura) e precisa confiar no que vê. E não podemos usar fotos sem direito de uso.

## D13. Público: quem decide onde investir contra enchentes

**Data:** 07/11/2026

**Decisão:** o CityShield é feito para quem **decide onde investir**. Quem mais se beneficia são os **moradores** das ruas que alagam.

| Grupo | Quem | Para quê |
|---|---|---|
| **Usa (principal)** | Defesa Civil de Sorocaba | apontar onde agir antes da próxima chuva, com base nos próprios registros |
| | Prefeitura: secretarias de Meio Ambiente e de Obras/Planejamento | priorizar onde estudar cada solução verde, com pouco orçamento |
| | Câmara de Vereadores | mostrar por onde começar se o PL Cidade-Esponja (2024) avançar |
| **Se beneficia** | Moradores das ruas que alagam (Parque das Águas, Dom Aguirre, XV de Agosto...) e associações de bairro | entender o risco da sua rua e cobrar ação com dado na mão |
| **Também pode usar** | Universidades, ONGs ambientais, imprensa local | pesquisa, fiscalização, reportagem |

**Em uma frase (pitch):** "O CityShield é para quem decide onde investir contra enchentes em Sorocaba, a Defesa Civil e a prefeitura, e beneficia diretamente os moradores das ruas que alagam todo ano."

**Por quê:** solução verde é obra pública. Quem pode transformar a recomendação em jardim de chuva ou parque inundável é o poder público, então a ferramenta precisa falar a língua de quem decide: risco, prioridade, área e volume, sempre com fonte.

**Consequências:** explica o visual técnico (D12), a falta de login (D9: ferramenta pública, aberta a qualquer um) e a exigência de fonte em todo número (D11).

## D14. Site em HTML, CSS e JavaScript puros, sem React

**Data:** 08/11/2026

**Decisão:** o site continua como está: páginas em HTML, CSS e JavaScript puros (`docs/index.html`, `docs/mapa.html`, `docs/comum.js`), publicadas direto pelo GitHub Pages, com o MapLibre guardado em `docs/vendor/`. A migração para React + Vite (#12) foi cancelada.

**Por quê:**

- O site já funciona e está publicado, com mapa de risco, validação, áreas com recomendação, popup explicado e painel antes/depois. Refazer em React levaria dias só para voltar ao mesmo ponto, perto do congelamento de 26/11.
- Sem etapa de build, tem menos coisa para quebrar na entrega: o que está no repositório é o que está no ar.
- O júri avalia se funciona, se está completo e como foi construído. Um site leve, sem dependências, que abre rápido no celular atende melhor a isso do que trocar de biblioteca.
- O MapLibre é o mesmo nos dois casos: o mapa, que é a parte principal, não muda.

**Alternativas:** React + Vite + TypeScript + TanStack Query, o plano original da #12. Bom para sites grandes com muito estado; o nosso tem duas páginas e um mapa.

**Consequências:** a pasta `web/` guarda só a saída do pipeline (`web/public/dados/`). O site lê os arquivos de `docs/dados/` e, quando a API estiver no ar, passa a ler dela com plano B para os arquivos (#24, D10).

**Pode voltar:** se o projeto continuar depois do hackathon e o site crescer (login, edição de dados), React volta a fazer sentido.
