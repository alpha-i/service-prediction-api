import unittest

from app.core.entities import User
from app.models import UserModel, CompanyModel
from app import services


class TestEntities():
    def test_entities_from_model(self):
        model = UserModel(email='gabriele@alese.it', company=CompanyModel(name='ciao'))
        entity = User.from_model(model)
        assert entity.email == model.email
