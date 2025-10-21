FROM python:3.12-slim-bookworm AS runtime

ENV VIRTUAL_ENV=/venv \
    PATH=/venv/bin:$PATH \
    PYTHONFAULTHANDLER=1 \
    PYTHONBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Crea venv
RUN python -m venv /venv && pip install --upgrade pip

# 1) Instala deps pinneadas
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
# (requirements.txt debe contener: neo4j==4.4.11)

# 2) Copia el código y instala editable SIN deps (para no tocar neo4j)
COPY . /app
RUN pip install -e . --no-deps

# (opcional si usas layout src)
ENV PYTHONPATH=/app/src

USER 1001:1001
EXPOSE 8000
CMD ["python", "/app/src/backend/manage.py", "runserver", "0.0.0.0:8000"]

#Por si no funciona es el neo4j 4.4.1 instalarlo a travñes de pip