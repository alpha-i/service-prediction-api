from celery import Celery
from flask import Flask, request
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap

from app.core.utils import CustomJSONEncoder
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


def create_app(config_filename, register_blueprints=True):
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    Bootstrap(app)

    app.config.from_object(config_filename)

    migrate = Migrate()

    # Init Flask-SQLAlchemy
    from app.db import db
    db.init_app(app)
    migrate.init_app(app, db)

    if register_blueprints:
        from app.views.main import home_blueprint
        from app.views.predict import predict_blueprint
        from app.views.customer import customer_blueprint
        from app.views.upload import upload_blueprint
        from app.views.authentication import authentication_blueprint
        from app.views.filters import to_pretty_json
        app.register_blueprint(home_blueprint, url_prefix='/')
        app.register_blueprint(predict_blueprint, url_prefix='/predict')
        app.register_blueprint(customer_blueprint, url_prefix='/customer')
        app.register_blueprint(upload_blueprint, url_prefix='/upload')
        app.register_blueprint(authentication_blueprint, url_prefix='/auth')
        app.jinja_env.filters['tojson_pretty'] = to_pretty_json

        @app.before_request
        def before_request():
            # When you import jinja2 macros, they get cached which is annoying for local
            # development, so wipe the cache every request.
            if 'localhost' in request.host_url or '0.0.0.0' in request.host_url:
                app.jinja_env.cache = {}

    app.json_encoder = CustomJSONEncoder
    return app


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=CELERY_RESULT_BACKEND,
        broker=CELERY_BROKER_URL
    )
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
