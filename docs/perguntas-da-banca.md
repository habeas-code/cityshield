# Perguntas da banca: o método em uma página

As perguntas que mais aparecem sobre a matemática do CityShield, com a resposta curta, de onde ela vem e o limite. Os detalhes estão em [validacao.md](validacao.md) e [recomendacoes.md](recomendacoes.md).

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

O teste mais próximo de uma previsão é o terceiro: **depois de o mapa ficar pronto**, 89% dos 102 chamados oficiais de 8 a 12/11/2026 caíram no risco alto ou médio (30% das ruas). A carta oficial marcou 33%. Mas é uma bacia e uma chuva só. [Validação](validacao.md)

## 5. Por que o piloto é o núcleo Norte e não o Centro?

Nos relatórios de 2022–2023, o núcleo Norte (Parque das Águas, Jd. Maria do Carmo, Abaeté) tem **41 registros** num raio de 800 m, contra 27 no Centro, e tem **área livre** para as soluções (parques, praças, estacionamentos). O corredor Dom Aguirre/Centro tem registros mais espalhados e pouco espaço livre. Ele é a **segunda etapa**. [Decisão D3](decisoes.md#d3-área-piloto-núcleo-norte-raio-de-800-m)

## 6. Vocês publicam dados de moradores?

**Não.** Os relatórios e a planilha da Defesa Civil têm o número da casa de cada chamado. Eles ficam fora do repositório, e o CI bloqueia a pasta privada. O site, a API e os arquivos para baixar só têm **rua, bairro, data e contagem**. Um teste automático falha se o CSV público ganhar outra coluna. [Decisão D4](decisoes.md#d4-registros-tratados-por-rua-nunca-por-endereço)
