# backend/Dockerfile — SmartGym v2, Entrega 1
#
# Imagen de desarrollo (NO multi-stage / NO optimizada para produccion:
# eso esta explicitamente fuera de alcance en Entrega 1, ver
# COORDINACION-ENTREGA1.md seccion 3, nota para Royer).
#
# Entrypoint exacto confirmado por Valde en backend/README.md, corrido
# con cwd = backend/ (que es el WORKDIR de esta imagen):
#   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
#
# Alembic (`alembic upgrade head`) NO se corre aqui a proposito -- se
# corre a mano (docker compose exec backend alembic upgrade head).

FROM python:3.13-slim

WORKDIR /app

# PYTHONPATH=/app para que `import src...` resuelva sin depender de que
# uvicorn agregue el directorio actual por su cuenta (ver backend/README.md).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Dependencias de sistema para compilar psycopg2-binary==2.9.9 desde
# fuente: esa version no publica wheel precompilado para Python 3.13,
# asi que pip cae a build-from-source y necesita gcc + headers de
# libpq (pg_config). No se sube la version de psycopg2-binary aqui a
# proposito porque esta fijada en el contrato de convenciones del
# equipo (COORDINACION-ENTREGA1.md, seccion 3).
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos primero solo requirements.txt para aprovechar la cache de
# capas de Docker: si el codigo cambia pero no las dependencias, no se
# vuelve a instalar pip en cada build.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# El resto del codigo se copia para que la imagen sea autocontenida (por
# ejemplo, para un `docker build` aislado). En docker-compose, este
# directorio queda ademas montado como volumen para hot-reload; ver
# docker-compose.yml en la raiz.
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
