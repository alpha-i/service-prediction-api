import logging
from functools import wraps

from flask import request, g, abort, redirect, url_for

from app.core.models import User
from app.entities import UserEntity


def requires_access_token(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = is_user_logged()
        if isinstance(user, UserEntity):
            g.user = User.from_model(user)
            return fn(*args, **kwargs)
        elif request.content_type == 'application/json':
            abort(401, "Unauthorised")
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
        return None
    if not token:
        abort(401, 'Please supply authentication')

    user = UserEntity.verify_auth_token(token)
    return user


def is_valid_email_for_company(email: str, company):
    company_domain = company.domain
    email_domain = email.split('@')[-1]
    return email_domain == company_domain
