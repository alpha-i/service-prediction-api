import datetime

from flask import Blueprint, request, abort, jsonify, g

from app.core.auth import requires_access_token
from app.db import db
from app.models.customer import Customer
from config import TOKEN_EXPIRATION

authentication_blueprint = Blueprint('authentication', __name__)


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
    assert request.content_type == 'application/json', abort(400)
    username = request.json.get('username')
    password = request.json.get('password')

    customer = Customer.get_customer_by_username(username)  # type: Customer
    if not customer:
        abort(401)

    if not customer.verify_password(password):
        abort(401)

    token = customer.generate_auth_token(expiration=TOKEN_EXPIRATION)
    ascii_token = token.decode('ascii')

    response = jsonify({'token': ascii_token})
    response.set_cookie(
        'token', ascii_token,
        expires=datetime.datetime.now() + datetime.timedelta(minutes=TOKEN_EXPIRATION)
    )
    return response, 200
