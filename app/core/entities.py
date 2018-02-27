import abc

from app.core.schemas import UserSchema, CompanySchema, TaskSchema, ResultSchema, DataSourceSchema
from app.models import (
    UserModel as UserModel, CompanyModel as CompanyModel, PredictionTaskModel as PredictionTaskModel,
    PredictionResultModel as PredictionResultModel, DataSourceModel as DataSourceModel
)


class EntityCreationException(Exception):
    pass


class BaseEntity(metaclass=abc.ABCMeta):
    SCHEMA = None
    MODEL = None

    @classmethod
    def from_model(cls, model):
        if model is None:
            return None

        schema = cls.SCHEMA()
        data, errors = schema.dump(model.to_dict())

        if errors:
            raise EntityCreationException(errors)

        entity = cls()

        for key, value in data.items():
            setattr(entity, key, value)
        setattr(entity, '_model', model)
        return entity

    @classmethod
    def from_models(cls, *models):
        return [BaseEntity.from_model(model) for model in models]

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
        return f"<{self.__class__.__name__}: {self.__dict__}>"


class User(BaseEntity):
    SCHEMA = UserSchema
    MODEL = UserModel


class Company(BaseEntity):
    SCHEMA = CompanySchema
    MODEL = CompanyModel


class Task(BaseEntity):
    SCHEMA = TaskSchema
    MODEL = PredictionTaskModel


class DataSource(BaseEntity):
    SCHEMA = DataSourceSchema
    MODEL = DataSourceModel


class Result(BaseEntity):
    SCHEMA = ResultSchema
    MODEL = PredictionResultModel
