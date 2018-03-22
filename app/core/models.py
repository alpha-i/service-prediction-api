import abc

import pandas as pd
from flask import json

from app.core.schemas import (
    UserSchema, CompanySchema, PredictionTaskSchema, DataSourceSchema,
    CompanyConfigurationSchema, PredictionTaskStatusSchema, TrainingTaskSchema,
    PredictionResultSchema)
from app.entities import (
    UserEntity, CompanyEntity, PredictionTaskEntity, PredictionResultEntity, DataSourceEntity,
    CompanyConfigurationEntity, PredictionTaskStatusEntity, TrainingTaskEntity
)
from app.entities.training import TrainingTaskStatusEntity
from config import HDF5_STORE_INDEX


class EntityCreationException(Exception):
    pass


class BaseModel(metaclass=abc.ABCMeta):
    SCHEMA = None
    MODEL = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def from_model(cls, model):
        if model is None:
            return None

        schema = cls.SCHEMA()
        data, errors = schema.loads(json.dumps(model.to_dict()))
        if errors:
            raise EntityCreationException(errors)

        entity = cls()
        setattr(entity, '_model', model)

        for key, value in data.items():
            setattr(entity, key, value)
        return entity

    @classmethod
    def from_models(cls, *models):
        return [BaseModel.from_model(model) for model in models]

    def to_model(self):
        model = self.MODEL()

        for key, value in self.__dict__.items():
            if value:
                setattr(model, key, value)
        return model

    def refresh(self):
        for key, value in self._model.to_dict().items():
            if not getattr(self, key, None):
                setattr(self, key, value)

    def load(self, **kwargs):
        return self.SCHEMA().load(kwargs)

    def dump(self):
        return self.SCHEMA().dumps(self)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.__dict__}>"


class User(BaseModel):
    SCHEMA = UserSchema
    MODEL = UserEntity


class Company(BaseModel):
    SCHEMA = CompanySchema
    MODEL = CompanyEntity


class PredictionTask(BaseModel):
    SCHEMA = PredictionTaskSchema
    MODEL = PredictionTaskEntity


class PredictionTaskStatus(BaseModel):
    SCHEMA = PredictionTaskStatusSchema
    MODEL = PredictionTaskStatusEntity


class DataSource(BaseModel):
    SCHEMA = DataSourceSchema
    MODEL = DataSourceEntity

    def get_file(self):
        with pd.HDFStore(self.location) as hdf_store:
            dataframe = hdf_store[HDF5_STORE_INDEX]
            return dataframe


class PredictionResult(BaseModel):
    SCHEMA = PredictionResultSchema
    MODEL = PredictionResultEntity


class CompanyConfiguration(BaseModel):
    SCHEMA = CompanyConfigurationSchema
    MODEL = CompanyConfigurationEntity


class TrainingTask(BaseModel):
    SCHEMA = TrainingTaskSchema
    MODEL = TrainingTaskEntity


class TrainingTaskStatus(BaseModel):
    SCHEMA = PredictionTaskStatusSchema
    MODEL = TrainingTaskStatusEntity
