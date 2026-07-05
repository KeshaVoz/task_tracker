FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh


ENTRYPOINT ["/docker-entrypoint.sh"]