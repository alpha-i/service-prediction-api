import logging

from flask import Blueprint, jsonify, url_for, g, request, abort

from app import services
from app.core.auth import requires_access_token
from app.core.content import ApiResponse
from app.core.schemas import PredictionRequestSchema
from app.core.utils import parse_request_data
from app.entities import TaskStatusTypes
from app.tasks.predict import training_and_prediction_task, prediction_failure

predict_blueprint = Blueprint('prediction', __name__)


@predict_blueprint.route('/', methods=['POST'])
@requires_access_token
@parse_request_data
def submit():
    company_id = g.user.company.id

    # the user can only predict against the _latest_ datasource
    datasource_id = g.user.company.current_datasource.id
    prediction_request, errors = PredictionRequestSchema().load(g.json)
    if errors:
        return jsonify(errors=errors), 400

    task_code = services.prediction.generate_task_code()
    logging.warning("Generated task code was %s", task_code)

    prediction_task = services.prediction.create_prediction_task(
        task_name=prediction_request['name'],
        task_code=task_code,
        company_id=company_id,
        datasource_id=datasource_id,
    )

    services.prediction.set_task_status(prediction_task, TaskStatusTypes.queued)
    upload_code = g.user.company.current_datasource.upload_code
    training_and_prediction_task.apply_async(
        (task_code, company_id, upload_code, prediction_request),
        link_error=prediction_failure.s()
    )

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        next=url_for('customer.dashboard'),
        context={
            'task_code': task_code,
            'task_status': url_for('prediction.get_single_task', task_code=task_code, _external=True),
            'result': url_for('prediction.result', task_code=task_code, _external=True)
        }
    )

    return response()


@predict_blueprint.route('/', methods=['GET'])
@requires_access_token
def get_tasks():
    return jsonify(g.user.company.prediction_tasks)


@predict_blueprint.route('/<string:task_code>', methods=['GET'])
@requires_access_token
@parse_request_data
def get_single_task(task_code):
    prediction_task = services.prediction.get_task_by_code(task_code)
    if not prediction_task:
        logging.debug(f"No task found for code {task_code}")
        abort(404, 'No task found!')
    if not prediction_task.company_id == g.user.company_id:
        abort(403)

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=prediction_task,
    )

    return response()


@predict_blueprint.route('/result', methods=['GET'])
@requires_access_token
@parse_request_data
def get_results():
    return jsonify(g.user.company.prediction_results)


@predict_blueprint.route('/result/<string:task_code>')
@requires_access_token
def result(task_code):
    """
    Get the result of an individual task
    """
    prediction_result = services.prediction.get_result_by_code(task_code)
    if not prediction_result:
        logging.debug(f"No result was found for task code {task_code}")
        abort(404, 'No result found!')

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=prediction_result
    )

    return response()
