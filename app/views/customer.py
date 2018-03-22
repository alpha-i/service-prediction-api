import logging
from datetime import timedelta

import os
import pandas as pd
from flask import Blueprint, jsonify, render_template, g, request, abort, Response, flash, redirect, url_for, \
    current_app
from werkzeug.utils import secure_filename

from app import services, ApiResponse
from app.core.auth import requires_access_token
from app.core.models import DataSource
from app.core.schemas import UserSchema
from app.core.utils import redirect_url, handle_error, allowed_extension, generate_upload_code
from app.db import db
from app.entities import CompanyConfigurationEntity, DataSourceEntity, PredictionTaskEntity
from app.entities.datasource import UploadTypes
from app.interpreters.prediction import prediction_result_to_dataframe
from config import MAXIMUM_DAYS_FORECAST, DATETIME_FORMAT, DEFAULT_TIME_RESOLUTION


customer_blueprint = Blueprint('customer', __name__)


@customer_blueprint.route('/')
@requires_access_token
def get_user_profile():
    customer = g.user
    user = UserSchema().dump(customer).data
    return jsonify(user)


@customer_blueprint.route('/dashboard')
@requires_access_token
def dashboard():

    prediction_tasks = g.user.company.prediction_tasks if g.user.company.prediction_tasks else []
    training_tasks = g.user.company.training_tasks if g.user.company.training_tasks else []
    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.current_data_source,
        'prediction_task_list': list(reversed(prediction_tasks))[:5],
        'training_task_list': list(reversed(training_tasks))[:5]
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


@customer_blueprint.route('/datasource/template')
@requires_access_token
def get_company_datasource_template():
    csv_interpreter = services.company.get_datasource_interpreter(g.user.company.current_configuration)
    columns = [csv_interpreter.INDEX_COLUMN] + csv_interpreter.COLUMNS

    return Response(
        pd.DataFrame(columns=columns).to_csv(header=True, index=False),
        mimetype='text/csv',
        headers={"Content-disposition": f"attachment; filename={g.user.company.name}_template.csv"}
    )


@customer_blueprint.route('/datasource/<string:datasource_id>', methods=['GET'])
@requires_access_token
def view_datasource(datasource_id):
    datasource = services.datasource.get_by_upload_code(upload_code=datasource_id)
    result_dataframe = services.datasource.get_dataframe(datasource)

    target_feature = g.user.company.current_configuration.configuration.target_feature
    data_source = {
        'content': repr(result_dataframe[target_feature].to_csv(header=False)),
        'header': ['timestamp', target_feature],
        'timestamp_range': [
            result_dataframe.index[0].strftime(DATETIME_FORMAT),
            result_dataframe.index[-1].strftime(DATETIME_FORMAT)
        ],
        'target_feature': target_feature,
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
        logging.debug(
            f"Asked to create a prediction when no data source was available for company {g.user.company.name}")
        message = "No data source available. <a href='{}'>Upload one</a> first!".format(
            url_for('customer.list_datasources'))
        return handle_error(request, 400, message)

    datasource_min_date = g.user.current_data_source.end_date
    max_date = datasource_min_date + timedelta(days=MAXIMUM_DAYS_FORECAST)

    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.current_data_source,
        'datasource_end_date': datasource_min_date,
        'target_feature': g.user.company.current_configuration.configuration.target_feature,
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
        logging.debug(f"No result for task code {task_code}")
        abort(404, f'Task {task_code} has no result')

    latest_date_in_datasource = g.user.current_data_source.end_date.date()
    latest_date_in_results = result_dataframe.index[-1].date()

    headers = list(result_dataframe.columns)
    target_feature = g.user.company.current_configuration.configuration.target_feature

    if latest_date_in_datasource > latest_date_in_results:

        actuals_dataframe = services.datasource.get_dataframe(g.user.current_data_source)
        actuals_dataframe.index = actuals_dataframe.index.tz_localize('UTC')
        actuals_dataframe = actuals_dataframe.resample(DEFAULT_TIME_RESOLUTION).sum()
        result_dataframe['actuals'] = actuals_dataframe[target_feature]
        result_dataframe['actuals'] = result_dataframe['actuals'].transform(
            lambda x: "{:.2f};{:.2f};{:.2f}".format(x, x, x)
        )
        headers.append('actuals')

    context['result'] = {
        'data': repr(result_dataframe.to_csv(header=False)),
        'header': ['timestamp'] + headers,
        'target_feature': target_feature,
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
    prediction_tasks = g.user.company.prediction_tasks if g.user.company.prediction_tasks else []

    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.current_data_source,
        'prediction_task_list': list(reversed(prediction_tasks))
    }

    return render_template("prediction/list.html", **context)


@customer_blueprint.route('/datasource/upload', methods=['POST'])
@requires_access_token
def datasource_upload():
    user = g.user
    if not len(request.files):
        logging.debug("No file was uploaded")
        handle_error(request, 400, "No file Provided!")

    uploaded_file = request.files['upload']

    if not allowed_extension(uploaded_file.filename):
        logging.debug(f"Invalid extension for upload {uploaded_file.filename}")
        return handle_error(request, 400, f'File extension for {uploaded_file.filename} not allowed!')

    interpreter = services.company.get_datasource_interpreter(user.company.current_configuration)
    uploaded_dataframe, errors = interpreter.from_csv_to_dataframe(uploaded_file)
    target_feature = user.company.current_configuration.configuration.target_feature
    if errors:
        logging.debug(f"Invalid file uploaded: {', '.join(errors)}")
        return handle_error(request, 400, ', '.join(errors))

    if target_feature not in list(uploaded_dataframe.columns):
        return handle_error(request, 400, f"Required feature {target_feature} not present in the file")

    upload_code = generate_upload_code()
    saved_path = os.path.join(current_app.config['TEMPORARY_CSV_FOLDER'], "{}.csv".format(upload_code))

    current_datasource_dataframe = pd.DataFrame()
    if user.current_data_source:
        data_source = services.datasource.get_by_upload_code(user.current_data_source.upload_code)
        current_datasource_dataframe = data_source._model.get_file()

    uploaded_dataframe.to_csv(saved_path)
    context = {
        'current_datasource_dataframe': current_datasource_dataframe,
        'uploaded_dataframe': uploaded_dataframe,
        'upload_code': upload_code
    }

    return render_template('datasource/confirm.html', **context)


@customer_blueprint.route('/datasource/confirm', methods=['POST'])
@requires_access_token
def datasource_confirm():
    user = g.user

    try:
        upload_code = request.form['upload_code']
    except KeyError as e:
        logging.error("Trying to confirm an upload for a non existent code {}".format(upload_code))
        flash("An error occurred while confirming the data source")
        return redirect(url_for('customer.list_datasources'), 400)

    csv_path = os.path.join(
        current_app.config['TEMPORARY_CSV_FOLDER'], "{}.csv".format(request.form.get('upload_code'))
    )
    csv_file = open(csv_path, 'r')
    interpreter = services.company.get_datasource_interpreter(g.user.company.current_configuration)
    uploaded_dataframe, errors = interpreter.from_csv_to_dataframe(csv_file)

    features = list(uploaded_dataframe.columns)

    if user.current_data_source:
        data_source = services.datasource.get_by_upload_code(user.current_data_source.upload_code)
        existing_data_frame = data_source._model.get_file()
        cumulative_dataframe = pd.concat([existing_data_frame, uploaded_dataframe])
    else:
        cumulative_dataframe = uploaded_dataframe

    saved_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_code + '.hdf5')
    cumulative_dataframe.to_hdf(saved_path, key=current_app.config['HDF5_STORE_INDEX'])

    original = True if len(user.company.data_sources) == 0 else False

    cumulative_dataframe = cumulative_dataframe.sort_index(ascending=True)

    target_feature = g.user.company.current_configuration.configuration.target_feature
    upload = DataSource(
        user_id=user.id,
        company_id=user.company_id,
        upload_code=upload_code,
        type=UploadTypes.FILESYSTEM,
        location=saved_path,
        filename=upload_code,
        start_date=cumulative_dataframe.index[0].to_pydatetime(),
        end_date=cumulative_dataframe.index[-1].to_pydatetime(),
        is_original=original,
        features=', '.join(features),
        target_feature=target_feature,
    )

    datasource = services.datasource.insert(upload)

    temporary_csv = os.path.join(current_app.config['TEMPORARY_CSV_FOLDER'], '{}.csv'.format(upload_code))
    try:
        os.remove(temporary_csv)
    except OSError as e:
        logging.warning("Trying to remove the original file {}.csv which doesn't exists".format(upload_code))

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=datasource,
        next=url_for('customer.list_datasources'),
        status_code=201
    )

    return response()


@customer_blueprint.route('/configuration', methods=['POST'])
@requires_access_token
def update_customer_configuration():
    user = g.user
    if not request.is_json:
        logging.debug("New company configuration wasn't uploaded via JSON")
        abort(400, "Invalid request format, must be json")
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
