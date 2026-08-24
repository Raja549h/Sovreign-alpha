FROM python:3.11-slim

LABEL version="3.0.0"
LABEL build_date="2026-08-19"

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libcairo2-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR $HOME/app

# We are using the main requirements.txt which is now streamlined for DaaS
COPY --chown=user requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

RUN chown -R user:user /home/user

USER user

# Headless DaaS pipeline — no web server, no exposed ports
CMD ["python", "-c", "print('Sovereign Alpha DaaS container ready.')"]
