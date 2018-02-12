import datetime
import logging

from flask import Blueprint, request, abort, jsonify, g, redirect

from app.core.auth import requires_access_token
from app.db import db
from app.models.customer import Customer
from config import TOKEN_EXPIRATION

authentication_blueprint = Blueprint('authentication', __name__)

logging.getLogger(__name__).addHandler(logging.NullHandler())


@authentication_blueprint.route('/register', methods=['POST'])
def register_new_user():
    if not request.content_type == 'application/json':
        abort(400)
    username = request.json.get('username')
    password = request.json.get('password')

    assert username and password, abort(400)

    customer = Customer.get_customer_by_username(username)
    if customer is not None:
        abort(400)

    customer = Customer(username=username)

    customer.hash_password(password)

    db.session.add(customer)
    db.session.commit()

    return jsonify(
        {'username': customer.username, 'userid': customer.id}), 201


@authentication_blueprint.route('/customer')
@requires_access_token
def get_customer():
    return jsonify(g.customer)


@authentication_blueprint.route('/login', methods=['POST'])
def get_new_token():

    allowed_request_content = ['application/x-www-form-urlencoded', 'application/json']
    assert request.content_type in allowed_request_content, abort(400)

    is_form_request = True if request.content_type == allowed_request_content[0] else False
    is_json_request = True if request.content_type == allowed_request_content[1] else False

    if is_form_request:
        username = request.form.get('username')
        password = request.form.get('password')
    elif is_json_request:
        username = request.json.get('username')
        password = request.json.get('password')

    customer = Customer.get_customer_by_username(username)  # type: Customer
    if not customer:
        abort(401)

    if not customer.verify_password(password):
        abort(401)

    token = customer.generate_auth_token(expiration=TOKEN_EXPIRATION)
    ascii_token = token.decode('ascii')

    if is_form_request:
        response = redirect(url_for('customer.dashboard'))
    else :
        response = jsonify({'token': ascii_token})

    response.set_cookie(
        'token', ascii_token,
        expires=datetime.datetime.now() + datetime.timedelta(minutes=TOKEN_EXPIRATION)
    )

    return response

