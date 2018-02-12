from functools import wraps

from flask import request, g, abort

from app.models.customer import Customer


def requires_access_token(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        elif 'token' in request.cookies:
            token = request.cookies.get('token')
        else:
            assert request.content_type == 'application/json'
            token = request.json.get('token')
        if not token:
            abort(401)
            return None

        customer = Customer.verify_auth_token(token)
        if not customer:
            abort(401)
        g.customer = customer
        return fn(*args, **kwargs)
    return wrapper
