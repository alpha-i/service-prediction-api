from app.db import db


class BaseEntity(db.Model):
    __abstract__ = True
    __tablename__ = None

    INCLUDE_ATTRIBUTES = ()
    EXCLUDE_ATTRIBUTES = ()

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now(), index=True)
    last_update = db.Column(db.DateTime(timezone=True), default=db.func.now(), onupdate=db.func.now(), index=True)

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

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.merge(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


