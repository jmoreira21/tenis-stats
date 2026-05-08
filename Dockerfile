# 1. A BASE: Linux + Python 3.10
FROM python:3.10-slim

# 2. O AVENTAL: Nossa pasta de trabalho lá dentro
WORKDIR /app

# 3. OS INGREDIENTES: Copia o txt que está DENTRO da pasta backend
COPY backend/requirements.txt .

# 4. PREPARO: Instala as bibliotecas
RUN pip install --no-cache-dir -r requirements.txt

# 5. O RECHEIO: Copia TUDO que está dentro da pasta backend (seus .py e o tenis.db) para a caixa
COPY backend/ .

# 6. O SERVIÇO: Libera a porta
EXPOSE 5000

# 7. O COMANDO FINAL: Substitua "app.py" pelo nome exato do seu arquivo principal!
CMD ["python", "app.py"]