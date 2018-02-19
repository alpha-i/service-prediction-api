import logging
from functools import wraps

from flask import request, g, abort, redirect, url_for

from app.models.customer import Customer


def requires_access_token(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        customer = is_user_logged()

        if isinstance(customer, Customer):
            g.customer = customer
            return fn(*args, **kwargs)
        elif request.content_type == 'application/json':
            abort(401)
        else:
            return redirect(url_for('main.home'))

    return wrapper


def is_user_logged():
    """
    Check if user is logged if the token exists and is valid

    :return customer|False:
    """
    token = None
    if 'Authorization' in request.headers:
        token = request.headers['Authorization']
    elif 'token' in request.cookies:
        token = request.cookies.get('token')
    elif request.content_type == 'application/json':
        token = request.json.get('token')

    if not token:
        logging.info("No token provided!")
        return False

    customer = Customer.verify_auth_token(token)

    if not customer:
        return False

    return customer
