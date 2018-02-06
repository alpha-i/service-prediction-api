from flask import Blueprint, jsonify, make_response

from app.models.prediction import PredictionTask, PredictionResult
from app.tasks.predict import predict_task

predict_blueprint = Blueprint('predict', __name__)


@predict_blueprint.route('/<int:customer_id>/')
def predict(customer_id):
    task = predict_task.delay(customer_id)
    return jsonify({
        'task_id': task.id
    })


@predict_blueprint.route('/status/<string:task_id>')
def get_task_status(task_id):
    task = PredictionTask.get_by_task_id(task_id)
    if task:
        return jsonify(task)
    else:
        return make_response("Task not found!"), 404


@predict_blueprint.route('/result/<string:task_id>')
def get_result(task_id):
    result = PredictionResult.get_for_task(task_id)
    if not result:
        return make_response("None found!"), 404
    return jsonify(result)
