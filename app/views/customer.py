from flask import Blueprint, jsonify
from app.models.prediction import PredictionTask


customer_blueprint = Blueprint('customer', __name__)


@customer_blueprint.route('/<int:customer_id>')
def get_customer_tasks(customer_id):
    """
    List all the tasks for a customer
    """
    tasks = PredictionTask.get_by_customer_id(customer_id)
    return jsonify(tasks)
