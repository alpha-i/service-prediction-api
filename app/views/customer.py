import hashlib
from datetime import timedelta

import pandas as pd
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

    min_date = g.customer.current_data_source.end_date
    max_date = min_date + timedelta(days=15)

    context = {
        'user_id': g.customer.id,
        'profile': {'user_name': g.customer.username, 'email': 'changeme@soon.com'},
        'datasource': g.customer.current_data_source,
        'min_date': min_date,
        'max_date': max_date
    }

    return render_template('prediction/new.html', **context)


@customer_blueprint.route('/prediction/<string:prediction_code>')
@requires_access_token
def view_prediction(prediction_code):

    prediction = PredictionTask.get_by_task_code(prediction_code)
    context = {
        'user_id': g.customer.id,
        'profile': {'user_name': g.customer.username, 'email': 'changeme@soon.com'},
        'datasource': g.customer.current_data_source,
        'prediction': prediction
    }

    formatted_result = {
        'labels': [],
        'dataset': {}
    }
    feature_dict = {}
    for current_prediction in prediction.prediction_result.result:
        formatted_result['labels'].append(current_prediction['timestamp'])
        for single_prediction in current_prediction['prediction']:
            feature_name = single_prediction['feature']
            value = single_prediction['value']
            if not feature_dict.get(feature_name):
                feature_dict[feature_name] = {
                    'label': feature_name,
                    'data': [],
                    'border_color': hashlib.md5(feature_name.encode('utf-8')).hexdigest()[0:6]
                }
            else:
                feature_dict[feature_name]['data'].append(value)

    formatted_result['dataset'] = list(feature_dict.values())

    context['formatted_result'] = formatted_result

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
