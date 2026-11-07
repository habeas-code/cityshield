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

223 dos 240 registros (75 de 79 ruas) foram localizados no mapa.

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

### Conferência com eventos de 2026

O mapa foi testado com registros de 2022–2023. Em 2026, a imprensa noticiou interdições por alagamento exatamente nas duas avenidas com mais registros:

| Data | O que aconteceu | Chuva | Parte da rua no risco alto do mapa |
|---|---|---|---|
| 22/09/2026 | Av. XV de Agosto interditada por alagamento "após o nível do Rio Sorocaba subir com as chuvas" | 23 mm em 24 h | 90% |
| 16/10/2026 | Av. Quinze de Agosto (entre a R. Fernandópolis e a Radial Norte) e Av. Dom Aguirre (entre a Av. Dr. Artur Bernardes e a Radial Norte) interditadas | 52 mm em 24 h; 216 mm em outubro | XV de Agosto 90%, Dom Aguirre 99,8% |

Não é um teste estatístico (são dois eventos noticiados, não um registro completo), mas mostra que os pontos que o mapa marca continuam alagando em anos que ele não viu.

Fontes: [Band, 22/09/2026](https://www.band.com.br/nacional/sp/xv-de-agosto-sorocaba) · [Band, 16/10/2026](https://www.band.com.br/nacional/sp/chuva-interdicoes-sorocaba)

## Limitações

- **Ruas, não pontos.** Uma avenida longa como a Dom Aguirre (12,9 km no mapa) recebe os registros distribuídos ao longo dela toda. É uma aproximação.
- **Quatro ruas ficaram de fora** (17 registros): Rua Projetada II (Guadalupe), Rua Três e Rua Nove (Itapemirim) e Rua Láurico. Não existem no OpenStreetMap com esse nome perto do lugar indicado, e preferimos deixá-las de fora a adivinhar.
- **Registros dependem de quem registra.** Lugares onde alaga mas ninguém chama a Defesa Civil não aparecem. O teste mede se o mapa acerta onde **houve registro**, não onde **não alaga**.
- **Dois anos de dados** (2022–2023). Os relatórios de 2024–2026 foram pedidos (tarefa #13) e entram como segundo teste.
- **Limiar fixo.** O córrego começa em 0,5 km² drenados e as faixas seguem Nobre et al. (2011). Esses valores **não foram ajustados** para melhorar este resultado.

## Fontes

- Defesa Civil de Sorocaba: relatórios de ocorrências 2022–2023 (anexo do TCC de M. C. Vargem, Unesp, 2024).
- OpenStreetMap (ODbL), via Overpass API.
- HAND: Nobre, A. D. et al. (2011). *Height Above the Nearest Drainage – a hydrologically relevant new terrain model*. Journal of Hydrology 404, 13–29. https://doi.org/10.1016/j.jhydrol.2011.03.051
- Relevo: ANADEM v1, Laipelt et al. (2024). https://doi.org/10.3390/rs16132321
