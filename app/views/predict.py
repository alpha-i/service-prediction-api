from flask import Blueprint, jsonify, make_response, url_for, request, abort

from app.core.auth import requires_access_token
from app.core.schemas import prediction_request_schema
from app.models.prediction import PredictionTask, PredictionResult
from app.tasks.predict import predict_task, prediction_failure

predict_blueprint = Blueprint('predict', __name__)


@predict_blueprint.route('/<string:customer_id>/<string:upload_id>', methods=['POST'])
@requires_access_token
def predict(customer_id, upload_id):
    """
    Submit a prediction task for a customer
    """
    assert request.content_type == 'application/json', abort(400)
    prediction_request, errors = prediction_request_schema.load(request.json)
    if errors:
        return jsonify(errors=errors), 400

    prediction_task = predict_task.apply_async(
        (customer_id, upload_id, prediction_request),
        link_error=prediction_failure.s()
    )
    return jsonify({
        'task_id': prediction_task.id,
        'task_status': url_for('.get_task_status', task_id=prediction_task.id, _external=True),
        'result': url_for('.get_result', task_id=prediction_task.id, _external=True)
    }), 202


@predict_blueprint.route('/status/<string:task_id>')
@requires_access_token
def get_task_status(task_id):
    """
    Get the status of a particular task
    """
    prediction_task = PredictionTask.get_by_task_id(task_id)
    if prediction_task:
        return jsonify(prediction_task)
    else:
        return make_response("Task not found!"), 404


@predict_blueprint.route('/result/<string:task_id>')
@requires_access_token
def get_result(task_id):
    """
    Get the result of an individual task
    """
    prediction_result = PredictionResult.get_for_task(task_id)
    if not prediction_result:
        return make_response("Result not found!"), 404

    return jsonify({
        'customer_id': prediction_result.customer_id,
        'task_id': prediction_result.task_id,
        'result': prediction_result.result,
    })
