# Como o time trabalha

Guia do **Habeas Code** para manter o CityShield organizado. Leia uma vez antes do primeiro commit.

## Frentes

Cada frente tem responsável: ele cuida das tarefas dela, revisa o que entra e decide quando há dúvida.

| Frente | Pastas | Responsável |
|---|---|---|
| Mapas e dados | `pipeline/` | Lucas ([@LucasAmadoS](https://github.com/LucasAmadoS)) |
| Site | `web/`, `docs/` (página pública) | Lucas ([@LucasAmadoS](https://github.com/LucasAmadoS)) |
| Backend | `api/`, `db/` | Rafael ([@rafaelsiverisaugusto](https://github.com/rafaelsiverisaugusto)) |
| Produto e apresentação | `README.md`, `docs/`, vídeo, pitch, fontes | Enzo ([@enzocalhareslava-boop](https://github.com/enzocalhareslava-boop)) (dados, fontes e Defesa Civil) e Nicollas ([@nicollasscarpellileon](https://github.com/nicollasscarpellileon)) (textos e vídeo). Conteúdo jurídico com consultoria do Rafael, advogado do time |

**Revisão cruzada:** o PR de uma frente é aprovado por alguém de **outra** frente. Assim todo mundo entende o projeto inteiro, e não só a sua parte.

## Quadro de tarefas

Todas as tarefas ficam no quadro: **https://github.com/orgs/habeas-code/projects/1**

| Coluna | Significa | Quem move |
|---|---|---|
| **A fazer** | ninguém começou | entra sozinha quando a issue é criada |
| **Fazendo** | alguém está trabalhando | você, ao começar |
| **Revisão** | PR aberto esperando aprovação | sozinho, quando o PR tem `Closes #N` |
| **Feito** | entrou na `main` | sozinho, quando o PR é mergeado |

Cada card é uma issue. O **rótulo** diz a frente (`pipeline`, `api`, `web`, `produto`) e o **marco** diz a semana do [cronograma](docs/CRONOGRAMA.md).

**Para pegar uma tarefa:** abra o card, clique em **Assignees** e se coloque, depois arraste para **Fazendo**. Pegue uma tarefa por vez.

**Para criar uma tarefa nova:** no repositório, vá em **Issues → New issue → Tarefa**. Ela entra sozinha no quadro em **A fazer**. Coloque o rótulo da frente e o marco da semana.

Na revisão do fim de semana, o time olha o quadro filtrado pelo marco da semana: o que não foi para **Feito** é discutido ou vai para a semana seguinte.

## Fluxo de uma tarefa

```
Issue  →  branch  →  commits  →  Pull Request  →  1 revisão  →  merge na main
```

1. **Toda tarefa é uma issue do quadro.** Se ainda não existe, crie com o modelo "Tarefa", com o rótulo da frente, e se atribua.
2. **Crie uma branch a partir da `main` atualizada:**
   ```bash
   git switch main
   git pull
   git switch -c feat/hand-area-piloto
   ```
3. **Faça commits pequenos** seguindo o padrão abaixo.
4. **Abra um Pull Request** usando o modelo e escreva `Closes #12` (número da issue) na descrição. Tem que ser em inglês (`Closes`, `Fixes` ou `Resolves`): é isso que liga o PR à issue, move o card no quadro e fecha a issue no merge.
5. **Outra pessoa revisa.** O merge só acontece com 1 aprovação. Use **Squash and merge**.
6. **Apague a branch** depois do merge.

Ninguém faz push direto na `main`.

## Nome das branches

`tipo/descricao-curta`, em minúsculas e com hífen:

```
feat/hand-area-piloto
fix/legenda-mapa-celular
docs/roteiro-video
```

## Padrão de commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/pt-br/) com a descrição em português:

```
tipo(escopo): o que mudou, no presente
```

| Tipo | Quando usar |
|---|---|
| `feat` | funcionalidade nova |
| `fix` | correção de erro |
| `docs` | README, guias, textos |
| `style` | só visual/CSS, sem mudar comportamento |
| `refactor` | reorganiza código sem mudar o resultado |
| `test` | testes |
| `data` | dados, fontes, camadas geradas |
| `chore` | configuração, dependências, Docker, CI |

**Escopos:** `pipeline`, `api`, `web`, `docs`, `db`, `infra`.

Exemplos:

```
feat(pipeline): calcula HAND da área piloto Norte
fix(web): legenda do mapa cortada no celular
data(pipeline): adiciona estacionamentos do OSM no raio de 800 m
docs: roteiro do vídeo do rascunho
chore(infra): fixa versão do PostGIS no compose
```

Regras:
- Uma mudança por commit. Se precisar de "e" na mensagem, provavelmente são dois commits.
- Até ~70 caracteres na primeira linha, sem ponto final.
- Se precisar explicar o porquê, pule uma linha e escreva no corpo.

## Commit todo dia

A organização do Hack Brasil acompanha os commits. Cada um faz pelo menos um commit nos dias em que trabalhar, mesmo que pequeno. Trabalho parado no seu computador não conta.

## O que nunca vai para o repositório

- `dados_privados/`: endereços e números de casa da Defesa Civil. **Nunca.**
- `.env` e qualquer senha ou chave de API. Use o `.env.example` como modelo.
- Arquivos `.tif` grandes: o pipeline baixa sozinho.
- Fotos sem licença livre. Toda imagem nova entra em `docs/img/CREDITOS.md`.

O CI barra automaticamente algumas dessas coisas, mas confira antes do `git add`.

## Números e fontes

Todo número que aparece no site ou no vídeo precisa ter fonte. Escreva a fonte no código ou no texto, junto do número. Os registros mostram **concentração por rua**, não o endereço exato. Não escreva o contrário.

## Quando está pronto

Uma tarefa está pronta quando:

- [ ] funciona rodando com `docker compose up` (ou abrindo a página)
- [ ] o PR foi revisado e aprovado por outra pessoa
- [ ] números novos têm fonte
- [ ] o README ou a documentação foi atualizado, se algo mudou para quem usa

## Comunicação

- **WhatsApp:** recados rápidos e aviso de "abri PR, alguém revisa?".
- **Issues e PRs:** decisões técnicas, para ficar registrado.
- **Reuniões:** horários fixos abaixo.

## Reuniões

| Dia | Horário | Duração | Pauta |
|---|---|---|---|
| **Terça** | 19h30–19h50 | 20 min | Acompanhamento: com o quadro aberto, cada um diz o que fez, o que vai fazer e o que está travando |
| **Quinta** | 19h30–19h50 | 20 min | Acompanhamento: mesma pauta da terça |
| **Domingo** | 10h00–10h40 | 40 min | Revisão da semana: quadro filtrado pelo marco da semana, meta do [cronograma](docs/CRONOGRAMA.md) cumprida ou não, o que passa para a próxima semana, distribuição das tarefas novas |

Regras:
- Começa e termina no horário. Assunto que não couber vira issue ou conversa à parte.
- Quem não puder ir avisa antes no grupo e manda por escrito o que fez, o que vai fazer e o que está travando.
- Decisão importante tomada na reunião entra em [`docs/decisoes.md`](docs/decisoes.md).
