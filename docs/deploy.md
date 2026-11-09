# Deploy

Banco no Neon, API no Render; o site continua no GitHub Pages (#23).

## Banco no Neon

### Limite de 5 s por consulta (statement_timeout)

Rodar **uma vez** no SQL Editor do Neon, trocando `cityshield` pelo usuário que a API usa:

```sql
ALTER ROLE cityshield SET statement_timeout = '5s';
```

**Por quê:** uma consulta presa é cancelada em 5 s em vez de travar a API. O limite fica no banco, e não na conexão, porque o endereço com pooler do Neon recusa o parâmetro `options` (erro *unsupported startup parameter*, [documentação do Neon](https://neon.com/docs/connect/connection-errors)).

No Docker isso já acontece sozinho pelo `db/init/02_statement_timeout.sql`.

**Conferir:** conectado com o usuário da API, `SHOW statement_timeout;` deve mostrar `5s`.
