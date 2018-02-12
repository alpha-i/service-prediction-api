from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
)
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models.base import BaseModel
from config import SECRET_KEY


class Customer(BaseModel):
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    tasks = relationship('PredictionTask', back_populates='customer')
    results = relationship('PredictionResult', back_populates='customer')
    data_sources = relationship('DataSource', back_populates='customer')

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=3600):  # TODO: change this!
        s = Serializer(SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id})

    @property
    def data_source(self):
        if len(self.data_sources):
            return self.data_sources[-1]

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(SECRET_KEY)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None

        user = Customer.query.get(data['id'])
        return user

    @staticmethod
    def get_customer_by_username(username):
        try:
            return Customer.query.filter(Customer.username == username).one()
        except NoResultFound:
            return None

    def to_dict(self):
        dictionary = super(Customer, self).to_dict()
        dictionary['data_sources'] = self.data_sources
        dictionary['data_source'] = self.data_source
        return dictionary
