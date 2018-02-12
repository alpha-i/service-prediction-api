import os
import uuid

from flask import Blueprint, request, current_app, jsonify

from app.core.auth import requires_access_token
from app.db import db
from app.models.files import FileUpload, FileTypes

upload_blueprint = Blueprint('upload', __name__)


@upload_blueprint.route('/<int:customer_id>', methods=['POST'])
@requires_access_token
def upload_file(customer_id):

    uploaded_file = request.files['upload']
    upload_code = str(uuid.uuid4())

    filename = FileUpload.generate_filename(upload_code, uploaded_file.filename)

    saved_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    uploaded_file.save(saved_path)

    upload = FileUpload(
        customer_id=customer_id,
        upload_code=upload_code,
        type=FileTypes.FILESYSTEM,
        location=saved_path,
        filename=filename
    )

    db.session.add(upload)
    db.session.commit()
    return jsonify(upload), 201
