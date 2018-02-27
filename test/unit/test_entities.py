import unittest

from app.core.entities import User as UserEntity
from app.models import User as UserModel


class TestEntities(unittest.TestCase):
    def test_entities_from_model(self):
        model = UserModel(email='gabriele@alese.it')
        entity = UserEntity.from_model(model)
        assert entity.email == model.email
