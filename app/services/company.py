from app.core.entities import Company
from app.models import CompanyModel


def get_for_email(email):
    company = CompanyModel.get_for_email(email)
    return Company.from_model(company)


def get_for_domain(domain):
    company = CompanyModel.get_for_domain(domain)
    return Company.from_model(company)
