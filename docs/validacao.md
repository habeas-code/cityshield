# Validação do mapa de risco

**Pergunta:** os lugares que de fato alagaram em Sorocaba caem nas áreas que o CityShield marca como risco?

**Resposta curta:** sim. **74% dos registros da Defesa Civil caem no risco alto, que reúne só 12% das ruas da cidade**: seis vezes mais do que se os alagamentos caíssem ao acaso.

Para refazer: `docker compose run --rm pipeline python -m pipeline validacao`. O resultado completo, rua por rua, fica em `web/public/dados/validacao.json`.

## Resultado

### Cidade inteira

| Faixa de risco (HAND) | Registros da Defesa Civil | Ruas da cidade | Vezes o acaso |
|---|---|---|---|
| **Alto** (0–5 m) | **74%** | 12% | **6,0×** |
| Médio (5–15 m) | 15% | 18% | |
| Baixo (> 15 m) | 12% | 70% | |
| **Alto + médio** | **88%** | 30% | **2,9×** |

Dos 253 registros transcritos dos relatórios (89 ruas), 240 (79 ruas) têm a rua localizada no mapa público (`docs/dados/ruas.geojson`). Destes, 223 (75 ruas) foram encontrados no OpenStreetMap e entram no teste.

### Área piloto (núcleo Norte, raio de 800 m)

| Faixa | Registros | Ruas do piloto |
|---|---|---|
| Alto | 78% | 61% |
| Médio | 10% | 28% |
| Baixo | 12% | 12% |

Dentro do piloto, a maior parte das ruas já é de risco alto: a área inteira está na várzea do Rio Sorocaba. Por isso a vantagem sobre o acaso ali é pequena (1,3×), e é também por isso que ela foi escolhida como piloto ([D3](decisoes.md#d3-área-piloto-núcleo-norte-raio-de-800-m)). O teste que mostra se o método funciona é o da cidade inteira.

## Como foi feito

1. **Registros.** Relatórios da Defesa Civil de Sorocaba de 2022–2023, transcritos e **agrupados por rua** (`docs/dados/ruas.geojson`). Nenhum endereço com número entra no projeto ([D4](decisoes.md#d4-registros-tratados-por-rua-nunca-por-endereço)).
2. **Traçado das ruas.** Cada rua foi localizada no OpenStreetMap pelo nome. Quando o nome existe em vários bairros, ficam só os trechos a até 3 km do ponto já geocodificado. Quando a grafia muda ("XV de Agosto" e "15 de Agosto", "Mota" e "Motta", "Afonso Vergueiro" e "Doutor Afonso Vergueiro"), aceitamos o nome parecido só a até 1,5 km do ponto. Cada par usado aparece no campo `nome_osm` do resultado, para conferência.
3. **Faixa de cada trecho.** A rua é amostrada a cada 10 m e cada ponto recebe a faixa do HAND.
4. **Divisão dos registros.** O relatório diz a rua, não o ponto exato. Por isso os registros de cada rua são divididos entre as faixas **na proporção do comprimento da rua** em cada uma. Exemplo: uma rua com 10 registros e 70% do comprimento no risco alto conta 7 registros no alto.
5. **Comparação justa.** A mesma conta é feita para **todas as ruas do município** (vias urbanas do OpenStreetMap). Comparar com a área da cidade inflaria o resultado, porque as ruas tendem a seguir os vales. "Vezes o acaso" = fração dos registros na faixa ÷ fração das ruas na faixa.

**Conferência por outro caminho:** usando só o ponto central de cada rua (a prévia da tarefa #8), 74% dos registros também caem no risco alto.

## Segundo teste: notícias de 2024 a 2026

O teste acima usa registros de 2022–2023. Para ver se o mapa acerta **em anos que ele não viu**, juntamos as ruas que a imprensa noticiou como alagadas em Sorocaba de **2024 a 2026** e fizemos **a mesma conta**. Para refazer: `docker compose run --rm pipeline python -m pipeline noticias`. Resultado em `noticias.json`.

| Grupo de vias | Vias | Registros | No risco **alto** | Ruas da cidade no alto | Vezes o acaso | Alto + médio (30% das ruas) |
|---|---|---|---|---|---|---|
| Todas as vias noticiadas | 57 | 130 | **61%** | 12% | **5,0×** | 76% |
| **Só as novas** (fora dos relatórios de 2022–2023) | 34 | 49 | **34%** | 12% | **2,7×** | 55% |
| Só as que já estavam nos relatórios | 23 | 81 | 78% | 12% | 6,3× | 88% |

- **O grupo que importa é o das vias novas.** O mapa nunca as viu, e elas caem no risco alto 2,7 vezes mais do que se os alagamentos caíssem ao acaso. Somando alto e médio, são 55% dos registros em 30% das ruas.
- **Os mesmos lugares continuam alagando.** As vias com mais eventos são a Av. Dom Aguirre (16 dos 23 eventos), a Av. XV de Agosto (11), a Av. Juvenal de Campos (7), a Av. Afonso Vergueiro, o Parque das Águas e a Praça da Bandeira (6 cada). Todas já estavam nos relatórios da Defesa Civil.
- **Carta oficial, mesmas vias novas:** classe alta com 12% dos registros em 2% das ruas (7,3×), mas **85% dos registros ficam fora de qualquer classe da carta**. É o mesmo padrão da comparação abaixo: a carta é mais precisa onde marca, e marca pouco.
- **Onde o mapa erra.** Algumas vias noticiadas ficam fora das faixas alta e média, como a Av. Dr. Armando Pannunzio, a Av. General Carneiro, a R. Ministro Salgado Filho e a R. da Penha. São trechos em terreno mais alto, onde o alagamento vem da rede de drenagem (bueiro, enxurrada) e não do transbordamento de um córrego. O HAND mede a altura sobre o córrego mais próximo e não enxerga esse tipo de alagamento.

### Como foi feito

1. **Busca.** Buscamos notícias com a ferramenta Firecrawl (Search), com termos como "alagamento Sorocaba 2024" e "Rio Sorocaba transborda", de 2024, 2025 e 2026. Saíram 99 links. Tiramos sites de alerta e páginas sem relação e lemos 85 (dois deram erro).
2. **Leitura.** O Firecrawl (Scrape, extração em JSON) leu cada notícia e devolveu a data do evento e as vias de Sorocaba citadas como alagadas, inundadas ou interditadas por água. Queda de árvore, granizo e outras cidades ficam de fora. Das 83 notícias lidas, 68 são de 2024–2026 e falam de alagamento em Sorocaba.
3. **Limpeza.** Grafias diferentes da mesma via viram um nome só ("XV de Agosto", "Quinze de Agosto" e "15 de Agosto"). Ficam de fora bairros, hospitais, córregos, nomes genéricos ("ruas e avenidas") e vias que não existem no OpenStreetMap com esse nome. A coluna `como_na_noticia` mostra o nome original de cada linha, para conferência.
4. **Um registro por via e por chuva.** A mesma chuva noticiada por cinco veículos conta uma vez. Datas a até 2 dias uma da outra são o mesmo evento. Ficaram **23 eventos**, de janeiro de 2024 a novembro de 2026.
5. **Mesma conta da validação.** Cada via recebe um ponto aproximado: o mesmo das ruas da Defesa Civil quando ela já estava lá, ou o do Nominatim (OpenStreetMap). Depois a conta segue os passos 2 a 5 acima.

**Nada do texto das notícias entra no projeto.** `docs/dados/noticias.csv` guarda só a data, a via, o veículo e o link de cada citação.

**Cuidado ao ler:** notícia mostra só o que virou notícia. Avenidas grandes e o Centro aparecem mais do que ruas de bairro. Por isso este é um **segundo teste**, não uma prova. O registro oficial completo de 2024–2026 continua pedido (tarefa #13).

## Comparação com a carta oficial

Sorocaba já tem um mapa oficial: a **carta de suscetibilidade a inundações** do IPT e do Serviço Geológico do Brasil (2015, escala 1:25.000, [repositório do SGB](https://rigeo.sgb.gov.br/items/cb9a8ac7-dda7-45e0-9dbe-7e8664b6b665)). Fizemos com ela **exatamente o mesmo teste** (mesmas ruas, mesma divisão dos registros, mesma comparação com todas as ruas). Para refazer: `docker compose run --rm pipeline python -m pipeline carta`. Resultado em `comparacao_carta.json`.

| Mapa | Área do município marcada | Registros da Defesa Civil | Ruas da cidade | Vezes o acaso |
|---|---|---|---|---|
| Carta oficial, classe **alta** | 3% | 24% | 2% | 15× |
| Carta oficial, alta + média + baixa | 6% | 45% | 4% | 12× |
| CityShield, risco **alto** (HAND 0–5 m) | 18% | **74%** | 12% | 6× |
| CityShield, alto + médio | 36% | 88% | 30% | 2,9× |

- **A carta é mais precisa; o CityShield é mais completo.** Onde a carta marca, a chance de ter registro é maior (15×), mas ela marca pouco: **55% dos registros ficam fora de qualquer classe dela**. O nosso risco alto reúne 74%.
- **Por quê:** a carta foi feita para inundação de rio em várzea. A revisão do Plano Diretor de Macrodrenagem (SAAE, 2025) diz que ela tem mais precisão "em planícies aluviais bem definidas" e não contempla bem os **vales estreitos**, comuns na zona urbana. Os registros da Defesa Civil também incluem alagamento por drenagem nesses vales. O HAND mede a altura sobre qualquer córrego, grande ou pequeno.
- **Os dois se completam.** Para escolher onde agir, a carta diz onde o rio transborda com certeza; o CityShield acrescenta os fundos de vale que também alagam.
- **Só a camada de inundação foi lida.** O passo `carta` lê, de dentro do pacote SIG do SGB (199 MB), só os quatro arquivos dela (~0,9 MB, por partes). A geometria da carta não vai para o repositório nem para o site; publicamos só os números.

## Limitações

- **Ruas, não pontos.** Uma avenida longa como a Dom Aguirre (12,9 km no mapa) recebe os registros distribuídos ao longo dela toda. É uma aproximação.
- **Quatro ruas ficaram de fora** (17 registros): Rua Projetada II (Guadalupe), Rua Três e Rua Nove (Itapemirim) e Rua Láurico. Não existem no OpenStreetMap com esse nome perto do lugar indicado, e preferimos deixá-las de fora a adivinhar.
- **Registros dependem de quem registra.** Lugares onde alaga mas ninguém chama a Defesa Civil não aparecem. O teste mede se o mapa acerta onde **houve registro**, não onde **não alaga**.
- **Dois anos de registros oficiais** (2022–2023). Os relatórios de 2024–2026 foram pedidos (tarefa #13). Enquanto não chegam, o [segundo teste](#segundo-teste-notícias-de-2024-a-2026) usa notícias desses anos.
- **Alagamento por drenagem.** O HAND mede a altura sobre os córregos. Alagamento de bueiro em terreno alto, como o de algumas vias do segundo teste, fica fora do risco alto.
- **Limiar fixo.** O córrego começa em 0,5 km² drenados e as faixas seguem Nobre et al. (2011). Esses valores **não foram ajustados** para melhorar este resultado.

## Fontes

- Defesa Civil de Sorocaba: relatórios de ocorrências 2022–2023 (anexo do TCC de M. C. Vargem, Unesp, 2024).
- OpenStreetMap (ODbL), via Overpass API.
- Notícias de 2024–2026 (G1, Jornal Cruzeiro do Sul, Agência de Notícias da Prefeitura, Band, TV Sorocaba, Jornal Z Norte, Portal Porque e outros): lista completa, com links, em `docs/dados/noticias.csv`. Busca e leitura com Firecrawl; pontos das vias novas pelo Nominatim (OpenStreetMap).
- HAND: Nobre, A. D. et al. (2011). *Height Above the Nearest Drainage – a hydrologically relevant new terrain model*. Journal of Hydrology 404, 13–29. https://doi.org/10.1016/j.jhydrol.2011.03.051
- Relevo: ANADEM v1, Laipelt et al. (2024). https://doi.org/10.3390/rs16132321
- Carta oficial: Instituto de Pesquisas Tecnológicas (IPT) e CPRM/Serviço Geológico do Brasil (2015). *Carta de suscetibilidade a movimentos gravitacionais de massa e inundações: município de Sorocaba - SP*. https://rigeo.sgb.gov.br/items/cb9a8ac7-dda7-45e0-9dbe-7e8664b6b665
