from app.core.schemas import UserSchema, CompanySchema, TaskSchema, ResultSchema, DataSourceSchema
from app.models import (
    User as UserModel, Company as CompanyModel, PredictionTask as PredictionTaskModel,
    PredictionResult as PredictionResultModel, DataSource as DataSourceModel
)

class EntityCreationException(Exception):
    pass


class Entity:
    SCHEMA = None
    MODEL = None

    @classmethod
    def from_model(cls, model):
        entity = cls()
        schema = cls.SCHEMA()
        errors = schema.validate(model.to_dict())
        if errors:
            raise EntityCreationException()
        for key, value in model.to_dict().items():
            setattr(entity, key, value)
        return entity

    @classmethod
    def from_models(cls, *models):
        return [Entity.from_model(model) for model in models]

    def to_model(self):
        model = self.MODEL
        for key, value in self.__dict__.items():
            if value:
                setattr(model, key, value)
        return model

    def load(self, **kwargs):
        return self.SCHEMA().load(kwargs)

    def dump(self):
        return self.SCHEMA().dumps(self)

    def __repr__(self):
        return f"<{self.MODEL.__name__}: {self.__dict__}>"


class User(Entity):
    SCHEMA = UserSchema
    MODEL = UserModel


class Company(Entity):
    SCHEMA = CompanySchema
    MODEL = CompanyModel


class Task(Entity):
    SCHEMA = TaskSchema
    MODEL = PredictionTaskModel


class DataSource(Entity):
    SCHEMA = DataSourceSchema
    MODEL = DataSourceModel


class Result(Entity):
    SCHEMA = ResultSchema
    MODEL = PredictionResultModel
