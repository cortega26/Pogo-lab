.PHONY: bootstrap migrate seed test run lint typecheck coverage precommit clean tailwind-install tailwind-build tailwind-watch

bootstrap: .venv compose.yaml
	uv sync
	cp -n .env.example .env 2>/dev/null || true
	uv run python manage.py migrate

.venv:
	uv sync

migrate:
	uv run python manage.py migrate

seed:
	uv run python manage.py seed

test:
	uv run pytest

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
	curl -sL https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 \
	  -o /tmp/tailwindcss
	chmod +x /tmp/tailwindcss
	mv /tmp/tailwindcss tailwindcss

tailwind-build: tailwindcss
	./tailwindcss -i static/css/input.css -o static/css/output.css --minify

tailwind-watch: tailwindcss
	./tailwindcss -i static/css/input.css -o static/css/output.css --watch

clean:
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	rm -f tailwindcss
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
