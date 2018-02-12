from flask import Blueprint, render_template

home_blueprint = Blueprint('main', __name__)


@home_blueprint.route('/')
def home():
    return render_template('login.html')
