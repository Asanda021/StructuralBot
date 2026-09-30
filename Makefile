.PHONY: install test compile check run docker-build docker-up docker-down docker-test clean

PYTHON := python
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest

# ---------------------------------------------------------
# INSTALLATION
# ---------------------------------------------------------

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio

# ---------------------------------------------------------
# TESTING
# ---------------------------------------------------------

test:
	$(PYTEST) -ra

test-unit:
	$(PYTEST) -ra -m unit

test-integration:
	$(PYTEST) -ra -m integration

test-billing:
	$(PYTEST) -ra -m billing

test-ai:
	$(PYTEST) -ra -m ai

test-bot:
	$(PYTEST) -ra -m bot

# ---------------------------------------------------------
# CODE QUALITY
# ---------------------------------------------------------

compile:
	$(PYTHON) -m compileall -q .

check:
	$(PYTEST) -ra
	$(PYTHON) -m compileall -q .

# ---------------------------------------------------------
# LOCAL RUN
# ---------------------------------------------------------

run:
	$(PYTHON) bot.py

# ---------------------------------------------------------
# DOCKER
# ---------------------------------------------------------

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# ---------------------------------------------------------
# CLEANUP
# ---------------------------------------------------------

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
