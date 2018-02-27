from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer)

from app.core.entities import User
from app.models import UserModel
from config import SECRET_KEY


def generate_auth_token(user, expiration=3600):
    s = Serializer(SECRET_KEY, expires_in=expiration)
    return s.dumps({'id': user.id})


def verify_token(token):
    user = UserModel.verify_auth_token(token)
    return User.from_model(user)


def get_by_email(email):
    user = UserModel.get_user_by_email(email)
    return User.from_model(user)

def verify_password(user, password):
    return user._model.verify_password(password)
