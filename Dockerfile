FROM python:3.11-slim

# ============================================================
# CONFIGURACIÓN DE PYTHON
# ============================================================

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app


# ============================================================
# DEPENDENCIAS
# ============================================================

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


# ============================================================
# CÓDIGO DE LA APLICACIÓN
# ============================================================

COPY . .


# ============================================================
# ENTRYPOINT
#
# Docker ejecuta Linux aunque el equipo anfitrión sea Windows.
# Por eso convertimos CRLF -> LF automáticamente.
# ============================================================

RUN sed -i 's/\r$//' /app/docker-entrypoint.sh \
    && chmod +x /app/docker-entrypoint.sh


# ============================================================
# PUERTO
# ============================================================

EXPOSE 8000


# ============================================================
# ARRANQUE
# ============================================================

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["gunicorn", "inventario.wsgi:application", "--bind", "0.0.0.0:8000"]