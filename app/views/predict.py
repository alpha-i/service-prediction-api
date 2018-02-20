import time

import pandas as pd
from flask import Blueprint, jsonify, url_for, g, Response, request, abort

from app.core.auth import requires_access_token
from app.core.interpreters import prediction_result_to_dataframe
from app.core.content import ApiResponse
from app.core.schemas import prediction_request_schema
from app.core.utils import parse_request_data
from app.models.prediction import PredictionTask, PredictionResult
from app.tasks.predict import predict_task, prediction_failure

predict_blueprint = Blueprint('predict', __name__)


@predict_blueprint.route('/', methods=['POST'])
@requires_access_token
@parse_request_data
def submit_prediction():
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
            'task_status': url_for('.get_task_status', task_code=celery_prediction_task.id, _external=True),
            'result': url_for('.get_task_result', task_code=celery_prediction_task.id, _external=True)
        }
    )

    return response()


@predict_blueprint.route('/status/<string:task_code>')
@requires_access_token
def get_task_status(task_code):
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


@predict_blueprint.route('/result/<string:task_code>')
@requires_access_token
def get_task_result(task_code):
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


@predict_blueprint.route('/result/<string:task_code>/csv')
@requires_access_token
def get_task_result_csv(task_code):

    prediction = PredictionTask.get_by_task_code(task_code)
    result_dataframe = prediction_result_to_dataframe(prediction)

    if isinstance(result_dataframe, pd.DataFrame):
        return Response(result_dataframe.to_csv(header=False), mimetype='text/plain')
    else:
        abort(404)


