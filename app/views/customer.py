from datetime import timedelta

from flask import Blueprint, jsonify, render_template, g, request, abort, Response

from app import services
from app.core.auth import requires_access_token
from app.core.interpreters import prediction_result_to_dataframe
from app.core.schemas import user_schema
from app.db import db
from app.entities import CompanyConfigurationEntity, DataSourceEntity, PredictionTaskEntity
from config import MAXIMUM_DAYS_FORECAST, DATETIME_FORMAT, TARGET_FEATURE

customer_blueprint = Blueprint('customer', __name__)


# TODO: get rid of me before committing
@customer_blueprint.route('/')
@requires_access_token
def get_user_profile():
    customer = g.user
    user = user_schema.dump(customer).data
    return jsonify(user)


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
def list_datasources():
    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'current_datasource': g.user.current_data_source,
        'datasource_history': g.user.data_sources
    }

    return render_template('datasource/list.html', **context)


@customer_blueprint.route('/datasource/<string:datasource_id>', methods=['GET'])
@requires_access_token
def view_datasource(datasource_id):
    datasource = services.datasource.get_by_upload_code(datasource_id=datasource_id)
    result_dataframe = services.datasource.get_dataframe(datasource)

    data_source = {
        'content': repr(result_dataframe[TARGET_FEATURE].to_csv(header=False)),
        'header': ['timestamp', TARGET_FEATURE],
        'timestamp_range': [
            result_dataframe.index[0].strftime(DATETIME_FORMAT),
            result_dataframe.index[-1].strftime(DATETIME_FORMAT)
        ],
        'target_feature': TARGET_FEATURE,
    }
    context = {
        'current_datasource': datasource,
        'profile': {'email': g.user.email},
        'data': data_source
    }

    return render_template('datasource/detail.html', **context)


@customer_blueprint.route('/new-prediction')
@requires_access_token
def new_prediction():
    if not g.user.current_data_source:
        abort(400, "No data source available. Upload one first!")
    datasource_min_date = g.user.current_data_source.end_date
    max_date = datasource_min_date + timedelta(days=MAXIMUM_DAYS_FORECAST)

    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.current_data_source,
        'datasource_end_date': datasource_min_date,
        'target_feature': TARGET_FEATURE,
        'min_date': datasource_min_date + timedelta(days=1),
        'max_date': max_date
    }

    return render_template('prediction/new.html', **context)


@customer_blueprint.route('/prediction/<string:task_code>')
@requires_access_token
def view_prediction(task_code):
    prediction = PredictionTaskEntity.get_by_task_code(task_code)
    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.current_data_source,
        'prediction': prediction
    }

    result_dataframe = prediction_result_to_dataframe(prediction)
    if result_dataframe is None:
        abort(404, f'Task {task_code} has no result')

    latest_date_in_datasource = g.user.current_data_source.end_date.date()
    latest_date_in_results = result_dataframe.index[-1].date()

    headers = list(result_dataframe.columns)
    if latest_date_in_datasource > latest_date_in_results:
        actuals_dataframe = services.datasource.get_dataframe(g.user.current_data_source)
        actuals_dataframe.index = actuals_dataframe.index.tz_localize('UTC')

        actuals_dataframe = actuals_dataframe.resample('15T').sum().astype(object)

        result_dataframe['actuals'] = actuals_dataframe[TARGET_FEATURE]
        for timestamp in result_dataframe.index:
            actual_datapoint = result_dataframe.loc[timestamp]['actuals']
            result_dataframe.loc[timestamp]['actuals'] = "{:.2f};{:.2f};{:.2f}".format(actual_datapoint, actual_datapoint, actual_datapoint)
        headers.append('actuals')


    context['result'] = {
        'data': repr(result_dataframe.to_csv(header=False)),
        'header': ['timestamp'] + headers,
        'target_feature': TARGET_FEATURE,
        'timestamp_range': [
            result_dataframe.index[0].strftime(DATETIME_FORMAT),
            result_dataframe.index[-1].strftime(DATETIME_FORMAT)
        ],
        'status': prediction.statuses[-1].state
    }

    return render_template('prediction/view.html', **context)


@customer_blueprint.route('/prediction/<string:task_code>/download')
@requires_access_token
def download_prediction_csv(task_code):
    prediction = PredictionTaskEntity.get_by_task_code(task_code)
    result_dataframe = prediction_result_to_dataframe(prediction)

    return Response(
        result_dataframe.to_csv(),
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename={}.csv".format(
            prediction.task_code
        )})


@customer_blueprint.route('/use_case')
@requires_access_token
def view_company_use_case():
    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email}
    }

    return render_template('company/use_case.html', **context)


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
    uploads = DataSourceEntity.get_for_user(user_id)
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
        configuration_entity = CompanyConfigurationEntity(
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
