import logging

import time
from flask import Blueprint, jsonify, make_response, url_for, request, abort, g

from app.core.auth import requires_access_token
from app.core.schemas import prediction_request_schema
from app.core.utils import parse_request_data
from app.models.prediction import PredictionTask, PredictionResult
from app.tasks.predict import predict_task, prediction_failure

DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

predict_blueprint = Blueprint('predict', __name__)

logging.getLogger(__name__).addHandler(logging.NullHandler())

@predict_blueprint.route('/', methods=['POST'])
@requires_access_token
@parse_request_data
def predict():
    """
    Submit a prediction task for a customer
    """

    customer_id = g.customer.id

    # the user can only predict against the _latest_ datasource
    upload_code = g.customer.current_data_source.upload_code

    prediction_request, errors = prediction_request_schema.load(g.json)
    if errors:
        return jsonify(errors=errors), 400

    celery_prediction_task = predict_task.apply_async(
        (customer_id, upload_code, prediction_request),
        link_error=prediction_failure.s()
    )

    response = jsonify({
            'task_code': celery_prediction_task.id,
            'task_status': url_for('.get_task_status', task_code=celery_prediction_task.id, _external=True),
            'result': url_for('.get_task_result', task_code=celery_prediction_task.id, _external=True)
        })

    response.headers['Location'] = url_for('customer.dashboard')
    time.sleep(1)

    return response, 303

@predict_blueprint.route('/status/<string:task_code>')
@requires_access_token
def get_task_status(task_code):
    """
    Get the status of a particular task
    """
    prediction_task = PredictionTask.get_by_task_code(task_code)
    if prediction_task:
        return jsonify(prediction_task)
    else:
        return make_response("Task not found!"), 404


@predict_blueprint.route('/result/<string:task_code>')
@requires_access_token
def get_task_result(task_code):
    """
    Get the result of an individual task
    """
    prediction_result = PredictionResult.get_for_task(task_code)
    if not prediction_result:
        return make_response("Result not found!"), 404

    return jsonify({
        'customer_id': prediction_result.customer_id,
        'task_code': prediction_result.task_code,
        'result': prediction_result.result,
    })
