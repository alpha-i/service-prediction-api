import re

from attribdict import AttribDict
from marshmallow import Schema, fields, validates, ValidationError, pre_load
from marshmallow_enum import EnumField

from app.entities.customer import UserPermissions
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
    feature = fields.String(required=True)
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

    @property
    def dict_class(self):
        return AttribDict


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
    features = fields.List(fields.String)

    @pre_load
    def process_list_of_features(self, data):
        features_string_list = data.get('features')
        if not features_string_list:
            return
        data['features'] = features_string_list.split(', ')


class OracleConfigurationSchema(BaseModelSchema):
    scheduling = fields.Dict()
    oracle = fields.Dict()
    oracle_class = fields.String()
    calendar_name = fields.String()


class CompanyConfigurationSchema(BaseModelSchema):
    company_id = fields.Integer()
    configuration = fields.Nested(OracleConfigurationSchema, many=False)


class CompanySchema(BaseModelSchema):
    name = fields.String()
    domain = fields.String()
    data_sources = fields.Nested(DataSourceSchema, many=True, default=[])
    current_configuration = fields.Nested(CompanyConfigurationSchema, default=None, allow_none=True)

    @validates('domain')
    def validate_domain(self, value):
        if not re.match(r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$', value):
            raise ValidationError("Invalid domain name")


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
    statuses = fields.Nested(TaskStatusSchema, many=True, default=[])
    datasource = fields.Nested(DataSourceSchema)
    prediction_request = fields.Nested(PredictionRequestSchema, allow_none=True)


class UserSchema(BaseModelSchema):
    email = fields.Email()
    confirmed = fields.Boolean(allow_none=True)
    company_id = fields.Integer()
    company = fields.Nested(CompanySchema, many=False)
    current_data_source = fields.Nested(DataSourceSchema, allow_none=True)
    data_sources = fields.Nested(DataSourceSchema, many=True, default=[])
    tasks = fields.Nested(TaskSchema, many=True, default=[])
    results = fields.Nested(ResultSchema, many=True, default=[])
    actions = fields.Nested(CustomerActionSchema, many=True, default=[])
    permissions = EnumField(UserPermissions)


user_schema = UserSchema()
