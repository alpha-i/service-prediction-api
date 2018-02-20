from flask import Blueprint, g, abort, request

from app.core.auth import requires_access_token
from app.core.content import ApiResponse
from app.core.utils import parse_request_data
from app.db import db
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
