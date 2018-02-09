from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
)
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models.base import BaseModel
from config import SECRET_KEY


class User(BaseModel):
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=3600):  # TODO: change this!
        s = Serializer(SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id})

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
    def get_user_by_username(username):
        try:
            return User.query.filter(User.username==username).one()
        except NoResultFound:
            return None
