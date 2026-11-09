# Recomendações: qual solução e por onde começar

**Pergunta:** em cada área candidata da área piloto, qual solução verde cabe, e quais áreas devem vir primeiro?

**Resposta curta:** os **dois parques da várzea**, o Parque das Águas do Abaeté e o Parque Linear do Rio Sorocaba, ficam no topo, com **nota 95 de 100**. São grandes, estão inteiros no risco alto e ficam ao lado das ruas que mais alagaram. Depois vêm áreas verdes pequenas e estacionamentos colados nas ruas com registro.

Para refazer: `docker compose run --rm pipeline python -m pipeline recomendacoes`. O resultado fica em `web/public/dados/recomendacoes.geojson` (cópia para o site em `docs/dados/`).

## Resultado

| Solução | Áreas | Área total |
|---|---|---|
| Parque inundável | 4 | 44,9 ha |
| Jardim de chuva | 31 | 8,7 ha |
| Piso permeável | 7 | 2,0 ha |
| Telhado verde | 6 | 2,7 ha |

**As 5 primeiras da fila:**

| # | Área | Solução | Nota |
|---|---|---|---|
| 1 | Parque das Águas do Abaeté | Parque inundável | 95 |
| 2 | Parque Linear do Rio Sorocaba | Parque inundável | 95 |
| 3 | Parque Porto das Águas | Parque inundável | 41 |
| 4 | Área verde sem nome (4.552 m²) | Jardim de chuva | 30 |
| 5 | Área verde sem nome (2.278 m²) | Jardim de chuva | 27 |

O Porto das Águas é o maior dos três parques, mas fica mais longe das ruas com registro (14 registros a até 300 m, contra 33 e 34 dos outros dois). Por isso fica em terceiro.

## Regra da solução

| Tipo de área (OpenStreetMap) | Condição | Solução |
|---|---|---|
| Área verde | 1 ha ou mais **e** metade ou mais no risco alto | **Parque inundável** |
| Área verde | as demais | **Jardim de chuva** |
| Estacionamento aberto | sempre | **Piso permeável** |
| Prédio com mais de 1.000 m² | sempre | **Telhado verde** |

- **Parque inundável** precisa de espaço e de estar no caminho da água: só faz sentido numa área grande dentro da várzea. Um hectare é o limite que separa os parques das praças nesta área piloto (a maior praça tem 1,0 ha; as demais áreas verdes têm menos de 0,95 ha).
- **Jardim de chuva** é um canteiro rebaixado. Cabe em praça, canteiro e gramado de qualquer tamanho.
- **Piso permeável** troca o asfalto do estacionamento por um piso que deixa a água passar para uma camada de brita por baixo.
- **Telhado verde** só depende de ter cobertura grande. O mapeamento de prédios no OpenStreetMap é parcial na região, então há mais telhados do que os 6 encontrados.

**Alerta de lençol freático.** Jardim de chuva e piso permeável funcionam deixando a água entrar no solo. Quando a área está praticamente no nível do córrego (HAND menor que 1 m), o lençol freático pode estar raso e a infiltração, limitada. Essas áreas **não saem da lista**: recebem um aviso para conferir a profundidade do lençol antes do projeto. O limite de 1 m é um critério nosso, para alertar, não um número de norma. Na área piloto, que está quase toda na várzea, o aviso aparece na maioria dos jardins de chuva e estacionamentos.

## Nota de prioridade

**Risco e prioridade são coisas diferentes.** O **risco** diz o quanto o terreno fica exposto à água (só o relevo, pelo HAND). A **prioridade** diz por onde começar: ela usa o risco e mais dois critérios, as ocorrências por perto e o tamanho. Por isso uma área pode estar **inteira no risco alto e ter prioridade média**: o Parque Porto das Águas é assim, porque tem menos ocorrências registradas por perto do que os dois primeiros da fila. O mapa mostra, em cada área, qual critério baixou a nota.

```
nota = 100 × risco × registros × tamanho
```

Cada fator vai de 0 a 1. Como é uma multiplicação, a área só vai para o topo se for boa nos três: estar no risco, estar perto de onde alaga e ter tamanho para fazer diferença.

| Fator | Como é calculado | Por quê |
|---|---|---|
| **Risco** | fração da área no risco alto + metade da fração no médio | Mesmas faixas do HAND usadas no mapa ([validação](validacao.md)). |
| **Registros** | registros da Defesa Civil em ruas a até **300 m** da borda da área, divididos pelo maior valor entre as áreas | Uma solução ajuda primeiro o entorno. Os registros são por rua, com um ponto por rua ([D4](decisoes.md#d4-registros-tratados-por-rua-nunca-por-endereço)), por isso uma faixa folgada de 300 m. |
| **Tamanho** | escala logarítmica entre a menor área aceita (200 m²) e a maior (16,7 ha) | Em escala normal, um parque de 15 ha valeria 700 praças pequenas e só os parques apareceriam. O logaritmo mantém a ordem (maior vale mais) sem apagar as áreas pequenas. |

**Como ler a nota:**

| Nota | Prioridade | Na área piloto |
|---|---|---|
| 50 a 100 | Alta | 2 áreas |
| 10 a 49 | Média | 11 áreas |
| 0 a 9 | Baixa | 35 áreas |

Nota 0 não quer dizer que a área é inútil: quer dizer que **não tem registro a até 300 m** ou que está **fora do risco**. São 17 áreas assim, entre elas o maior telhado (1,9 ha, num ponto alto). Um telhado verde num lugar alto também segura água que desceria para a várzea, mas esse efeito à distância não entra na nota desta versão.

### Sensibilidade da nota

**A fila quase não muda quando a conta muda.** A nota é uma análise multicritério (MCE) por multiplicação. O jeito mais comum na literatura de seleção de locais para soluções verdes (por exemplo [Alves et al., 2024](https://doi.org/10.1016/j.jenvman.2024.120999), em Londrina) é a **combinação linear ponderada** (WLC): soma os fatores, cada um com um peso, e os pesos somam 1. Refizemos a fila com WLC e quatro conjuntos de pesos (`python -m pipeline sensibilidade`, saída `sensibilidade.json`):

| Pesos WLC (risco / registros / tamanho) | Top 10 igual ao nosso | Top 3 igual | Spearman (fila inteira) |
|---|---|---|---|
| iguais (0,33 / 0,33 / 0,33) | 8 de 10 | 3 de 3 | 0,91 |
| risco em dobro (0,50 / 0,25 / 0,25) | 8 de 10 | 3 de 3 | 0,86 |
| registros em dobro (0,25 / 0,50 / 0,25) | 9 de 10 | 2 de 3 | 0,89 |
| tamanho em dobro (0,25 / 0,25 / 0,50) | 8 de 10 | 3 de 3 | 0,91 |

Spearman compara as duas filas inteiras das 48 áreas: 1 é a mesma ordem, 0 é sem relação.

- **As 6 primeiras ficam no top 10 em todos os cenários.** Abaeté, Parque Linear e Porto das Águas são o top 3 em três dos quatro. Com registros em dobro, o Porto das Águas cede o 3º lugar a uma área verde com mais ocorrências por perto.
- **Quem entra e sai são áreas do meio da fila**, do 7º ao 16º, com notas de 7 a 17. A que mais cai é uma área verde com risco 0,77: quando o risco pesa o dobro, as muitas áreas com risco 1,0 passam na frente dela.
- **Por que mantemos a multiplicação:** na soma, uma área sem nenhuma ocorrência perto ainda pode subir só pelo risco e pelo tamanho. Na multiplicação, ela precisa dos três. É uma escolha de projeto (começar onde já alagou), e o teste mostra que ela não muda quem lidera a fila.

## Quanta água cada solução segura (#17)

**Chuva de referência: 50 mm**, perto da chuva de **16/10/2026** em Sorocaba (52 mm em 24 h), quando a Av. Dom Aguirre e a XV de Agosto foram interditadas. Cada número usa um valor publicado ([D11](decisoes.md#d11-toda-estimativa-com-fonte)) ou uma conta com o relevo, e o site mostra a conta e a fonte no ⓘ de cada área.

| Solução | Conta | Valor usado | Fonte |
|---|---|---|---|
| Piso permeável | área × 50 mm | a base de brita segura até **50 mm** da chuva que cai no próprio piso | Prefeitura de São Paulo, ETS-03/2013 (brita de 25 cm × 20% de vazios) |
| Jardim de chuva | área do jardim × 15 cm | lâmina de **15 cm = 150 L por m²**; o jardim recebe a água de 10× a sua área em volta | Hinman, *Rain Gardens*, WSU Extension, 2007 |
| Telhado verde | área × 50 mm × 47% | retém **47%** da chuva (limite de baixo da faixa 47–62%; em chuva forte é menos) | Vacari et al., 2019, *E&S Engineering and Science*, UFMT |
| Parque inundável | volume entre o terreno e uma lâmina de **1 m** acima do fundo | capacidade de armazenamento, pelo relevo | cálculo do CityShield sobre o ANADEM v1 (30 m) |

**Premissas nossas** (estão no começo de `pipeline/pipeline/volumes.py` e saem no campo `parametros` do arquivo):

- **Jardins ocupam 10% da área verde.** Uma praça não vira um jardim de chuva inteiro: ela continua sendo praça, com canteiros rebaixados. Com 10%, a conta fica conservadora.
- **Parque alaga até 1 m acima do fundo.** O fundo é o 10º percentil da altura do terreno dentro do parque. As células mais de 3 m abaixo da mediana ficam de fora, porque são lago ou leito de rio e já têm água (é o caso de parte do Porto das Águas).

**Resultado na área piloto:**

| Solução | Áreas | Volume |
|---|---|---|
| Parque inundável | 4 | ≈ 131.700 m³ de **capacidade** de armazenamento |
| Jardim de chuva | 31 | ≈ 1.300 m³ retidos na chuva de 50 mm |
| Piso permeável | 7 | ≈ 1.000 m³ retidos na chuva de 50 mm |
| Telhado verde | 6 | ≈ 630 m³ retidos na chuva de 50 mm |

1 m³ = 1.000 litros = uma caixa d'água comum. Os parques da várzea concentram quase todo o volume. A nota de prioridade não usa o volume: ela continua sendo risco × ocorrências × tamanho.

**Capacidade não é o mesmo que água retida.** Jardim, piso e telhado seguram a chuva que cai neles ou em volta. O parque inundável é um **reservatório**: a capacidade diz quanto cabe nele quando o rio e as galerias transbordam. Por isso o site usa rótulos diferentes ("água que segura" e "água que pode guardar") e os dois tipos não são somados.

**Limites:** são valores de projeto publicados, não medições em Sorocaba. Solo argiloso e lençol freático alto reduzem a infiltração. O relevo de 30 m dá ordem de grandeza para os parques, não o volume de projeto. Telhado verde precisa de laudo da estrutura.

## Cenário antes e depois (#20)

Na plataforma, a aba **Simulação** mostra o cenário da área piloto: a pessoa escolhe a **chuva** (10 a 120 mm), as **soluções** e se entram **todas as áreas** ou **só as de prioridade média ou alta**, e vê quanto da água vai para a rua **antes** e **depois**.

Para cada área de jardim, piso ou telhado, com chuva de `P` mm:

| Solução | Água que chega | Água retida |
|---|---|---|
| Piso permeável | área × P | área × mín(P, 50 mm) |
| Telhado verde | área × P | área × P × 0,47 |
| Jardim de chuva | jardim × 10 × P, com jardim = 10% da área | mín(chega, jardim × 0,15 m) |

Antes = soma da água que chega. Depois = antes − retida. Os **parques** aparecem num bloco separado, com a **capacidade** total, que não muda com a chuva e não entra na conta de antes e depois.

Os números (50 mm, 0,47, 10%, 10×, 0,15 m) **não estão escritos no site**: ele lê do campo `parametros` do `recomendacoes.geojson`, que o pipeline grava a partir de `pipeline/pipeline/volumes.py`. Assim pipeline, site e API (`/cenario`, #18) usam sempre os mesmos valores. Com 50 mm, a conta do site dá exatamente o `volume_m3` do pipeline em todas as 44 áreas de jardim, piso e telhado (conferido em teste).

Na área piloto, com todas as áreas:

| Chuva | Chega | Retida | Retido |
|---|---|---|---|
| 10 mm | 1.337 m³ | 1.195 m³ | 89% |
| 50 mm | 6.686 m³ | 2.937 m³ | 44% |
| 120 mm | 16.047 m³ | 3.818 m³ | 24% |

Em chuva forte a porcentagem cai porque as soluções enchem: é o comportamento esperado, e o painel mostra isso em vez de esconder.

## O que o arquivo traz

Cada área em `recomendacoes.geojson` tem os campos do [passo das áreas](../pipeline/pipeline/areas.py) (tipo, nome, área, frações de risco) e mais:

| Campo | Exemplo | O que é |
|---|---|---|
| `id` | `way-48448685` | id fixo da área, vindo do OpenStreetMap (`osm` com hífen no lugar da barra). Use este em `/areas/{id}`; a `posicao` muda quando os parâmetros mudam |
| `solucao` | `parque_inundavel` | código da solução: `parque_inundavel`, `jardim_chuva`, `piso_permeavel`, `telhado_verde` |
| `solucao_rotulo` | `Parque inundável` | nome para mostrar |
| `motivo` | `Área verde grande na várzea: ...` | uma frase explicando a escolha |
| `alerta` | `Área no nível do córrego: ...` ou `null` | aviso do lençol freático |
| `registros_perto` | `33` | registros em ruas a até 300 m |
| `fator_risco`, `fator_registros`, `fator_tamanho` | `1.0`, `0.97`, `0.98` | os três fatores da nota, de 0 a 1, com 2 casas (a nota sai deles, então a conta fecha) |
| `nota` | `95` | prioridade de 0 a 100 |
| `posicao` | `1` | lugar na fila (1 = primeira) |
| `volume_m3` | `63879` | água que a solução segura (retido) ou pode guardar (capacidade), em m³ |
| `volume_tipo` | `capacidade` | `retido` (chuva de 50 mm) ou `capacidade` (parque) |
| `fracao_retida` | `0.3` ou `null` | parte da água que chega que fica retida; `null` no parque |
| `volume_conta` | `jardim de 455 m² (10% da área) × 15 cm de lâmina` | a conta, em texto |
| `volume_fonte` | `Hinman, Rain Gardens, WSU Extension, 2007` | a fonte do valor |

Esse é o formato que a API entrega em `/areas` e `/areas/{id}` (#18).

## Limites

- **Áreas são candidatas a estudo**, não terrenos disponíveis: uma praça pode já ter outro uso, e um estacionamento pode ser particular.
- A regra olha o tipo e o relevo. Ela não sabe se o solo infiltra bem, se há rede de drenagem por baixo, nem quem é o dono da área. Isso é trabalho de projeto, depois da priorização.
- Os parâmetros (1 ha, metade no risco alto, 300 m, 1 m) estão no começo de `pipeline/pipeline/recomendacoes.py` e saem gravados no arquivo, no campo `parametros`. Mudar um deles e rodar de novo refaz a fila inteira.
