from app import create_app, make_celery

# yes, we need to make this config dynamic
APP = create_app('config')
# yes, you have to run a postgresql instance locally (I know, I know)
# use the provided docker-compose – but create a `test` database on it first (test.sh does that for you)
APP.config['TESTING'] = True
APP.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres@localhost:5432/test"
celery = make_celery(APP)
