import logging
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
    name = db.Column(db.String, nullable=False)
    logo = db.Column(db.String)
    domain = db.Column(db.String, nullable=False)
    profile = db.Column(db.JSON)

    user_id = db.Column(db.ForeignKey('user.id'))
    users = relationship('User', back_populates='company')

    @staticmethod
    def get_for_email(email):
        domain = email.split('@')[-1]
        try:
            logging.info('Searching for a company %s', domain)
            company = Company.query.filter(Company.domain==domain).one()
        except NoResultFound:
            return None
        return company



class User(BaseModel):
    email = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    tasks = relationship('PredictionTask', back_populates='user')
    results = relationship('PredictionResult', back_populates='user')
    data_sources = relationship('DataSource', back_populates='user')
    actions = relationship('CustomerAction', back_populates='user')
    configuration = relationship('UserConfiguration', back_populates='user', uselist=False)
    company = relationship('Company')
    profile = relationship('UserProfile', uselist=False)

    confirmed = db.Column(db.Boolean, default=False)

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

        user = User.query.get(data['id'])
        return user

    @staticmethod
    def get_user_by_email(email):
        try:
            return User.query.filter(User.email == email).one()
        except NoResultFound:
            return None

    def to_dict(self):
        dictionary = super(User, self).to_dict()
        dictionary['data_sources'] = self.data_sources
        dictionary['current_data_source'] = self.current_data_source
        dictionary['configuration'] = getattr(self.configuration, 'configuration', None)
        dictionary['actions'] = self.actions
        return dictionary


class CustomerAction(BaseModel):
    user_id = db.Column(db.ForeignKey('user.id'))
    user = relationship('User')
    action = db.Column(db.Enum(Actions))


class UserConfiguration(BaseModel):
    user_id = db.Column(db.ForeignKey('user.id'))
    user = relationship('User')
    configuration = db.Column(db.JSON)


class UserProfile(BaseModel):
    user_id = db.Column(db.ForeignKey('user.id'))
    user = relationship('User')
