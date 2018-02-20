import datetime
import logging

from flask import Blueprint, abort, jsonify, g, url_for, redirect, make_response, request

from app.core.auth import requires_access_token, generate_confirmation_token, confirm_token, is_valid_email_for_company
from app.core.content import ApiResponse
from app.core.utils import parse_request_data
from app.db import db
from app.models.customer import User, Company
from config import TOKEN_EXPIRATION

authentication_blueprint = Blueprint('authentication', __name__)


@authentication_blueprint.route('/register-user', methods=['POST'])
@parse_request_data
def register_new_user():
    email = g.json.get('email')
    password = g.json.get('password')

    assert email and password, abort(400)

    company = Company.get_for_email(email)
    if not company:
        logging.warning("No company could be found for %s", email)
        abort(401)

    if not is_valid_email_for_company(email, company):
        logging.warning("Invalid email %s for company: %s", email, company.domain)
        abort(401)

    user = User.get_user_by_email(email)
    if user is not None:
        abort(400)

    user = User(email=email, confirmed=False, company_id=company.id)

    user.hash_password(password)

    db.session.add(user)
    db.session.commit()
    confirmation_token = generate_confirmation_token(user.email)
    logging.info("Confirmation token for %s: %s", user.email, confirmation_token)

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        next=url_for('main.login'),
        status_code=201,
        context={'email': user.email, 'id': user.id}
    )

    return response()


@authentication_blueprint.route('/register-company', methods=['POST'])
@parse_request_data
def register_new_company():
    company_name = g.json.get('name')
    domain = g.json.get('domain')

    assert company_name and domain, abort(400)

    existing_company = Company.get_for_domain(domain)
    if existing_company:
        abort(400)

    company = Company(name=company_name, domain=domain)
    db.session.add(company)
    db.session.commit()

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=company,
        status_code=201
    )

    return response()


@authentication_blueprint.route('/confirm/<string:token>')
def confirm_user_registration(token):
    email = confirm_token(token)
    if not email:
        abort(401)

    user = User.get_user_by_email(email)
    if user.confirmed:
        abort(400)
    user.confirmed = True
    db.session.add(user)
    db.session.commit()

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        next=url_for('main.login'),
        context=user,
    )


    return response()


@authentication_blueprint.route('/login', methods=['POST'])
@parse_request_data
def get_new_token():
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


