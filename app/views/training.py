from flask import Blueprint, request, url_for, abort

from app import ApiResponse
from app import services
from app.core.auth import requires_admin_permissions
from app.core.utils import parse_request_data
from app.tasks.train import traing_task, training_failure

train_blueprint = Blueprint('training', __name__)


@train_blueprint.route('<string:task_code>', methods=['GET'])
@parse_request_data
def detail(task_code: str):
    training_task = services.training.get_for_task_code(task_code)
    if not training_task:
        abort(404)

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=training_task
    )

    return response()


@train_blueprint.route('<string:upload_code>', methods=['POST'])
@parse_request_data
@requires_admin_permissions
def new(upload_code: str):
    async_training_task = traing_task.apply_async(
        (upload_code,), link_error=training_failure.s()
    )

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        next=url_for('customer.dashboard'),
        context={
            'task_code': async_training_task.id
        },
        status_code=201
    )

    return response()
