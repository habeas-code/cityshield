-- Nenhuma consulta do usuário da API passa de 5 s: uma consulta presa é
-- cancelada em vez de travar a API.
-- Fica no banco, e não na conexão, porque o pooler do Neon recusa o
-- parâmetro "options" (https://neon.com/docs/connect/connection-errors).
-- No Docker, este script roda como o usuário do .env (POSTGRES_USER).
-- No Neon, o mesmo comando é rodado uma vez no SQL Editor (docs/deploy.md).
ALTER ROLE CURRENT_USER SET statement_timeout = '5s';
