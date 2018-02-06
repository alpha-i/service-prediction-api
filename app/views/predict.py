from flask import Blueprint, jsonify, make_response, url_for

from app.models.prediction import PredictionTask, PredictionResult
from app.tasks.predict import predict_task, prediction_failure

predict_blueprint = Blueprint('predict', __name__)


@predict_blueprint.route('/<string:customer_id>/<string:upload_id>')
def predict(customer_id, upload_id):
    """
    Submit a prediction task for a customer
    """
    task = predict_task.apply_async((customer_id, upload_id), link_error=prediction_failure.s())
    return jsonify({
        'task_id': task.id,
        'task_status': url_for('.get_task_status', task_id=task.id, _external=True),
        'result': url_for('.get_result', task_id=task.id, _external=True)
    }), 202


@predict_blueprint.route('/status/<string:task_id>')
def get_task_status(task_id):
    """
    Get the status of a particular task
    """
    task = PredictionTask.get_by_task_id(task_id)
    if task:
        return jsonify(task)
    else:
        return make_response("Task not found!"), 404


@predict_blueprint.route('/result/<string:task_id>')
def get_result(task_id):
    """
    Get the result of an individual task
    """
    result = PredictionResult.get_for_task(task_id)
    if not result:
        return make_response("None found!"), 404
    return jsonify(result)
