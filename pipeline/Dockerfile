FROM python:3.12-slim
WORKDIR /app
# libexpat1: o GDAL que vem dentro do rasterio precisa dela e a imagem slim não traz
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "pipeline"]
