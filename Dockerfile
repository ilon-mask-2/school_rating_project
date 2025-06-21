# Используем официальный минимальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем все файлы проекта в контейнер
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Указываем переменную окружения, чтобы Python правильно видел модули
ENV PYTHONPATH=/app

# Открываем порт 5000 (если Railway или Docker его требует)
EXPOSE 5000

COPY server/db/database.db /app/server/db/database.db
# Запуск Flask-приложения
CMD ["python", "server/wsgi.py"]
