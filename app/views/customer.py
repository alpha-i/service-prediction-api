import logging
import os
from datetime import timedelta, datetime

import pandas as pd
from flask import (
    Blueprint, jsonify, render_template, g, request, abort, Response,
    flash, redirect, url_for, current_app
)

from app import services, ApiResponse
from app.core.auth import requires_access_token
from app.core.models import DataSource
from app.core.utils import handle_error, allowed_extension, generate_upload_code
from app.entities import CompanyConfigurationEntity, PredictionTaskEntity
from app.entities.datasource import UploadTypes
from app.interpreters.prediction import (
    prediction_result_to_dataframe_with_error,
    calculate_average_factors_percentage,
    combine_average_and_symbols_sensitivities)
from config import MAXIMUM_DAYS_FORECAST, DATETIME_FORMAT, DEFAULT_TIME_RESOLUTION

customer_blueprint = Blueprint('customer', __name__)


@customer_blueprint.route('/dashboard')
@requires_access_token
def dashboard():
    company = g.user.company
    prediction_tasks = company.prediction_tasks
    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': company.current_datasource,
        'prediction_task_list': list(reversed(prediction_tasks))[:5],
    }

    return render_template('dashboard.html', **context)


@customer_blueprint.route('/datasource', methods=['GET'])
@requires_access_token
def list_datasources():
    company = g.user.company
    current_datasource = company.current_datasource
    prediction_task_list = getattr(current_datasource, 'prediction_task_list', [])

    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'current_datasource': current_datasource,
        'datasource_history': company.data_sources,
        'prediction_task_list': prediction_task_list
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
    if not datasource:
        return handle_error(404, "No such datasource!")
    if not datasource.company_id == g.user.company_id:
        return handle_error(403, "Unauthorised")
    context = {
        'current_datasource': datasource,
        'profile': {'email': g.user.email},
        'prediction_task_list': services.prediction.get_task_for_datasource_id(datasource.id)
    }

    return render_template('datasource/detail.html', **context)


@customer_blueprint.route('/prediction/new', methods=['GET'])
@requires_access_token
def new_prediction():
    company = g.user.company
    current_datasource = company.current_datasource
    if not current_datasource:
        logging.debug(
            f"Asked to create a prediction when no data source was available for company {g.user.company.name}")
        message = f"No data source available. <a href='{url_for('customer.list_datasources')}'>Upload one</a> first!"
        return handle_error(400, message)

    datasource_min_date = current_datasource.end_date
    max_date = datasource_min_date + timedelta(days=MAXIMUM_DAYS_FORECAST)

    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': current_datasource,
        'datasource_end_date': datasource_min_date,
        'target_feature': company.current_configuration.configuration.target_feature,
        'min_date': datasource_min_date + timedelta(days=1),
        'max_date': max_date
    }

    return render_template('prediction/new.html', **context)


@customer_blueprint.route('/prediction/<string:task_code>')
@requires_access_token
def view_prediction(task_code):
    prediction = services.prediction.get_task_by_code(task_code)
    if not prediction:
        return handle_error(404, "No prediction found!")
    if not prediction.company_id == g.user.company_id:
        return handle_error(403, "Unauthorised")

    datasource = services.datasource.get_by_upload_code(prediction.datasource_upload_code)
    prediction.datasource = datasource

    if prediction.is_completed:
        elapsed = prediction.statuses[-1].last_update - prediction.created_at
    else:
        elapsed = datetime.utcnow() - prediction.created_at

    minutes, seconds = divmod(elapsed.seconds + elapsed.days * 86400, 60)
    hours, minutes = divmod(minutes, 60)

    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.company.current_datasource,
        'prediction': prediction,
        'elapsed': f"{hours:02d}:{minutes:02d}:{seconds:02d}",
        'result': None
    }

    result_dataframe = prediction_result_to_dataframe_with_error(prediction)
    if result_dataframe is not None:

        latest_date_in_datasource = g.user.company.current_datasource.end_date.date()
        latest_date_in_results = result_dataframe.index[-1].date()

        headers = list(result_dataframe.columns)
        target_feature = g.user.company.current_configuration.configuration.target_feature

        if latest_date_in_datasource > latest_date_in_results:
            actuals_dataframe = services.datasource.get_dataframe(g.user.company.current_datasource)
            actuals_dataframe.index = actuals_dataframe.index.tz_localize('UTC')
            actuals_dataframe = actuals_dataframe.resample(DEFAULT_TIME_RESOLUTION).sum()
            result_dataframe['actuals'] = actuals_dataframe[target_feature]
            result_dataframe['actuals'] = result_dataframe['actuals'].transform(
                lambda x: "{:.2f};{:.2f};{:.2f}".format(x, x, x)
            )
            headers.append('actuals')

        factors = prediction.prediction_result.result['factors']

        percent_factors = calculate_average_factors_percentage(factors)

        context['result'] = {
            'data': prediction.prediction_result.result['datapoints'][0]['prediction'],
            'header': headers,
            'target_feature': target_feature,
            'timestamp_range': [
                result_dataframe.index[0].strftime(DATETIME_FORMAT),
                result_dataframe.index[-1].strftime(DATETIME_FORMAT)
            ],
            'status': prediction.statuses[-1].state,
            'prediction_result': prediction.prediction_result,
            "factors": percent_factors
        }

    return render_template('prediction/view.html', **context)


@customer_blueprint.route('/prediction/<string:task_code>/download')
@requires_access_token
def download_prediction_csv(task_code):
    prediction = PredictionTaskEntity.get_by_task_code(task_code)
    if not prediction:
        return handle_error(404, "No prediction found!")

    if not prediction.company_id == g.user.company_id:
        return handle_error(403, "Unauthorised")

    result_dataframe = prediction_result_to_dataframe_with_error(prediction)

    return Response(
        result_dataframe.to_csv(),
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename={}.csv".format(
            prediction.name
        )})


@customer_blueprint.route('/prediction/<string:task_code>/factors')
@requires_access_token
def download_prediction_factors(task_code):
    prediction = PredictionTaskEntity.get_by_task_code(task_code)
    if not prediction:
        return handle_error(404, "No prediction found!")

    if not prediction.company_id == g.user.company_id:
        return handle_error(403, "Unauthorised")

    factors = prediction.prediction_result.result['factors']
    prediction_factors = combine_average_and_symbols_sensitivities(factors)

    df = pd.DataFrame(prediction_factors)
    return Response(
        df.to_csv(index_label=['symbol']),
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename={}_sensitivities.csv".format(
            prediction.name
        )})


@customer_blueprint.route('/prediction', methods=['GET'])
@requires_access_token
def list_predictions():
    prediction_tasks = g.user.company.prediction_tasks if g.user.company.prediction_tasks else []

    context = {
        'user_id': g.user.id,
        'profile': {'email': g.user.email},
        'datasource': g.user.company.current_datasource,
        'prediction_task_list': list(reversed(prediction_tasks))
    }

    return render_template("prediction/list.html", **context)


@customer_blueprint.route('/datasource', methods=['POST'])
@requires_access_token
def datasource_upload():
    user = g.user
    company = user.company

    if not len(request.files):
        logging.debug("No file was uploaded")
        return handle_error(400, "No file Provided!")

    company_configuration = company.current_configuration
    uploaded_file = request.files['upload']

    if not company_configuration:
        uploaded_file.close()
        return handle_error(400, f"{company.name} cannot upload historical data yet, please contact support.")

    if not allowed_extension(uploaded_file.filename):
        logging.debug(f"Invalid extension for upload {uploaded_file.filename}")
        return handle_error(400, f'File extension for {uploaded_file.filename} not allowed!')

    interpreter = services.company.get_datasource_interpreter(company_configuration)
    uploaded_dataframe, errors = interpreter.from_csv_to_dataframe(uploaded_file)
    target_feature = company_configuration.configuration.target_feature
    if errors:
        logging.debug(f"Invalid file uploaded: {', '.join(errors)}")
        return handle_error(400, ', '.join(errors))

    if target_feature not in list(uploaded_dataframe.columns):
        return handle_error(400, f"Required feature {target_feature} not present in the file")

    upload_code = generate_upload_code()
    saved_path = os.path.join(current_app.config['TEMPORARY_CSV_FOLDER'], f"{upload_code}.csv")

    current_datasource_dataframe = pd.DataFrame()
    if user.company.current_datasource:
        data_source = services.datasource.get_by_upload_code(user.company.current_datasource.upload_code)
        current_datasource_dataframe = data_source._model.get_file()

    uploaded_dataframe.to_csv(saved_path)

    context = {
        'current_datasource_dataframe': current_datasource_dataframe.sort_index(ascending=True),
        'uploaded_dataframe': uploaded_dataframe.sort_index(ascending=True),
        'upload_code': upload_code,
        'company_configuration': company_configuration.configuration
    }

    return render_template('datasource/confirm.html', **context)


@customer_blueprint.route('/datasource/confirm', methods=['POST'])
@requires_access_token
def datasource_confirm():
    user = g.user
    company = user.company
    company_configuration = company.current_configuration

    try:
        upload_code = request.form['upload_code']
    except KeyError as e:
        logging.error(f"Trying to confirm an upload for a non existent code {upload_code}")
        flash("An error occurred while confirming the data source")
        return redirect(url_for('customer.list_datasources'), 400)

    csv_path = os.path.join(
        current_app.config['TEMPORARY_CSV_FOLDER'], f"{request.form.get('upload_code')}.csv"
    )
    csv_file = open(csv_path, 'r')
    interpreter = services.company.get_datasource_interpreter(company_configuration)
    uploaded_dataframe, errors = interpreter.from_csv_to_dataframe(csv_file)

    features = list(uploaded_dataframe.columns)

    if user.company.current_datasource:
        data_source = services.datasource.get_by_upload_code(user.company.current_datasource.upload_code)
        existing_data_frame = data_source._model.get_file()
        cumulative_dataframe = pd.concat([existing_data_frame, uploaded_dataframe])
    else:
        cumulative_dataframe = uploaded_dataframe

    saved_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_code + '.hdf5')
    cumulative_dataframe = cumulative_dataframe.reset_index()
    cumulative_dataframe = cumulative_dataframe.drop_duplicates()
    cumulative_dataframe = cumulative_dataframe.set_index(interpreter.INDEX_COLUMN)
    cumulative_dataframe.to_hdf(saved_path, key=current_app.config['HDF5_STORE_INDEX'])

    original = True if len(user.company.data_sources) == 0 else False

    cumulative_dataframe = cumulative_dataframe.sort_index(ascending=True)

    target_feature = company_configuration.configuration.target_feature
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
        logging.warning(
            f"Trying to remove the original file {upload_code}.csv which doesn't exists while confirming the datasource"
        )

    upload_strategy_class = company_configuration.configuration.upload_strategy
    upload_strategy = services.strategies.get_upload_strategy(upload_strategy_class)
    upload_strategy.run(datasource=datasource, company_configuration=company_configuration)

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=datasource,
        next=url_for('customer.list_datasources'),
        status_code=201
    )

    return response()


@customer_blueprint.route('/datasource/discard/<string:upload_code>')
@requires_access_token
def datasource_discard(upload_code):
    temporary_csv = os.path.join(current_app.config['TEMPORARY_CSV_FOLDER'], f'{upload_code}.csv')

    try:
        os.remove(temporary_csv)
    except OSError:
        logging.warning(
            f"trying to remove a non existent csv source {upload_code} user_id {g.user.id} company_id {g.user.company_id}"
        )

    return redirect(url_for('customer.list_datasources'))


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
            user_id=user.id,
            company_id=g.user.company_id
        )
    configuration_entity.update(configuration=new_configuration)
    return jsonify(user.configuration), 201


@customer_blueprint.route('/configuration', methods=['GET'])
@requires_access_token
def get_customer_configuration():
    return jsonify(g.user.configuration), 200
