# Prediction Service API Server

Tell something more about the app...

## Setup

`pip install -r dev-requirements.txt`

## Test

By running

`./test.sh`

you'll get a functional test run. Currently we don't mock anything, so the unit tests need a running postgresql
and a test celery worker. This needs to change in the future (by abstracting out db access and mocking tasks).

## Run

`docker-compose up -d`

`export FLASK_APP=run.py`

`export PGUSER=postgres`

`PGPASSWORD=postgres psql -h localhost -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'database'" | grep -q 1 || psql -U postgres -h localhost -c "CREATE DATABASE database"`

`flask db upgrade`

`export APP_CONFIG=local.env`

`honcho start`

The API server is now running on localhost:5000. Follow the tests for a little tour of the current functionality.
