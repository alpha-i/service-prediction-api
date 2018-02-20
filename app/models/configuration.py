from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models.base import BaseModel

# noinspection PyUnresolvedReferences
from app.models.customer import Company

class CompanyConfiguration(BaseModel):
    company_id = db.Column(db.ForeignKey('company.id'), nullable=False)
    company = relationship('Company')
    configuration = db.Column(db.JSON)

    @staticmethod
    def get_by_id(id):
        try:
            configuration = CompanyConfiguration.query.filter(CompanyConfiguration.id == id).one()
        except NoResultFound:
            return None
        return configuration
