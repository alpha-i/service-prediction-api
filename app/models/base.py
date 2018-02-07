import datetime

from app.db import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    last_update = db.Column(db.DateTime, onupdate=datetime.datetime.utcnow(), default=datetime.datetime.utcnow(), index=True)

    def to_dict(self):
        return {column.key: getattr(self, attr) for attr, column in self.__mapper__.c.items()}

    def __iter__(self):
        return self.to_dict().iteritems()
