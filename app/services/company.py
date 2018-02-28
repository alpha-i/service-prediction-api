from app.core.entities import Company, CompanyConfiguration
from app.models import CompanyModel, CompanyConfigurationModel


def get_for_email(email):
    company = CompanyModel.get_for_email(email)
    return Company.from_model(company)


def get_for_domain(domain):
    company = CompanyModel.get_for_domain(domain)
    return Company.from_model(company)


def insert(company):
    model = company.to_model()
    model.save()
    return Company.from_model(model)


def get_configuration_for_id(id):
    model = CompanyConfigurationModel.get_by_id(id)
    return CompanyConfiguration.from_model(model)

def insert_configuration(company_configuration):
    # TODO: generalise this
    model = company_configuration.to_model()
    model.save()
    return CompanyConfiguration.from_model(model)
