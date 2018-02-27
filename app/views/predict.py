import time

from flask import Blueprint, jsonify, url_for, g, request, abort

from app.core.auth import requires_access_token
from app.core.content import ApiResponse
from app.core.schemas import prediction_request_schema
from app.core.utils import parse_request_data
from app.models.prediction import PredictionTask, PredictionResult
from app.tasks.predict import predict_task, prediction_failure

predict_blueprint = Blueprint('prediction', __name__)


@predict_blueprint.route('/', methods=['POST'])
@requires_access_token
@parse_request_data
def submit():
    """
    Submit a prediction task for a customer
    """

    user_id = g.user.id

    # the user can only predict against the _latest_ datasource
    upload_code = g.user.current_data_source.upload_code

    prediction_request, errors = prediction_request_schema.load(g.json)
    if errors:
        return jsonify(errors=errors), 400

    celery_prediction_task = predict_task.apply_async(
        (user_id, upload_code, prediction_request),
        link_error=prediction_failure.s()
    )

    time.sleep(1)  # wait for task status creation

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        next=url_for('customer.dashboard'),  # TODO: changeme, it should point to the status
        context={
            'task_code': celery_prediction_task.id,
            'task_status': url_for('prediction.status', task_code=celery_prediction_task.id, _external=True),
            'result': url_for('prediction.status', task_code=celery_prediction_task.id, _external=True)
        }
    )

    return response()


@predict_blueprint.route('/', methods=['GET'])
@requires_access_token
@parse_request_data
def get_tasks():
    return jsonify(g.user.tasks)


@predict_blueprint.route('/status/<string:task_code>')
@requires_access_token
def status(task_code):
    """
    Get the status of a particular task
    """
    prediction_task = PredictionTask.get_by_task_code(task_code)
    if not prediction_task:
        return abort(404)

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=prediction_task,
    )

    return response()


@predict_blueprint.route('/result', methods=['GET'])
@requires_access_token
@parse_request_data
def get_results():
    return jsonify(g.user.results)


@predict_blueprint.route('/result/<string:task_code>')
@requires_access_token
def result(task_code):
    """
    Get the result of an individual task
    """
    prediction_result = PredictionResult.get_for_task(task_code)
    if not prediction_result:
        abort(404)

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context={
            'user_id': prediction_result.user_id,
            'task_code': prediction_result.task_code,
            'result': prediction_result.result,
        })

    return response()
