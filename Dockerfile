# ─── Image de base ───────────────────────────────────────────────
FROM python:3.12-slim

# ─── Variables d'environnement ────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=logement_cm.settings_prod

# ─── Dépendances système ──────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ─── Répertoire de travail ────────────────────────────────────────
WORKDIR /app

# ─── Dépendances Python ───────────────────────────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# ─── Code source ──────────────────────────────────────────────────
COPY . .

# ─── Collecter les fichiers statiques ────────────────────────────
RUN python manage.py collectstatic --noinput

# ─── Port exposé ──────────────────────────────────────────────────
EXPOSE 8000

# ─── Démarrage ───────────────────────────────────────────────────
CMD ["gunicorn", "logement_cm.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-"]
