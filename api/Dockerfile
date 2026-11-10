FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Produção (Render): sem --reload e na porta que o Render define em PORT.
# Sem PORT (no computador), usa 8000. O "exec" deixa o uvicorn receber direto
# o aviso de desligar do Render e fechar as conexões com calma.
# (No docker compose, o "command" do serviço api troca isto pelo modo --reload.)
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
