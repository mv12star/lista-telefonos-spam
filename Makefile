.PHONY: help install test lint typecheck run clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter (ruff)"
	@echo "  make typecheck  - Run type checker (mypy)"
	@echo "  make run        - Run the spider"
	@echo "  make clean      - Clean generated files"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

lint-fix:
	ruff check src/ tests/ --fix

typecheck:
	mypy src/

format:
	black src/ tests/

run:
	python -m src.spider

run-scraper:
	python src/scraper.py

clean:
	rm -f lista_numeros_spam.txt
	rm -f numeros_spam_dialer.txt
	rm -f numeros_spam_blocker.txt
	rm -f contactos_spam.vcf
	rm -f numeros_spam.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
