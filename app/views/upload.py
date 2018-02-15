import logging
import os
import uuid

from flask import Blueprint, request, current_app, jsonify, g, abort, url_for
import pandas as pd

from app.core.auth import requires_access_token
from app.db import db
from app.models.customer import Customer
from app.models.datasource import DataSource, UploadTypes

upload_blueprint = Blueprint('upload', __name__)


def allowed_extension(filename):
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config['ALLOWED_EXTENSIONS']


def generate_upload_code():
    return str(uuid.uuid4())


@upload_blueprint.route('/', methods=['POST'])
@requires_access_token
def upload_file():
    customer = g.customer  # type: Customer
    customer_id = customer.id
    uploaded_file = request.files['upload']
    if not allowed_extension(uploaded_file.filename):
        abort(400)

    upload_code = generate_upload_code()

    filename = DataSource.generate_filename(upload_code, uploaded_file.filename)

    data_frame = pd.read_csv(uploaded_file, sep=',', index_col='date', parse_dates=True)

    if customer.current_data_source:
        logging.warning('User already has a data source')
        existing_data_frame = customer.current_data_source.get_file()
        data_frame = pd.concat([existing_data_frame, data_frame])

    saved_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename + '.hdf5')
    data_frame.to_hdf(saved_path, key=current_app.config['HDF5_STORE_INDEX'])

    upload = DataSource(
        customer_id=customer_id,
        upload_code=upload_code,
        type=UploadTypes.FILESYSTEM,
        location=saved_path,
        filename=filename,
        start_date=data_frame.index[0].to_pydatetime(),
        end_date=data_frame.index[-1].to_pydatetime()
    )

    db.session.add(upload)
    db.session.commit()
    response = jsonify(upload)
    response.headers['Location'] = url_for('customer.dashboard')
    return response, 303
