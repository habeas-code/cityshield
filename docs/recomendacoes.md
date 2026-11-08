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

## O que o arquivo traz

Cada área em `recomendacoes.geojson` tem os campos do [passo das áreas](../pipeline/pipeline/areas.py) (tipo, nome, área, frações de risco) e mais:

| Campo | Exemplo | O que é |
|---|---|---|
| `solucao` | `parque_inundavel` | código da solução: `parque_inundavel`, `jardim_chuva`, `piso_permeavel`, `telhado_verde` |
| `solucao_rotulo` | `Parque inundável` | nome para mostrar |
| `motivo` | `Área verde grande na várzea: ...` | uma frase explicando a escolha |
| `alerta` | `Área no nível do córrego: ...` ou `null` | aviso do lençol freático |
| `registros_perto` | `33` | registros em ruas a até 300 m |
| `fator_risco`, `fator_registros`, `fator_tamanho` | `0.998`, `0.971`, `0.984` | os três fatores da nota, de 0 a 1 |
| `nota` | `95` | prioridade de 0 a 100 |
| `posicao` | `1` | lugar na fila (1 = primeira) |

Esse é o formato que a API entrega em `/areas` e `/areas/{id}` (#18).

## Limites

- **Áreas são candidatas a estudo**, não terrenos disponíveis: uma praça pode já ter outro uso, e um estacionamento pode ser particular.
- A regra olha o tipo e o relevo. Ela não sabe se o solo infiltra bem, se há rede de drenagem por baixo, nem quem é o dono da área. Isso é trabalho de projeto, depois da priorização.
- Os parâmetros (1 ha, metade no risco alto, 300 m, 1 m) estão no começo de `pipeline/pipeline/recomendacoes.py` e saem gravados no arquivo, no campo `parametros`. Mudar um deles e rodar de novo refaz a fila inteira.
- O volume de água que cada solução segura vem na tarefa #17, com as fontes já escolhidas ([D11](decisoes.md#d11-toda-estimativa-com-fonte)).
