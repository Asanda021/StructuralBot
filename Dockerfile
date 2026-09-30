FROM python:3.12-slim

# ---------------------------------------------------------
# SYSTEM SETTINGS
# ---------------------------------------------------------

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ---------------------------------------------------------
# WORKING DIRECTORY
# ---------------------------------------------------------

WORKDIR /app

# ---------------------------------------------------------
# SYSTEM DEPENDENCIES
# ---------------------------------------------------------

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# PYTHON DEPENDENCIES
# ---------------------------------------------------------

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

# ---------------------------------------------------------
# APPLICATION FILES
# ---------------------------------------------------------

COPY . .

# ---------------------------------------------------------
# RUNTIME ENVIRONMENT
# ---------------------------------------------------------

ENV STRUCTURALBOT_TESTING=false \
    AI_ENABLED=false \
    AI_PROVIDER=placeholder \
    PAYMENT_PROVIDER=placeholder \
    PAYMENT_GATEWAY_ENABLED=false

# ---------------------------------------------------------
# SECURITY
# ---------------------------------------------------------

RUN useradd \
        --create-home \
        --shell /usr/sbin/nologin \
        structuralbot \
    && chown -R structuralbot:structuralbot /app

USER structuralbot

# ---------------------------------------------------------
# HEALTH / STARTUP
# ---------------------------------------------------------

CMD ["python", "bot.py"]
