#!/usr/bin/env bash
PGPASSWORD=postgres psql -h localhost -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'test'" | grep -q 1 || psql -U postgres -h localhost -c "CREATE DATABASE test"
PYTHONOPTIMIZE=1 celery -A test.test_app.celery worker -E --loglevel=info &
sleep 3  # give celery time to start
pytest test/
