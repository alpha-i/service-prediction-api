from datetime import timedelta

from flask import Blueprint, jsonify, render_template, g, request, abort

from app.core.auth import requires_access_token
from app.db import db
from app.models.customer import UserConfiguration
from app.models.datasource import DataSource
from app.models.prediction import PredictionTask

customer_blueprint = Blueprint('customer', __name__)


# TODO: get rid of me before committing
@customer_blueprint.route('/')
@requires_access_token
def get_user_profile():
    customer = g.user
    return jsonify(customer)


@customer_blueprint.route('/dashboard')
@requires_access_token
def dashboard():
    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.current_data_source,
        'task_list': list(reversed(g.user.tasks))[:5]
    }

    return render_template('dashboard.html', **context)


@customer_blueprint.route('/datasource')
@requires_access_token
def view_datasource():
    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'current_datasource': g.user.current_data_source,
        'datasource_history': g.user.data_sources
    }

    return render_template('datasource/index.html', **context)


@customer_blueprint.route('/new-prediction')
@requires_access_token
def new_prediction():
    min_date = g.user.current_data_source.end_date
    max_date = min_date + timedelta(days=30)

    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.current_data_source,
        'min_date': min_date,
        'max_date': max_date
    }

    return render_template('prediction/new.html', **context)


@customer_blueprint.route('/prediction/<string:task_code>')
@requires_access_token
def view_prediction(task_code):
    prediction = PredictionTask.get_by_task_code(task_code)
    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.current_data_source,
        'prediction': prediction
    }

    result = []
    ordered_feature_list = []
    if prediction.prediction_result:
        for prediction_element in prediction.prediction_result.result:
            features_in_prediction = {}
            for prediction_data in prediction_element['prediction']:
                features_in_prediction.update({
                    prediction_data['feature']: {
                        'lower': prediction_data['lower'],
                        'value': prediction_data['value'],
                        'upper': prediction_data['upper']
                    }
                })

            ordered_feature_list = sorted(features_in_prediction.keys())

            row = [
                prediction_element['timestamp'],
            ]

            for feature in ordered_feature_list:
                feature_data = features_in_prediction[feature]
                row += [[feature_data['lower'], feature_data['value'], feature_data['upper']]]

            result.append(row)

    header = ['timestamp'] + ordered_feature_list
    timestamp_list = [row[0] for row in result]
    timestamp_range = [timestamp_list[0], timestamp_list[-1]] if len(timestamp_list) > 0 else []
    context['formatted_result'] = {
        'data': result,
        'header': header,
        'features': ordered_feature_list,
        'timestamp_range': timestamp_range,
        'prediction_status': prediction.statuses[-1].state
    }

    return render_template('prediction/view.html', **context)


@customer_blueprint.route('/prediction')
@requires_access_token
def list_predictions():
    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.current_data_source,
        'task_list': list(reversed(g.user.tasks))
    }

    return render_template("prediction/list.html", **context)


# TODO: temporary view to show the uploads for this customer
@customer_blueprint.route('/uploads')
@requires_access_token
def list_customer_uploads():
    user_id = g.user.id
    uploads = DataSource.get_for_user(user_id)
    return jsonify(uploads)


# TODO: temporary view to show the customer tasks
@customer_blueprint.route('/tasks')
@requires_access_token
def list_customer_tasks():
    return jsonify(g.user.tasks)


@customer_blueprint.route('/results')
@requires_access_token
def list_customer_results():
    return jsonify(g.user.results)


@customer_blueprint.route('/configuration', methods=['POST'])
@requires_access_token
def update_customer_configuration():
    user = g.user
    assert request.is_json, abort(400)
    new_configuration = request.json  # TODO: needs to implement a schema!
    configuration_entity = user.configuration
    if not configuration_entity:
        configuration_entity = UserConfiguration(
            user_id=user.id
        )
    configuration_entity.configuration = new_configuration
    db.session.add(configuration_entity)
    db.session.add(user)  # TODO: needs to be decoupled!
    db.session.commit()  # maybe follow implement a repository/entity pattern
    return jsonify(user.configuration), 201

@customer_blueprint.route('/configuration', methods=['GET'])
@requires_access_token
def get_customer_configuration():
    return jsonify(g.user.configuration), 200
