from enum import Enum
from functools import wraps

from flask import request, g, abort
from flask.json import JSONEncoder
from sqlalchemy.ext.declarative import DeclarativeMeta


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            return obj.to_dict()
        if issubclass(obj.__class__, Enum):
            return obj.value
        return super(CustomJSONEncoder, self).default(obj)


def parse_request_data(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.is_json:
            g.json = request.json
        elif request.form:
            g.json = dict(request.form.items())
        else:
            abort(400)
        return fn(*args, **kwargs)

    return wrapper
