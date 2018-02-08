from flask import Blueprint, jsonify, render_template

from app.models.files import FileUpload
from app.models.prediction import PredictionTask

customer_blueprint = Blueprint('customer', __name__)


# TODO: temporary view to show a html form
@customer_blueprint.route('/<string:customer_id>/upload')
def upload_view(customer_id):
    return render_template('upload.html', customer_id=customer_id)


# TODO: temporary view to show the uploads for this customer
@customer_blueprint.route('/<string:customer_id>/uploads')
def list_uploads(customer_id):
    uploads = FileUpload.get_for_customer(customer_id)
    return jsonify(uploads)


# TODO: temporary view to show the customer tasks
@customer_blueprint.route('/<string:customer_id>/tasks')
def get_customer_tasks(customer_id):
    """
    List all the tasks for a customer
    """
    tasks = PredictionTask.get_by_customer_id(customer_id)
    return jsonify(tasks)
