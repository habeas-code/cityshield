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

**Cuidado ao ler:** notícia mostra só o que virou notícia. Avenidas grandes e o Centro aparecem mais do que ruas de bairro. Por isso este é um **segundo teste**, não uma prova. Os registros oficiais de 2024–2026 chegaram depois, só da Bacia do Itanguá: veja o [terceiro teste](#terceiro-teste-registros-oficiais-de-2021-a-2026).

## Terceiro teste: registros oficiais de 2021 a 2026

Pedimos à Prefeitura, pela Lei de Acesso à Informação, os registros de alagamento, inundação e enxurrada de 2024 a 2026 (tarefa #13). A resposta chegou em **16/11/2026** (Fala.BR nº 03959.2026.000348-13, SEMOB / Coordenadoria Municipal de Proteção e Defesa Civil), com uma planilha **só da Bacia do Itanguá**: **365 registros, de agosto de 2021 a 12 de novembro de 2026** (296 deles de 2026). Fizemos **a mesma conta** da validação. Para refazer: `docker compose run --rm pipeline python -m pipeline lai`. Resultado em `lai_defesa_civil.json`.

**O teste mais limpo é o dos registros de depois de o mapa ficar pronto.** O mapa de risco e a validação foram juntados ao projeto em **07/11/2026**. De 8 a 12 de novembro, uma chuva forte gerou **102 registros** na bacia, a maioria na Vila Mineirão. O mapa não tinha como ter visto esses registros.

| Grupo | Vias | Registros | No risco **alto** (12% das ruas) | Vezes o acaso | Alto + médio (30% das ruas) | Carta oficial, qualquer classe (4% das ruas) |
|---|---|---|---|---|---|---|
| **Depois do mapa pronto** (8–12/11/2026) | 11 | 102 | **47%** | **3,8×** | **89%** | 33% |
| Todos (2021–2026) | 56 | 334 | 64% | 5,2× | 92% | 28% |
| Só 2024–2026 | 55 | 317 | 64% | 5,2× | 91% | 28% |
| **Só vias novas** (fora dos relatórios de 2022–2023) | 35 | 106 | **72%** | **5,8×** | 82% | 18% |

- **O mapa acertou o que veio depois.** Dos 102 registros de 8 a 12 de novembro, **89% caíram no risco alto ou médio**, faixas que reúnem 30% das ruas da cidade. A carta oficial marcou 33% deles; os outros 67% ficam fora de qualquer classe da carta.
- **Por que "alto ou médio" e não só "alto".** As ruas mais atingidas da Vila Mineirão (Antônio Furtado Lopes, Abner Pedroso de Alcântara, Pedro Lombardi) ficam metade no risco alto e metade no médio. Foi uma inundação grande, que subiu além da faixa mais baixa do vale. O risco médio (HAND de 5 a 15 m) existe para isso.
- **As vias novas confirmam o teste das notícias, com mais força.** Vias que não estavam nos relatórios de 2022–2023 caem no risco alto 5,8 vezes mais do que ao acaso (72% dos registros em 12% das ruas). Nas notícias, eram 2,7×; a diferença é que estes são registros oficiais de bairro, não só de avenidas que viram notícia.
- **A carta continua precisa onde marca, e marca pouco.** Na classe alta, 10% dos registros em 1,6% das ruas (6,3×). Mas 72% dos registros ficam fora de qualquer classe dela.

### Como foi feito

1. **Transcrição.** A planilha veio em PDF. Lemos as colunas pela posição de cada palavra na página e conferimos a contagem página por página. A última página repete os registros do Jardim Marli e ficou de fora.
2. **Limpeza.** Grafias diferentes da mesma via viram um nome só ("Dr Campos Salles" e "Doutor Campos Salles"; "Alfeu" e "Alpheu Castro Santos"), e o mesmo para os bairros ("Jd Marly", "MARLI, JD"). 13 registros vieram sem rua ("-", "vários endereços").
3. **Ponto de cada via.** A via é procurada pelo nome no OpenStreetMap; quando o nome existe em vários lugares da cidade (como "Rua Dois"), fica a mais perto do centro do bairro informado, até 2,5 km. Grafias diferentes no OpenStreetMap ("Jorge Bacelli", "Karim Jamal") são aceitas pela semelhança. Sem achar, tentamos o Nominatim (OpenStreetMap).
4. **Mesma conta da validação.** Cada chamado conta, como nos relatórios de 2022–2023, e os registros de uma via se dividem pela extensão dela em cada faixa de risco.

**Nenhum dado pessoal entra no projeto.** A planilha da Prefeitura traz o número da casa de cada chamado. `docs/dados/lai_defesa_civil.csv` guarda só a data, a via, o bairro, o tipo e o número de registros. A planilha original fica fora do repositório.

**Cuidado ao ler:**

- **Uma região só.** A planilha cobre o que a Defesa Civil chama de Bacia do Itanguá, não a cidade inteira. A comparação com as ruas da própria região está logo abaixo.
- **Um evento concentrado.** Os registros de depois do mapa vêm quase todos de uma chuva e de três ruas da Vila Mineirão. É um caso real e independente, mas não é uma amostra da cidade.
- **Um chamado por casa.** Uma rua com muitas casas atingidas soma muitos registros. Isso pesa a favor das ruas com mais moradores na várzea.
- **25 registros de fora:** 13 sem rua, 12 em vielas do Jardim Itapemirim (Viela 203, Viela 148 e outras) e uma "Rua 2" sem bairro, que não existem com esse nome no OpenStreetMap. Mais três vias com ponto (duas "Rua 2" e a Rua Três do Itapemirim, 6 registros) não foram achadas pela conta da validação.

### Comparação local: o teste mais duro

**A pergunta:** os registros vêm de uma região de vale. Uma região assim tem mais ruas baixas que a média da cidade. Comparar com as ruas da **cidade inteira** pode inflar o resultado. E se a comparação for só com as ruas **da própria região**?

**Primeiro achado: a "Bacia do Itanguá" da Defesa Civil não é a bacia do relevo.** Desenhamos a bacia do Córrego Itanguá pelo relevo (`python -m pipeline bacia`: tudo o que drena até a foz do córrego no Rio Sorocaba, 41 km², arquivo `bacia_itangua.geojson`). Só **89 dos 340** registros com a rua localizada caem dentro dela, e a Vila Mineirão, o Centro, a Vila Barcelona e o Além Ponte ficam fora. A "bacia" da planilha é uma **região de trabalho** da Defesa Civil, não uma bacia hidrográfica.

Por isso fizemos a comparação local de dois jeitos:

| Comparação | Registros | Risco alto | Ruas no alto | Vezes o acaso | Alto + médio | Ruas no alto + médio | Vezes o acaso |
|---|---|---|---|---|---|---|---|
| **Depois do mapa, cidade inteira** (a tabela acima) | 102 | 47% | 12% | 3,8× | 89% | 30% | 3,0× |
| **Depois do mapa, só ruas da região** (a até 1 km de alguma via da planilha) | 102 | 47% | 16% | **3,0×** | **89%** | **35%** | **2,6×** |
| Todos, só ruas da região | 334 | 64% | 16% | 4,1× | 92% | 35% | 2,6× |
| Todos, só ruas da bacia do relevo (os 87 de dentro) | 87 | 67% | 7% | 10× | 86% | 21% | 4,0× |

- **A região tem mesmo mais ruas baixas:** 35% das ruas dela estão no risco alto ou médio, contra 30% na cidade. A preocupação procede.
- **Mesmo assim, o resultado continua forte.** Comparando só com as ruas vizinhas, os chamados de depois do mapa caem no risco alto ou médio **2,6 vezes** mais do que se caíssem em qualquer rua da região, e no risco alto, **3 vezes** mais.
- **A carta oficial, na mesma comparação local,** marca 7% das ruas da região e pega 33% dos chamados de depois do mapa.
- **Dentro da bacia do relevo** o número sobe (10× no risco alto), porque a bacia inteira, com as cabeceiras altas, tem poucas ruas baixas. Mas lá só entram 87 registros e só 1 de depois do mapa, então esse grupo não serve para o teste de depois do mapa.
- **Qual número usar:** para falar com a banca, o mais justo é o da região: **89% dos chamados de depois do mapa no risco alto ou médio, que reúne 35% das ruas da região (2,6×)**. Os números de todas as comparações estão em `lai_defesa_civil.json`, no campo `comparacao_local`.

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
- **Registros oficiais da cidade inteira só de 2022–2023.** Os de 2021–2026 chegaram só da Bacia do Itanguá ([terceiro teste](#terceiro-teste-registros-oficiais-de-2021-a-2026)). Para o resto da cidade nesses anos, o [segundo teste](#segundo-teste-notícias-de-2024-a-2026) usa notícias.
- **Alagamento por drenagem.** O HAND mede a altura sobre os córregos. Alagamento de bueiro em terreno alto, como o de algumas vias do segundo teste, fica fora do risco alto.
- **Limiar fixo.** O córrego começa em 0,5 km² drenados e as faixas seguem Nobre et al. (2011). Esses valores **não foram ajustados** para melhorar este resultado.

## Fontes

- Defesa Civil de Sorocaba: relatórios de ocorrências 2022–2023 (anexo do TCC de M. C. Vargem, Unesp, 2024).
- Defesa Civil de Sorocaba: registros de alagamento, inundação e enxurrada da Bacia do Itanguá, 2021–2026. Resposta ao pedido de acesso à informação Fala.BR nº 03959.2026.000348-13 (Prefeitura de Sorocaba, SEMOB, 16/11/2026). Agregado por via em `docs/dados/lai_defesa_civil.csv`.
- OpenStreetMap (ODbL), via Overpass API.
- Notícias de 2024–2026 (G1, Jornal Cruzeiro do Sul, Agência de Notícias da Prefeitura, Band, TV Sorocaba, Jornal Z Norte, Portal Porque e outros): lista completa, com links, em `docs/dados/noticias.csv`. Busca e leitura com Firecrawl; pontos das vias novas pelo Nominatim (OpenStreetMap).
- HAND: Nobre, A. D. et al. (2011). *Height Above the Nearest Drainage – a hydrologically relevant new terrain model*. Journal of Hydrology 404, 13–29. https://doi.org/10.1016/j.jhydrol.2011.03.051
- Relevo: ANADEM v1, Laipelt et al. (2024). https://doi.org/10.3390/rs16132321
- Carta oficial: Instituto de Pesquisas Tecnológicas (IPT) e CPRM/Serviço Geológico do Brasil (2015). *Carta de suscetibilidade a movimentos gravitacionais de massa e inundações: município de Sorocaba - SP*. https://rigeo.sgb.gov.br/items/cb9a8ac7-dda7-45e0-9dbe-7e8664b6b665
