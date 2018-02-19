from enum import Enum

from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
)
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models.base import BaseModel
from config import SECRET_KEY


class Actions(Enum):
    FILE_UPLOAD = 'FILE_UPLOAD'
    PREDICTION_STARTED = 'PREDICTION_STARTED'
    CONFIGURATION_UPDATE = 'CONFIGURATION_UPDATE'


class Company(BaseModel):
    name = db.Column(db.String)
    logo = db.Column(db.String)
    profile = db.Column(db.JSON)

    customer_id = db.Column(db.ForeignKey('customer.id'))
    customer = relationship('Customer', back_populates='company')


class Customer(BaseModel):
    email = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    tasks = relationship('PredictionTask', back_populates='customer')
    results = relationship('PredictionResult', back_populates='customer')
    data_sources = relationship('DataSource', back_populates='customer')
    actions = relationship('CustomerAction', back_populates='customer')
    configuration = relationship('CustomerConfiguration', back_populates='customer', uselist=False)
    company = relationship('Company', uselist=False)
    profile = relationship('CustomerProfile', uselist=False)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=3600):  # TODO: change this!
        s = Serializer(SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id})

    @property
    def current_data_source(self):
        if len(self.data_sources):
            return self.data_sources[-1]
        return None

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
    def get_customer_by_email(email):
        try:
            return Customer.query.filter(Customer.email == email).one()
        except NoResultFound:
            return None

    def to_dict(self):
        dictionary = super(Customer, self).to_dict()
        dictionary['data_sources'] = self.data_sources
        dictionary['current_data_source'] = self.current_data_source
        dictionary['configuration'] = getattr(self.configuration, 'configuration', None)
        dictionary['actions'] = self.actions
        return dictionary


class CustomerAction(BaseModel):
    customer_id = db.Column(db.ForeignKey('customer.id'))
    customer = relationship('Customer')
    action = db.Column(db.Enum(Actions))


class CustomerConfiguration(BaseModel):
    customer_id = db.Column(db.ForeignKey('customer.id'))
    customer = relationship('Customer')
    configuration = db.Column(db.JSON)


class CustomerProfile(BaseModel):
    customer_id = db.Column(db.ForeignKey('customer.id'))
    customer = relationship('Customer')
