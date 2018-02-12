from flask import Blueprint, jsonify, render_template, g

from app.core.auth import requires_access_token
from app.models.datasource import DataSource

customer_blueprint = Blueprint('customer', __name__)


# TODO: get rid of me before committing
@customer_blueprint.route('/')
@requires_access_token
def get_user_profile():
    customer = g.customer
    return jsonify(customer)


@customer_blueprint.route('/dashboard')
@requires_access_token
def dashboard():

    context = {
        'user_id': g.customer.id,
        'profile': {'user_name': g.customer.username, 'email': 'changeme@soon.com'},
        'datasource': g.customer.current_data_source
    }

    return render_template('dashboard.html', **context)

@customer_blueprint.route('/upload')
@requires_access_token
def upload():
    context = {
        'user_id': g.customer.id,
        'profile': {'user_name': g.customer.username, 'email': 'changeme@soon.com'},
        'file_uploaded': DataSource.get_for_customer(g.customer.id)
    }

    return render_template('datasource_upload.html', **context)

# TODO: temporary view to show the uploads for this customer
@customer_blueprint.route('/uploads')
@requires_access_token
def list_customer_uploads():
    customer_id = g.customer.id
    uploads = DataSource.get_for_customer(customer_id)
    return jsonify(uploads)


# TODO: temporary view to show the customer tasks
@customer_blueprint.route('/tasks')
@requires_access_token
def list_customer_tasks():
    return jsonify(g.customer.tasks)


@customer_blueprint.route('/results')
@requires_access_token
def list_customer_results():
    return jsonify(g.customer.results)
