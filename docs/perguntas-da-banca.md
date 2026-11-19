# Perguntas da banca: o método em uma página

As perguntas que mais aparecem sobre a matemática do CityShield (1 a 6 e 12) e sobre o uso no mundo real (7 a 11 e 13), com a resposta curta, de onde ela vem e o limite. Os detalhes estão em [validacao.md](validacao.md) e [recomendacoes.md](recomendacoes.md).

## 1. Por que jardim de chuva aqui e piso permeável ali?

**Resposta:** pelo **tipo de lugar** que o OpenStreetMap mostra, mais o risco. É uma regra fixa, igual para todas as áreas:

| Lugar | Condição | Solução |
|---|---|---|
| Área verde | 1 ha ou mais **e** metade ou mais no risco alto | Parque inundável |
| Área verde | as demais | Jardim de chuva |
| Estacionamento aberto | sempre | Piso permeável |
| Prédio com mais de 1.000 m² | sempre | Telhado verde |

Depois da regra, cada área recebe **avisos do que conferir em campo**: lençol freático provavelmente raso (área a menos de 1 m acima do córrego), piso com declividade acima de 3% e jardim a partir de 15%. Os avisos vêm de manuais publicados (MPCA, Hinman/WSU) e não tiram nenhuma área da lista.

**Limite:** a regra **não sabe como o solo infiltra**, se há galeria por baixo nem quem é o dono da área. Não existe esse dado aberto para Sorocaba. Por isso a ficha de cada área começa os "próximos passos" com visita e sondagem do solo. [Regra completa](recomendacoes.md#regra-da-solução)

## 2. A nota de prioridade mede o benefício ambiental?

**Não, e de propósito.** A nota responde **"por onde começar"**, não "quanto ajuda":

```
nota = 100 × risco × ocorrências por perto × tamanho
```

Ela junta três coisas: o terreno está no caminho da água, já alagou ali perto (registros da Defesa Civil a até 300 m) e há espaço para fazer diferença. Como é multiplicação, a área só sobe se for boa nas três.

O **benefício** (quanta água cada área segura) é calculado **à parte** e aparece na ficha. Ele não entra na nota por dois motivos:

- **Jardim, piso e telhado** seguram a chuva que cai neles. **Parque inundável** é um reservatório: a conta dele é de **capacidade**, para quando o rio e as galerias transbordam. Somar ou ordenar os dois juntos misturaria coisas diferentes.
- Os volumes usam valores de manual, não medidas de cada lugar. Pô-los na nota daria a eles uma precisão que não têm.

**A fila é estável:** refizemos a nota como soma com pesos (o jeito mais comum na literatura, WLC) em 4 combinações de pesos. As 6 primeiras áreas ficam entre as 10 primeiras em todas, e a ordem inteira se mantém (Spearman de 0,86 a 0,91). [Sensibilidade](recomendacoes.md#sensibilidade-da-nota)

## 3. O volume de água é coerente com o terreno?

**Nos parques, sim, na escala do relevo. Nos jardins, pisos e telhados, ele é de manual.**

| Solução | De onde vem o volume | Usa o terreno do lugar? |
|---|---|---|
| Parque inundável | volume entre o terreno e 1 m acima do fundo, medido no relevo ANADEM (30 m), mais a área que escoa para o parque e a curva de até onde a água sobe | **Sim** |
| Jardim de chuva | 10% da área vira jardim, com lâmina de 15 cm (Hinman 2007; EPA 2023) | Não; só o tamanho |
| Piso permeável | brita segura até 50 mm (Prefeitura de SP, ETS-03/2013) | Não; só o tamanho |
| Telhado verde | retém 47% da chuva (Vacari et al., 2019) | Não; só o tamanho |

**Limites:**

- Com células de 30 m, a conta serve para parques de vários hectares, não para uma praça pequena.
- A conta é da chuva que cai **nas áreas**. Na bacia inteira o efeito é bem menor: uma simulação hidráulica da Unesp (2026) numa bacia de Sorocaba, com telhado verde e piso permeável, deu de −2,7% a −5,1% no volume da foz. O site mostra esse aviso.
- **Não é modelagem hidráulica:** o CityShield não simula o caminho da água na cidade. É uma estimativa para comparar opções. [Volumes](recomendacoes.md#quanta-água-cada-solução-segura-17)

## 4. Os 74% querem dizer que o mapa acerta 74% das enchentes?

**Não.** Querem dizer que 74% dos registros da Defesa Civil de 2022–2023 caem nos trechos de rua que o mapa marca como risco alto, e que esses trechos são só 12% das ruas da cidade (6× o acaso).

- Os relatórios dizem **a rua**, não o ponto exato. Por isso os registros de cada rua são **divididos pelo comprimento dela** em cada faixa de risco.
- A comparação é com **as ruas da cidade**, não com a área, para não inflar o número (ruas tendem a ficar nos vales).
- É **associação** com o que já aconteceu, não taxa de acerto de previsão.

O teste mais próximo de uma previsão é o terceiro: **depois de o mapa ficar pronto**, 89% dos 102 chamados oficiais de 8 a 12/11/2026 caíram no risco alto ou médio (30% das ruas). A carta oficial marcou 33%. E se a comparação for só com as ruas da própria região, que tem mais ruas baixas que a cidade (35% no risco alto ou médio)? Os 89% continuam: 2,6× o acaso. Mas é uma região e uma chuva só.

O teste **maior** é o quarto: 1.261 chamados oficiais de 2024 a 2026 da **cidade inteira**, depois dos dados com que conferimos o mapa. 75% caem no risco alto (6,1× o acaso); na cheia de janeiro de 2024, 80%. Nas ruas que nem estavam nos relatórios de 2022–2023, 71%. Comparando só com as ruas vizinhas aos chamados, o risco alto ainda pega 5,2× o acaso. [Validação](validacao.md#quarto-teste-a-cidade-inteira-2021-a-2026)

## 5. Por que o piloto é o núcleo Norte e não o Centro?

Nos relatórios de 2022–2023, o núcleo Norte (Parque das Águas, Jd. Maria do Carmo, Abaeté) tem **41 registros** num raio de 800 m, contra 27 no Centro, e tem **área livre** para as soluções (parques, praças, estacionamentos). O corredor Dom Aguirre/Centro tem registros mais espalhados e pouco espaço livre. Ele é a **segunda etapa**. [Decisão D3](decisoes.md#d3-área-piloto-núcleo-norte-raio-de-800-m)

## 6. Vocês publicam dados de moradores?

**Não.** Os relatórios e a planilha da Defesa Civil têm o número da casa de cada chamado. Eles ficam fora do repositório, e o CI bloqueia a pasta privada. O site, a API e os arquivos para baixar só têm **rua, bairro, data e contagem**. Um teste automático falha se o CSV público ganhar outra coluna. [Decisão D4](decisoes.md#d4-registros-tratados-por-rua-nunca-por-endereço)

## 7. Por que não usaram só os dados históricos?

**Porque o histórico só mostra onde alguém chamou a Defesa Civil.** Rua sem registro não quer dizer rua que não alaga: pode ser lugar onde ninguém ligou, ou onde ainda não choveu forte o bastante. O relevo cobre **a cidade inteira**, com ou sem registro.

Os dois se completam, e um testa o outro: o mapa do relevo foi feito **sem olhar os registros** e depois conferido contra eles três vezes ([validação](validacao.md)). Os registros entram na nota de prioridade, para começar por onde já alagou.

## 8. Como vocês evitam falsos positivos?

**Não evitamos todos, e dizemos isso.** O risco alto reúne 12% das ruas da cidade, e muitas delas não têm nenhum registro. Parte disso é falta de registro (pergunta 7); parte é lugar baixo que tem drenagem boa. O relevo não enxerga galerias e bueiros.

O que fizemos para que isso não vire decisão errada:

- **A nota exige ocorrência por perto.** Como ela é uma multiplicação, uma área no risco alto sem nenhum registro a até 300 m fica com nota 0 e vai para o fim da fila.
- **A recomendação é "estudar aqui", não "obra aqui".** A ficha de cada área começa os próximos passos com visita e sondagem.
- **Os erros ficam publicados.** O [segundo teste](validacao.md#segundo-teste-notícias-de-2024-a-2026) lista vias que alagaram fora do risco alto (alagamento de bueiro em terreno alto), que o HAND não pega.

## 9. E se os dados ficarem desatualizados?

**Tudo é refeito com um comando.** O pipeline baixa de novo o OpenStreetMap e refaz risco, validação, áreas, notas e volumes (`docker compose run --rm pipeline`); rodando do zero, ele chega aos mesmos resultados que estão no repositório. Como o OpenStreetMap é editado todo dia, uma conta pode mudar na segunda casa decimal: no teste do zero de 18/11/2026, 5,98× virou 5,97×. Nenhum número publicado (74%, 6×, 89%) muda.

Os **registros novos** vêm da Defesa Civil. Já mostramos o caminho: pedimos pela Lei de Acesso à Informação e recebemos 365 registros da Bacia do Itanguá até 12/11/2026 (terceiro teste); no recurso, a cidade inteira, 1.494 registros de 2021 a 2026 (quarto teste). O ideal, que a própria revisão do [Plano Diretor de Macrodrenagem](https://www.saaesorocaba.com.br/wp-content/uploads/2025/12/volume-vi-relatorio-sintese-3.pdf) (SAAE, 2025) recomenda, é a Defesa Civil georreferenciar as ocorrências e integrar com a drenagem.

O **relevo** quase não muda. Uma obra grande (canalização, aterro) muda o terreno no lugar dela, e o modelo de 30 m não a enxerga até sair uma versão nova do ANADEM.

## 10. Serve para outras cidades?

**O método serve; os dados locais precisam ser buscados.**

| O que o pipeline usa | Para outra cidade |
|---|---|
| Relevo ANADEM (30 m) | já cobre o Brasil inteiro |
| OpenStreetMap (ruas, parques, estacionamentos, prédios) | já cobre; a qualidade varia de cidade para cidade |
| Limite do município | trocar o arquivo `limite_sorocaba.geojson` |
| Área piloto | trocar o ponto e o raio (`PILOTO` em `validacao.py`) |
| Registros de alagamento | **pedir à Defesa Civil local**: sem eles não há validação nem o fator de ocorrências da nota |
| Equação de chuva | trocar pela da cidade (costuma estar no plano de drenagem do município) |

A parte cara de um projeto assim é juntar e limpar os registros. É também o que torna o resultado confiável.

## 11. Qual o custo de implantação e manutenção?

**Do sistema: hoje, zero.** O site fica no GitHub Pages, a API no Render e o banco no Neon, todos em planos gratuitos. A plataforma lê arquivos estáticos e funciona mesmo se a API sair do ar ([D10](decisoes.md#d10-plano-b-geojson-estático)). Para uma prefeitura, o custo é o de alguém rodar o pipeline quando chegarem registros novos.

**Das obras: não estimamos, de propósito.** O custo de um jardim de chuva ou de um piso permeável depende do projeto de engenharia de cada área (solo, drenagem existente, desapropriação, manutenção). Pôr um preço sem esse projeto seria inventar um número. O CityShield entrega **onde estudar primeiro e quanta água cada opção pode segurar**, que é o que a prefeitura precisa para decidir onde gastar o estudo.

## 12. Por que usar HAND?

**Porque precisa só do relevo, que é aberto para o Brasil inteiro, e cabe numa frase:** HAND é a altura do terreno acima do córrego mais próximo ([Nobre et al., 2011](https://doi.org/10.1016/j.jhydrol.2011.03.051)). O terreno que fica poucos metros acima do córrego é o primeiro a encher.

- **Por que não um modelo hidráulico (HEC-RAS, SWMM)?** Eles precisam da rede de galerias, da vazão dos córregos e de cheias medidas para calibrar. Sorocaba não tem esses dados abertos. E um modelo calibrado com os registros da Defesa Civil não poderia ser conferido com esses mesmos registros.
- **Sem ajuste.** O córrego começa em 0,5 km² drenados e as faixas (alto 0–5 m, médio 5–15 m) são as de Nobre et al. Nada foi mexido para melhorar o resultado, e mesmo assim 74% dos registros de 2022–2023 caem no risco alto, que tem 12% das ruas (6× o acaso). O resultado se mantém com chamados que o mapa nunca viu: 75% dos 1.261 de 2024–2026 (6,1×) ([validação](validacao.md)).
- **E a carta oficial?** A carta do IPT/SGB (2015) é precisa nas várzeas largas, mas 55% dos registros ficam fora dela. O HAND mede a altura sobre qualquer córrego, grande ou pequeno, e pega também os vales estreitos da zona urbana ([comparação](validacao.md#comparação-com-a-carta-oficial)).

**Limite:** o HAND diz **onde** a água tende a se acumular, não **quando** nem **quanta**. Também não enxerga alagamento de bueiro em terreno alto. Saber a altura da água numa chuva específica é trabalho de um modelo hidráulico, o próximo passo natural se a prefeitura quiser projetar uma obra.

## 13. Como a prefeitura usaria isso no dia a dia?

**Para decidir onde gastar o próximo estudo de viabilidade.** Cada parte da plataforma responde a uma pergunta de quem decide ([público, D13](decisoes.md#d13-público-quem-decide-onde-investir-contra-enchentes)):

| Quem | Quando | O que faz na plataforma |
|---|---|---|
| Defesa Civil | antes da época de chuva | vê onde o relevo e os próprios registros apontam risco (aba Diagnóstico) |
| Defesa Civil | depois de uma chuva forte | manda a planilha nova; o pipeline roda com um comando e mostra se os chamados caíram nas áreas marcadas, como no [terceiro teste](validacao.md#terceiro-teste-registros-oficiais-de-2021-a-2026) |
| Meio Ambiente e Obras | ao montar o orçamento do ano | escolhe na fila "Por onde começar" quais áreas estudar primeiro; a ficha diz o porquê e os próximos passos (visita, sondagem do solo e do lençol, projeto) |
| Meio Ambiente e Obras | ao comparar opções | usa a Simulação para ver quanta água cada tipo de solução segura, com a chuva da equação do SAAE |
| Câmara de Vereadores | se o PL Cidade-Esponja (2024) avançar | tem uma lista pública de por onde começar, com fonte em cada número |

**Exemplo:** o Parque das Águas do Abaeté é o 1º da fila (nota 95). A ficha mostra 14,9 ha no risco alto, os registros da Defesa Civil nas ruas em volta e quanto ele pode guardar como parque inundável. O próximo passo indicado não é a obra: é confirmar quem administra a área e fazer o estudo de viabilidade.

A revisão do [Plano Diretor de Macrodrenagem](https://www.saaesorocaba.com.br/wp-content/uploads/2025/12/volume-vi-relatorio-sintese-3.pdf) (SAAE, 2025) pede justamente georreferenciar as ocorrências da Defesa Civil e integrá-las à drenagem. É o que o pipeline faz com a planilha deles.

**Limite:** a plataforma não substitui o projeto de engenharia nem a visita de campo. E ainda não foi usada dentro da prefeitura: os registros vieram pela Lei de Acesso à Informação, e o teste com quem decide é o próximo passo.
