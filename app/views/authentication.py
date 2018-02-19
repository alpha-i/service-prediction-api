import datetime
import logging

from flask import Blueprint, abort, jsonify, g, url_for

from app.core.auth import requires_access_token
from app.core.utils import parse_request_data
from app.db import db
from app.models.customer import Customer
from config import TOKEN_EXPIRATION

authentication_blueprint = Blueprint('authentication', __name__)

logging.getLogger(__name__).addHandler(logging.NullHandler())


@authentication_blueprint.route('/register', methods=['POST'])
@parse_request_data
def register_new_user():
    email = g.json.get('email')
    password = g.json.get('password')

    assert email and password, abort(400)

    customer = Customer.get_customer_by_email(email)
    if customer is not None:
        abort(400)

    customer = Customer(email=email)

    customer.hash_password(password)

    db.session.add(customer)
    db.session.commit()

    return jsonify(
        {'email': customer.email, 'userid': customer.id}), 201


@authentication_blueprint.route('/customer')
@requires_access_token
def get_customer():
    return jsonify(g.customer)


@authentication_blueprint.route('/login', methods=['POST'])
@parse_request_data
def get_new_token():
    email = g.json.get('email')
    password = g.json.get('password')

    customer = Customer.get_customer_by_email(email)  # type: Customer
    if not customer:
        logging.warning("No customer found for %s", email)
        abort(401)

    if not customer.verify_password(password):
        logging.warning("Incorrect password for %s", email)
        abort(401)

    token = customer.generate_auth_token(expiration=TOKEN_EXPIRATION)
    ascii_token = token.decode('ascii')

    response = jsonify({'token': ascii_token})
    response.set_cookie(
        'token', ascii_token,
        expires=datetime.datetime.now() + datetime.timedelta(minutes=TOKEN_EXPIRATION)
    )
    response.headers['Location'] = url_for('customer.dashboard')

    return response, 303


@authentication_blueprint.route('/logout')
@requires_access_token
def logout():

    response = redirect(url_for('main.home'))
    response.set_cookie('token', '', expires=0)

    return response


