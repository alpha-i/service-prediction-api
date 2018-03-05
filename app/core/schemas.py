import re

from marshmallow import Schema, fields, validates, ValidationError
from marshmallow_enum import EnumField

from app.entities.datasource import UploadTypes


class DataPointSchema(Schema):
    feature = fields.String()
    value = fields.Float()
    lower = fields.Float()
    upper = fields.Float()


class PredictionSchema(Schema):
    timestamp = fields.DateTime(required=True)
    prediction = fields.Nested(DataPointSchema, many=True)


class PredictionRequestSchema(Schema):
    name = fields.String(required=True)
    features = fields.String(required=True)
    start_time = fields.Date(required=True)
    end_time = fields.Date(required=True)


prediction_request_schema = PredictionRequestSchema()


class PredictionResultSchema(Schema):
    user_id = fields.String(required=True)
    task_code = fields.UUID(required=True)
    prediction = fields.Nested(PredictionSchema)


prediction_result_schema = PredictionResultSchema()


class BaseModelSchema(Schema):
    id = fields.Integer(allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    last_update = fields.DateTime(allow_none=True)


class DataSourceSchema(BaseModelSchema):
    user_id = fields.Integer()
    company_id = fields.Integer()
    upload_code = fields.String()
    type = EnumField(UploadTypes)
    location = fields.String()
    filename = fields.String()
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    is_original = fields.Boolean(allow_none=True)


class CompanySchema(BaseModelSchema):
    name = fields.String()
    domain = fields.String()

    @validates('domain')
    def validate_domain(self, value):
        if not re.match(r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$', value):
            raise ValidationError("Invalid domain name")


class OracleConfigurationSchema(BaseModelSchema):
    scheduling = fields.Dict()
    oracle = fields.Dict()
    oracle_class = fields.String()


class CompanyConfigurationSchema(BaseModelSchema):
    company_id = fields.Integer()
    configuration = fields.Nested(OracleConfigurationSchema, many=False)


class CustomerActionSchema(BaseModelSchema):
    action = fields.String()


class UserProfileSchema(BaseModelSchema):
    pass


class TaskStatusSchema(BaseModelSchema):
    state = fields.String()
    message = fields.String(allow_none=True)


class ResultSchema(BaseModelSchema):
    user_id = fields.Integer()
    task_code = fields.String()
    result = fields.Nested(PredictionSchema, many=True)


class TaskSchema(BaseModelSchema):
    name = fields.String()
    user_id = fields.Integer()
    task_code = fields.String()
    status = fields.String(allow_none=True)
    is_completed = fields.Boolean()


class UserSchema(BaseModelSchema):
    email = fields.Email()
    confirmed = fields.Boolean(allow_none=True)
    company = fields.Nested(CompanySchema, many=False)


user_schema = UserSchema()
