from flask import Blueprint, render_template

from app.views import USER_ID, USER_PROFILE

home_blueprint = Blueprint('main', __name__)


@home_blueprint.route('/')
def home():
    context = {
        'user_id': USER_ID,
        'profile': USER_PROFILE
    }
    return render_template('home.html', **context)


