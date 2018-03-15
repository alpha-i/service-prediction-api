from celery import Celery
from flask import Flask, request, render_template
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap

from app.core.content import ApiResponse
from app.core.jsonencoder import CustomJSONEncoder
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
        from app.views.user import user_blueprint
        from app.views.company import company_blueprint
        from app.views.prediction import predict_blueprint
        from app.views.customer import customer_blueprint
        from app.views.datasource import datasource_blueprint
        from app.views.authentication import authentication_blueprint
        app.register_blueprint(home_blueprint, url_prefix='/')
        app.register_blueprint(user_blueprint, url_prefix='/user')
        app.register_blueprint(authentication_blueprint, url_prefix='/auth')
        app.register_blueprint(company_blueprint, url_prefix='/company')
        app.register_blueprint(datasource_blueprint, url_prefix='/datasource')
        app.register_blueprint(predict_blueprint, url_prefix='/prediction')
        app.register_blueprint(customer_blueprint, url_prefix='/customer')

        @app.before_request
        def before_request():
            # When you import jinja2 macros, they get cached which is annoying for local
            # development, so wipe the cache every request.
            if 'localhost' in request.host_url or '0.0.0.0' in request.host_url:
                app.jinja_env.cache = {}

        @app.errorhandler(404)
        def render_404(e):
            response = ApiResponse(
                content_type=request.accept_mimetypes.best,
                context={'message': e.description},
                template='404.html',
                status_code=404
            )
            return response()

        @app.errorhandler(401)
        def render_401(e):
            response = ApiResponse(
                content_type=request.accept_mimetypes.best,
                context={'message': e.description},
                template='401.html',
                status_code=401
            )
            return response()

        @app.errorhandler(400)
        def render_400(e):
            response = ApiResponse(
                content_type=request.accept_mimetypes.best,
                context={'message': e.description},
                template='400.html',
                status_code=400
            )
            return response()

        @app.errorhandler(500)
        def render_500(e):
            # We don't want to show internal exception messages...
            return render_template('500.html'), 500

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


