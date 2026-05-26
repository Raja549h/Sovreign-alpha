FROM python:3.11-slim

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

COPY --chown=user requirements-render.txt .

RUN pip install --no-cache-dir --user -r requirements-render.txt

COPY --chown=user . .

RUN mkdir -p billing research/data/filings research/data/transcripts research/data/notes logs

RUN python dashboard/seed_db.py

EXPOSE 7860

CMD ["python", "dashboard/app.py"]
