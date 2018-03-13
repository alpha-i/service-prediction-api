from datetime import datetime, date
from enum import Enum

import numpy
from flask.json import JSONEncoder
from sqlalchemy.ext.declarative import DeclarativeMeta

from app.core.models import BaseModel


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        if issubclass(obj.__class__, BaseModel):
            data, _ = obj.SCHEMA().dump(obj)
            return data
        if isinstance(obj.__class__, DeclarativeMeta):
            return obj.to_dict()
        if issubclass(obj.__class__, Enum):
            return obj.name
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S%z')
        if isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, numpy.float32):
            return obj.tolist()
        return super(CustomJSONEncoder, self).default(obj)
