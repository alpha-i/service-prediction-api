import logging
import os
import uuid

import pandas as pd
from flask import Blueprint, request, abort, current_app, url_for, g

from app.core.auth import requires_access_token
from app.core.content import ApiResponse
from app.db import db
from app.models.datasource import DataSource, UploadTypes

datasource_blueprint = Blueprint('datasource', __name__)


def allowed_extension(filename):
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config['ALLOWED_EXTENSIONS']


def generate_upload_code():
    return str(uuid.uuid4())


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
    datasource = DataSource.get_by_upload_code(datasource_id)
    if not datasource:
        abort(404)

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=datasource
    )

    return response()

@datasource_blueprint.route('/upload', methods=['POST'])
@requires_access_token
def upload():
    user = g.user
    user_id = user.id
    uploaded_file = request.files['upload']
    if not allowed_extension(uploaded_file.filename):
        abort(400)

    upload_code = generate_upload_code()

    filename = DataSource.generate_filename(upload_code, uploaded_file.filename)

    data_frame = pd.read_csv(uploaded_file, sep=',', index_col='date', parse_dates=True)

    if user.current_data_source:
        logging.warning('User already has a data source')
        existing_data_frame = user.current_data_source.get_file()
        data_frame = pd.concat([existing_data_frame, data_frame])

    saved_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename + '.hdf5')
    data_frame.to_hdf(saved_path, key=current_app.config['HDF5_STORE_INDEX'])

    upload = DataSource(
        user_id=user_id,
        upload_code=upload_code,
        type=UploadTypes.FILESYSTEM,
        location=saved_path,
        filename=filename,
        start_date=data_frame.index[0].to_pydatetime(),
        end_date=data_frame.index[-1].to_pydatetime()
    )

    db.session.add(upload)
    db.session.commit()

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=upload,
        next=url_for('customer.view_datasource')
    )

    return response()