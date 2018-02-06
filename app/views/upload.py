import os
import uuid

from flask import Blueprint, request, current_app, jsonify

from app.db import db
from app.models.files import FileUpload, FileTypes

upload_blueprint = Blueprint('upload', __name__)


@upload_blueprint.route('/<int:customer_id>', methods=['POST'])
def upload_file(customer_id):
    upload_file = request.files['upload']

    upload_id = str(uuid.uuid4())
    filename = f"{upload_id}_{upload_file.filename}"
    saved_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    upload_file.save(saved_path)

    upload = FileUpload(
        customer_id=customer_id,
        upload_id=upload_id,
        type=FileTypes.FILESYSTEM,
        location=saved_path
    )
    db.session.add(upload)
    db.session.commit()
    return jsonify(upload), 201
