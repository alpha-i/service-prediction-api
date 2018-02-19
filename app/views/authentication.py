import datetime
import logging

from flask import Blueprint, abort, g, url_for, request

from app.core.auth import requires_access_token
from app.core.content import ApiResponse
from app.core.utils import parse_request_data
from app.models.customer import User
from config import TOKEN_EXPIRATION

authentication_blueprint = Blueprint('authentication', __name__)


@authentication_blueprint.route('/login', methods=['POST'])
@parse_request_data
def login():
    email = g.json.get('email')
    password = g.json.get('password')

    user = User.get_user_by_email(email)  # type: User
    if not user:
        logging.warning("No user found for %s", email)
        abort(401)

    if not user.verify_password(password):
        logging.warning("Incorrect password for %s", email)
        abort(401)

    if not user.confirmed:
        logging.warning("User %s hasn't been confirmed!", user.email)
        abort(401)

    token = user.generate_auth_token(expiration=TOKEN_EXPIRATION)
    ascii_token = token.decode('ascii')

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        next=url_for('customer.dashboard'),
        context={'token': ascii_token}
    )

    response.set_cookie(
        'token', ascii_token,
        expires=datetime.datetime.now() + datetime.timedelta(minutes=TOKEN_EXPIRATION)
    )

    return response()


@authentication_blueprint.route('/logout')
@requires_access_token
def logout():
    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        next=url_for('main.login')
    )
    response.set_cookie('token', '', expires=0)

    return response()
