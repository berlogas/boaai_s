FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Исправление Unicode-проблемы в paper-qa (surrogate characters в PDF)
RUN python3 -c "\
import os; \
utils_path = '/usr/local/lib/python3.11/site-packages/paperqa/utils.py'; \
content = open(utils_path).read(); \
content = content.replace('data = data.encode(\"utf-8\")', 'data = data.encode(\"utf-8\", errors=\"replace\")'); \
open(utils_path, 'w').write(content); \
print('✅ PaperQA Unicode fix applied')\
"

COPY ./app ./app
RUN mkdir -p /app/data /app/global_index /app/uploads

ENV PYTHONPATH=/app/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
