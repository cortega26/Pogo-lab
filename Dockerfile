FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY manage.py ./
COPY config/ ./config/
COPY apps/ ./apps/
COPY engine/ ./engine/
COPY templates/ ./templates/
COPY static/ ./static/
COPY locale/ ./locale/
COPY docs/ ./docs/
RUN uv sync --frozen --no-dev
RUN uv run python manage.py collectstatic --noinput --settings=config.settings.prod

FROM python:3.13-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN groupadd --system app && useradd --system --gid app app

WORKDIR /app
COPY --from=builder /app /app

ENV DJANGO_SETTINGS_MODULE=config.settings.prod
ENV PATH="/app/.venv/bin:$PATH"

USER app

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
