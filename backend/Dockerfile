# syntax=docker/dockerfile:1

FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system app \
    && useradd --system --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

# Build-time only: lets settings.py import and collectstatic run without a
# real database or secret. Not used at runtime - real values come from the
# deploy environment. Migrations are deliberately NOT run here; see
# docs/DECISIONS.md.
RUN DJANGO_SECRET_KEY=build-time-placeholder-not-used-at-runtime \
    DJANGO_DEBUG=False \
    POSTGRES_DB=build POSTGRES_USER=build POSTGRES_PASSWORD=build \
    POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
    python manage.py collectstatic --no-input

RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/')" || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]
