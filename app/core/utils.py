import uuid
from datetime import datetime, date
from enum import Enum
from functools import wraps

import numpy
from flask import request, g, json, current_app
from flask.json import JSONEncoder
from sqlalchemy.ext.declarative import DeclarativeMeta
from app.core.entities import BaseEntity


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        if issubclass(obj.__class__, BaseEntity):
            data, _ = obj.SCHEMA().dump(obj)
            return data
        if isinstance(obj.__class__, DeclarativeMeta):
            return obj.to_dict()
        if issubclass(obj.__class__, Enum):
            return obj.value
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S%z')
        if isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, numpy.float32):
            return obj.tolist()
        return super(CustomJSONEncoder, self).default(obj)


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
