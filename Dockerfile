# Dockerfile
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости системы (если нужно psycopg2, pip и т.д.)
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Копируем только requirements сначала, чтобы кэшировать зависимости
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

# Определяем переменные окружения
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "-m", "handlers"]
