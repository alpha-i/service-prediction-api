import uuid
from functools import wraps
import importlib

from flask import request, g, json, current_app


def parse_request_data(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.is_json:
            g.json = request.json
        elif request.form:
            g.json = {
                key: value[0] if len(value) == 1 else value
                for key, value in request.form.lists()
            }
        return fn(*args, **kwargs)

    return wrapper


def json_reload(json_as_a_dict):
    return json.loads(json.dumps(json_as_a_dict))


def allowed_extension(filename):
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config['ALLOWED_EXTENSIONS']


def generate_upload_code():
    return str(uuid.uuid4())


def import_class(name):
    components = name.split('.')
    mod = importlib.import_module(".".join(components[:-1]))
    return getattr(mod, components[-1])
