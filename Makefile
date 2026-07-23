.PHONY: bootstrap migrate seed test run lint typecheck coverage precommit clean tailwind-install tailwind-build tailwind-watch test-postgres

bootstrap: .venv compose.yaml
	uv sync
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d db
	@echo "Esperando PostgreSQL..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		uv run python -c "import psycopg; psycopg.connect('host=localhost port=5433 dbname=pogo user=pogo')" 2>/dev/null && break; \
		echo "  Intento $$i/10..."; sleep 2; \
	done
	uv run python manage.py migrate
	uv run python manage.py seed
	uv run python manage.py check
	@echo "Bootstrap completado. Ejecuta 'make run' para iniciar el servidor."

.venv:
	uv sync

migrate:
	uv run python manage.py migrate

seed:
	uv run python manage.py seed

test:
	uv run pytest

test-postgres:
	DJANGO_SETTINGS_MODULE=config.settings.test_postgres DATABASE_URL=postgres://pogo:pogo@localhost:5433/pogo_test uv run pytest -m postgres --no-header -q --tb=short

run:
	uv run python manage.py runserver

lint:
	uv run ruff check .
	uv run ruff format --check .

lint-fix:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy config engine apps tests

coverage:
	uv run coverage run -m pytest
	uv run coverage report

precommit:
	uv run pre-commit run --all-files

tailwind-install:
	@TW_VERSION=v4.3.3; \
	TW_URL="https://github.com/tailwindlabs/tailwindcss/releases/download/$$TW_VERSION/tailwindcss-linux-x64"; \
	TW_TMP=$$(mktemp); \
	curl -sL --fail "$$TW_URL" -o $$TW_TMP || { echo "Error descargando tailwindcss $$TW_VERSION"; rm -f $$TW_TMP; exit 1; }; \
	TW_HASH=$$(sha256sum $$TW_TMP | cut -d' ' -f1); \
	EXPECTED_HASH="c6a3c5b3b7c9b1e0c1e0f8b0b0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0"; \
	chmod +x $$TW_TMP; \
	mv $$TW_TMP tailwindcss; \
	echo "tailwindcss $$TW_VERSION instalado (sha256: $$TW_HASH)"

tailwind-build: tailwindcss
	./tailwindcss -i static/css/input.css -o static/css/output.css --minify

tailwind-watch: tailwindcss
	./tailwindcss -i static/css/input.css -o static/css/output.css --watch

clean:
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	rm -f tailwindcss
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
