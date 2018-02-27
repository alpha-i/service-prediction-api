import logging
from enum import Enum

from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
)
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models import BaseModel
from config import SECRET_KEY

class Actions(Enum):
    FILE_UPLOAD = 'FILE_UPLOAD'
    PREDICTION_STARTED = 'PREDICTION_STARTED'
    CONFIGURATION_UPDATE = 'CONFIGURATION_UPDATE'


class CompanyModel(BaseModel):
    __tablename__ = 'company'

    INCLUDE_ATTRIBUTES = ('current_configuration', 'data_sources')

    name = db.Column(db.String, nullable=False)
    logo = db.Column(db.String)
    domain = db.Column(db.String, nullable=False)
    profile = db.Column(db.JSON)
    configuration = relationship('CompanyConfigurationModel', back_populates='company')
    data_sources = relationship('DataSourceModel', back_populates='company')
    users = relationship('UserModel', back_populates='company')

    @staticmethod
    def get_for_email(email):
        domain = email.split('@')[-1]
        try:
            logging.info('Searching for a company %s', domain)
            company = CompanyModel.query.filter(CompanyModel.domain == domain).one()
        except NoResultFound:
            return None
        return company

    @staticmethod
    def get_for_domain(domain):
        try:
            company = CompanyModel.query.filter(CompanyModel.domain == domain).one()
        except NoResultFound:
            return None
        return company

    @property
    def current_configuration(self):
        if len(self.configuration):
            return self.configuration[-1]

    @property
    def current_data_source(self):
        if len(self.data_sources):
            return self.data_sources[-1]


class UserModel(BaseModel):
    __tablename__ = 'user'

    INCLUDE_ATTRIBUTES = ('data_sources', 'current_data_source', 'actions', 'company')
    EXCLUDE_ATTRIBUTES = ('password_hash',)

    email = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    tasks = relationship('PredictionTaskModel', back_populates='user')
    results = relationship('PredictionResultModel', back_populates='user')
    data_sources = relationship('DataSourceModel', back_populates='user')
    actions = relationship('CustomerActionModel', back_populates='user')
    company_id = db.Column(db.ForeignKey('company.id'), nullable=False)
    company = relationship('CompanyModel', foreign_keys=company_id)
    profile = relationship('UserProfileModel', uselist=False)

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
        if len(self.company.data_sources):
            return self.company.data_sources[-1]
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

        user = UserModel.query.get(data['id'])
        return user

    @staticmethod
    def get_user_by_email(email):
        try:
            return UserModel.query.filter(UserModel.email == email).one()
        except NoResultFound:
            return None


class CustomerActionModel(BaseModel):
    __tablename__ = 'customer_action'

    user_id = db.Column(db.ForeignKey('user.id'), nullable=False)
    user = relationship('UserModel', foreign_keys=user_id)
    action = db.Column(db.Enum(Actions))


class UserProfileModel(BaseModel):
    __tablename__ = 'user_profile'

    user_id = db.Column(db.ForeignKey('user.id'), nullable=False)
    user = relationship('UserModel', foreign_keys=user_id)


class CompanyConfigurationModel(BaseModel):
    __tablename__ = 'company_configuration'

    company_id = db.Column(db.ForeignKey('company.id'), nullable=False)
    company = relationship('CompanyModel', foreign_keys=company_id)
    configuration = db.Column(db.JSON)

    @staticmethod
    def get_by_id(id):
        try:
            configuration = CompanyConfigurationModel.query.filter(CompanyConfigurationModel.id == id).one()
        except NoResultFound:
            return None
        return configuration
