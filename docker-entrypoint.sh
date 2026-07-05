#!/bin/sh

echo "Waiting for PostgreSQL..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done
echo "PostgreSQL is ready"

echo "Waiting for Kafka broker to open port 29092..."
while ! nc -z kafka 29092; do
  sleep 1
done
echo "Kafka broker is ready and accepting connections!"

echo "Alembic migrations..."
alembic upgrade head

echo "Starting application with arguments: $@"
exec "$@"