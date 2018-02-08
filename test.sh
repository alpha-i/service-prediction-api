#!/usr/bin/env bash

trap "exit" INT TERM ERR
trap "kill 0" EXIT
docker-compose up -d
PGPASSWORD=postgres psql -h localhost -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'test'" | grep -q 1 || psql -U postgres -h localhost -c "CREATE DATABASE test"
celery -A test.test_app.celery worker -E --loglevel=info &
sleep 3  # give celery time to start
pytest test/
kill %1
docker-compose stop
wait
