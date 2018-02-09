from functools import wraps

from flask import request, g, abort

from app.models.user import User


def requires_access_token(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # the token must be in the json body or in the authorization header
        # TODO: might have to check the cookies too, for the form?
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        else:
            assert request.content_type == 'application/json'
            token = request.json.get('token')
        if not token:
            abort(401)
            return None

        user = User.verify_auth_token(token)
        if not user:
            abort(401)
        g.user = user
        return fn(*args, **kwargs)
    return wrapper
