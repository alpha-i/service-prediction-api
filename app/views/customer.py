from flask import Blueprint, jsonify, render_template, g

from app.core.auth import requires_access_token
from app.models.files import FileUpload
from app.models.prediction import PredictionTask

customer_blueprint = Blueprint('customer', __name__)


@customer_blueprint.route('/dashboard')
@requires_access_token
def dashboard():

    context = {
        'user_id': g.customer.id,
        'profile': {'user_name': g.customer.username, 'email': 'changeme@soon.com'},
        'file_uploaded': FileUpload.get_for_customer(g.customer.id)
    }

    return render_template('dashboard.html', **context)

# TODO: temporary view to show the uploads for this customer
@customer_blueprint.route('/<string:customer_id>/uploads')
@requires_access_token
def list_uploads(customer_id):
    uploads = FileUpload.get_for_customer(customer_id)
    return jsonify(uploads)


# TODO: temporary view to show the customer tasks
@customer_blueprint.route('/<string:customer_id>/tasks')
@requires_access_token
def get_customer_tasks(customer_id):
    """
    List all the tasks for a customer
    """
    tasks = PredictionTask.get_by_customer_id(customer_id)
    return jsonify(tasks)
