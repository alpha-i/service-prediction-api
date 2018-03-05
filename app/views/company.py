from flask import Blueprint, g, abort, request

from app import services
from app.core.auth import requires_access_token
from app.core.content import ApiResponse
from app.core.models import Company, CompanyConfiguration
from app.core.schemas import OracleConfigurationSchema
from app.core.utils import parse_request_data, json_reload

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

    assert company_name and domain, abort(400, 'Request error: please specify company name and company domain.')

    existing_company = services.company.get_for_domain(domain)
    if existing_company:
        abort(400, 'Unable to create existing company')

    company = Company(name=company_name, domain=domain)
    company = services.company.insert(company)

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
    configuration = services.company.get_configuration_for_id(id)
    if not configuration:
        abort(404, 'No such configuration found')
    if configuration.company_id != g.user.company.id:
        abort(401, 'Unauthorised')
    return ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=configuration
    )()


@company_blueprint.route('/configuration', methods=['POST'])
@requires_access_token
@parse_request_data
def configuration_update():
    configuration_request = g.json
    data, errors = OracleConfigurationSchema().load(configuration_request)
    if errors or not data:
        return abort(400, str(errors))

    configuration = CompanyConfiguration(
        company_id=g.user.company_id,
        configuration=json_reload(data)
    )

    configuration = services.company.insert_configuration(configuration)

    response = ApiResponse(
        content_type=request.accept_mimetypes.best,
        context=configuration.configuration,
        status_code=201
    )

    return response()
