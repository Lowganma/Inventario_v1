FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
CMD ["gunicorn", "inventario.wsgi:application", "--bind", "0.0.0.0:8000"]
