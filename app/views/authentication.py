from flask import Blueprint, request, abort, jsonify, url_for, g

from app.core.auth import requires_access_token
from app.db import db
from app.models.user import User

authentication_blueprint = Blueprint('authentication', __name__)


@authentication_blueprint.route('/register', methods=['POST'])
def register_new_user():
    assert request.content_type == 'application/json', abort(400)
    username = request.json.get('username')
    password = request.json.get('password')

    assert username and password, abort(400)

    user = User.get_user_by_username(username)
    if user is not None:
        abort(400)

    user = User(username=username)

    user.hash_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify(
        {'username': user.username}), 201, {'Location': url_for('.get_user', user_id=user.id, _external=True)}


@authentication_blueprint.route('/user')
@requires_access_token
def get_user():
    return jsonify(g.user)


@authentication_blueprint.route('/login', methods=['POST'])
def get_new_token():
    assert request.content_type == 'application/json', abort(400)
    username = request.json.get('username')
    password = request.json.get('password')

    user = User.get_user_by_username(username)  # type: User
    if not user:
        abort(401)

    if not user.verify_password(password):
        abort(401)

    token = user.generate_auth_token()

    return jsonify(
        {
            'token': token.decode('ascii')
        }
    )
