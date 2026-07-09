# Task Tracker

A feature-rich, high-performance task management system with asynchronous notifications, text summarization microservice, and automated CI/CD pipeline.

## Quick Start (Local Development)

### 1. Configure environment variables

Copy the example environment file and update the values with your own credentials:

```bash
cp .env.example .env
```

### 2. Start services

Run the local development stack:

```bash
docker compose -f docker-compose.local.yaml up -d
```

### 3. Open the app

- **Web UI**: http://localhost
- **API Documentation (Swagger)**: http://localhost:8080/docs

### 4. Running Tests Local

To run the automated test suite inside the Docker containers, use the following commands:

```bash
# Main Backend API tests
docker compose -f docker-compose.local.yaml exec api python -m pytest app/tests/ -v -s

# Summarization Microservice tests
docker compose -f docker-compose.local.yaml exec summarization-service python -m pytest app/tests/ -v -s
```

**Stack**: FastAPI · PostgreSQL · Redis · RabbitMQ · Celery · Apache Kafka · Nginx · GigaChat LLM · Pytest · GitHub Actions · Docker
