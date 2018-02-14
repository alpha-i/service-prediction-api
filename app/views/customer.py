from flask import Blueprint, jsonify, render_template, g, request, abort

from app.core.auth import requires_access_token
from app.db import db
from app.models.customer import CustomerConfiguration
from app.models.datasource import DataSource
from app.models.prediction import PredictionTask

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
        'datasource': g.customer.current_data_source,
        'task_list': list(reversed(g.customer.tasks))[:5]
    }

    return render_template('dashboard.html', **context)


@customer_blueprint.route('/upload')
@requires_access_token
def upload():
    context = {
        'user_id': g.customer.id,
        'profile': {'user_name': g.customer.username, 'email': 'changeme@soon.com'},
        'current_datasource': g.customer.current_data_source
    }

    return render_template('datasource_upload.html', **context)


@customer_blueprint.route('/new-prediction')
@requires_access_token
def new_prediction():

    context = {
        'user_id': g.customer.id,
        'profile': {'user_name': g.customer.username, 'email': 'changeme@soon.com'},
        'datasource': g.customer.current_data_source
    }

    return render_template('prediction/new.html', **context)


@customer_blueprint.route('/prediction/<string:prediction_code>')
@requires_access_token
def view_prediction(prediction_code):

    context = {
        'user_id': g.customer.id,
        'profile': {'user_name': g.customer.username, 'email': 'changeme@soon.com'},
        'datasource': g.customer.current_data_source,
        'prediction': PredictionTask.get_by_task_code(prediction_code)
    }

    return render_template('prediction/view.html', **context)


@customer_blueprint.route('/prediction')
@requires_access_token
def list_predictions():

    context = {
        'user_id': g.customer.id,
        'profile': {'user_name': g.customer.username, 'email': 'changeme@soon.com'},
        'datasource': g.customer.current_data_source,
        'task_list': list(reversed(g.customer.tasks))
    }

    return render_template("prediction/list.html", **context)


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


@customer_blueprint.route('/configuration', methods=['GET', 'POST'])
@requires_access_token
def customer_configuration():
    customer = g.customer
    if request.method == 'GET':
        return jsonify(customer.configuration), 200
    assert request.is_json, abort(400)
    new_configuration = request.json  # TODO: needs to implement a schema!
    configuration_entity = customer.configuration
    if not configuration_entity:
        configuration_entity = CustomerConfiguration(
            customer_id=customer.id
        )
    configuration_entity.configuration = new_configuration
    db.session.add(configuration_entity)
    db.session.add(customer)  # TODO: needs to be decoupled!
    db.session.commit()  # maybe follow implement a repository/entity pattern
    return jsonify(customer.configuration), 201
