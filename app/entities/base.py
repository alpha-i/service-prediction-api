import datetime

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

from app.database import db_session


class MyBase:

    def save(self):
        db_session.add(self)
        db_session.flush()
        db_session.commit()

    def update(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return self.save()

    def delete(self):
        db_session.delete(self)
        db_session.flush()
        db_session.commit()


EntityDeclarativeBase = declarative_base(cls=MyBase)
EntityDeclarativeBase.query = db_session.query_property()


class BaseEntity(EntityDeclarativeBase):
    __abstract__ = True
    __tablename__ = None

    INCLUDE_ATTRIBUTES = ()
    EXCLUDE_ATTRIBUTES = ()

    id = Column(Integer, autoincrement=True, primary_key=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, index=True)
    last_update = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                         index=True)

    def serialize(self, format):
        if format == 'json':
            return self.to_dict()

    def to_dict(self):
        base_attributes_dict = {
            column.key: getattr(self, attr)
            for attr, column in
            self.__mapper__.c.items()
        }
        for attribute in self.EXCLUDE_ATTRIBUTES:
            base_attributes_dict.pop(attribute)

        for attribute in self.INCLUDE_ATTRIBUTES:
            base_attributes_dict.update({attribute: getattr(self, attribute, None)})

        return base_attributes_dict

    def __iter__(self):
        return self.to_dict().iteritems()
