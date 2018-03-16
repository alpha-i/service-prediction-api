import logging
import os

import pandas as pd
from flask import Blueprint, request, abort, current_app, url_for, g

from app import services
from app.core.auth import requires_access_token
from app.core.content import ApiResponse
from app.core.models import DataSource
from app.core.utils import allowed_extension, generate_upload_code
from app.entities.datasource import UploadTypes

datasource_blueprint = Blueprint('datasource', __name__)


@datasource_blueprint.route('/')
@requires_access_token
def list_datasources():
    datasources = g.user.data_sources
    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=datasources
    )
    return response()


@datasource_blueprint.route('/current')
@requires_access_token
def current():
    current_datasource = g.user.current_data_source
    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=current_datasource,
    )
    return response()


@datasource_blueprint.route('/<string:datasource_id>')
@requires_access_token
def get(datasource_id):
    datasource = services.datasource.get_by_upload_code(datasource_id)
    if not datasource:
        logging.debug(f"No datasource was found for id {datasource_id}")
        abort(404, 'No data source found!')

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=datasource
    )

    return response()


@datasource_blueprint.route('/upload', methods=['POST'])
@requires_access_token
def upload():
    user = g.user
    if not len(request.files):
        logging.debug("No file was uploaded")
        abort(400, "No file provided!")

    uploaded_file = request.files['upload']

    if not allowed_extension(uploaded_file.filename):
        logging.debug(f"Invalid extension for upload {uploaded_file.filename}")
        abort(400, f'File extension for {uploaded_file.filename} not allowed!')

    upload_code = generate_upload_code()
    filename = services.datasource.generate_filename(upload_code, uploaded_file.filename)

    interpreter = services.company.get_datasource_interpreter(g.user.company.current_configuration)
    target_feature = g.user.company.current_configuration.configuration.target_feature
    data_frame, errors = interpreter.from_csv_to_dataframe(uploaded_file)

    if not target_feature in list(data_frame.columns):
        abort(400, f"Required feature {target_feature} not in {uploaded_file.filename}")
    if errors:
        logging.debug(f"Invalid file uploaded: {errors}")
        abort(400, errors)

    features = list(data_frame.columns)

    if user.current_data_source:
        data_souce = services.datasource.get_by_upload_code(user.current_data_source.upload_code)
        existing_data_frame = data_souce._model.get_file()
        data_frame = pd.concat([existing_data_frame, data_frame])

    saved_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename + '.hdf5')
    data_frame.to_hdf(saved_path, key=current_app.config['HDF5_STORE_INDEX'])

    original = True if len(user.company.data_sources) == 0 else False

    upload = DataSource(
        user_id=user.id,
        company_id=user.company_id,
        upload_code=upload_code,
        type=UploadTypes.FILESYSTEM,
        location=saved_path,
        filename=filename,
        start_date=data_frame.index[0].to_pydatetime(),
        end_date=data_frame.index[-1].to_pydatetime(),
        is_original=original,
        features=', '.join(features),
        target_feature=target_feature,
    )

    datasource = services.datasource.insert(upload)

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=datasource,
        next=url_for('customer.list_datasources')
    )

    return response()


@datasource_blueprint.route('/delete/<string:datasource_id>', methods=['POST'])
@requires_access_token
def delete(datasource_id):
    datasource = services.datasource.get_by_upload_code(datasource_id)
    if datasource.is_original:
        logging.debug(f"Tried to delete original ingestion datasource: {datasource_id}")
        abort(400)

    services.datasource.delete(datasource)

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        next=url_for('customer.list_datasources'),
        status_code=200
    )

    return response()
