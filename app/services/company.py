from app.core.models import Company, CompanyConfiguration
from app.core.utils import import_class
from app.entities import CompanyEntity, CompanyConfigurationEntity


def get_for_email(email):
    company = CompanyEntity.get_for_email(email)
    return Company.from_model(company)


def get_for_domain(domain):
    company = CompanyEntity.get_for_domain(domain)
    return Company.from_model(company)


def insert(company):
    model = company.to_model()
    model.save()
    return Company.from_model(model)


def get_configuration_for_company_id(id):
    model = CompanyConfigurationEntity.get_by_company_id(id)
    return CompanyConfiguration.from_model(model)


def insert_configuration(company_configuration):
    # TODO: generalise this
    model = company_configuration.to_model()
    model.save()
    return CompanyConfiguration.from_model(model)


def get_datasource_interpreter(company_configuration):
    from app.interpreters import datasource
    interpeter = getattr(datasource, company_configuration.configuration['datasource_interpreter'])
    return interpeter
