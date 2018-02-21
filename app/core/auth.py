import logging
from functools import wraps

from flask import request, g, abort
from itsdangerous import URLSafeTimedSerializer
from flask import request, g, abort, redirect, url_for

from app.models.customer import User
from config import SECRET_KEY


def requires_access_token(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = is_user_logged()

        if isinstance(user, User):
            g.user = user
            return fn(*args, **kwargs)
        elif request.content_type == 'application/json':
            abort(401)
        else:
            return redirect(url_for('main.login'))

    return wrapper


def is_user_logged():
    """
    Check if user is logged if the token exists and is valid

    :return customer|False:
    """
    if 'X-Token' in request.headers:
        token = request.headers['X-Token']
    elif 'token' in request.cookies:
        token = request.cookies.get('token')
    elif request.content_type == 'application/json':
        token = request.json.get('token')
    else:
        logging.info("No token provided!")
        return False

    user = User.verify_auth_token(token)
    if not user:
        return None
    return user


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email)


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, max_age=expiration)
    except:
        return False
    return email


def is_valid_email_for_company(email: str, company):
    company_domain = company.domain
    email_domain = email.split('@')[-1]
    return email_domain == company_domain
