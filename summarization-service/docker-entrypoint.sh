#!/bin/sh


echo "Waiting for Summary PostgreSQL..."
while ! nc -z "$SUMMARY_DB_HOST" 5432; do
  sleep 1
done
echo "Summary PostgreSQL is ready"

echo "Running Alembic migrations for Summary DB..."
alembic upgrade head

echo "Starting FastStream application..."
exec faststream run app.main:app --host 0.0.0.0