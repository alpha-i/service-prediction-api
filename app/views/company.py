from flask import Blueprint, g, abort, request

from app.core.auth import requires_access_token
from app.core.content import ApiResponse
from app.core.utils import parse_request_data, json_reload
from app.db import db
from app.models.customer import CompanyConfiguration
from app.models.customer import Company

company_blueprint = Blueprint('company', __name__)


@company_blueprint.route('/', methods=['GET'])
@requires_access_token
def show_current_company_info():
    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=g.user.company
    )
    return response()


@company_blueprint.route('/register', methods=['POST'])
@parse_request_data
def register():
    company_name = g.json.get('name')
    domain = g.json.get('domain')

    assert company_name and domain, abort(400)

    existing_company = Company.get_for_domain(domain)
    if existing_company:
        abort(400)

    company = Company(name=company_name, domain=domain)
    db.session.add(company)
    db.session.commit()

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=company,
        status_code=201
    )

    return response()


@company_blueprint.route('/configuration', methods=['GET'])
@requires_access_token
def current_configuration():
    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=g.user.company.current_configuration
    )

    return response()


@company_blueprint.route('/configuration/<int:id>')
@requires_access_token
def configuration_detail(id):
    configuration = CompanyConfiguration.get_by_id(id)
    if not configuration:
        abort(404)
    if configuration.company_id != g.user.company.id:
        abort(401)
    return ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=configuration
    )()


@company_blueprint.route('/configuration', methods=['POST'])
@requires_access_token
@parse_request_data
def configuration_update():
    configuration_request = g.json

    configuration = CompanyConfiguration(
        company_id=g.user.company_id,
        configuration=json_reload(configuration_request)
    )

    db.session.add(configuration)
    db.session.commit()

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=configuration.configuration,
        status_code=201
    )

    return response()
