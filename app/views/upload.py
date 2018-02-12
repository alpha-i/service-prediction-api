import os
import uuid

from flask import Blueprint, request, current_app, jsonify, g

from app.core.auth import requires_access_token
from app.db import db
from app.models.datasource import DataSource, UploadTypes

upload_blueprint = Blueprint('upload', __name__)


@upload_blueprint.route('/', methods=['POST'])
@requires_access_token
def upload_file():
    customer_id = g.customer.id
    uploaded_file = request.files['upload']
    upload_code = str(uuid.uuid4())
    filename = DataSource.generate_filename(upload_code, uploaded_file.filename)

    saved_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    uploaded_file.save(saved_path)

    upload = DataSource(
        customer_id=customer_id,
        upload_code=upload_code,
        type=UploadTypes.FILESYSTEM,
        location=saved_path,
        filename=filename
    )

    db.session.add(upload)
    db.session.commit()
    return jsonify(upload), 201
