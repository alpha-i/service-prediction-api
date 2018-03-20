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


class DataPointsListSchema(Schema):
    timestamp = fields.DateTime(required=True)
    prediction = fields.Nested(DataPointSchema, many=True)


class PredictionResultResultSchema(Schema):
    factors = fields.Dict(allow_none=True)
    datapoints = fields.Nested(DataPointsListSchema, many=True, default=[])


class PredictionRequestSchema(Schema):
    name = fields.String(required=True)
    start_time = fields.Date(required=True)
    end_time = fields.Date(required=True)


class PredictionResultSchema(Schema):
    company_id = fields.Integer(required=True)
    prediction_task_id = fields.Integer(required=True)
    task_code = fields.UUID(required=True)
    result = fields.Nested(PredictionResultResultSchema)


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
    target_feature = fields.String()

    @pre_load
    def process_list_of_features(self, data):
        features_string_list = data.get('features')
        if not features_string_list:
            return
        data['features'] = features_string_list.split(', ')


class OracleConfigurationSchema(BaseModelSchema):
    scheduling = fields.Dict(required=True)
    oracle = fields.Dict(required=True)
    oracle_class = fields.String(required=True)
    calendar_name = fields.String(required=True)
    target_feature = fields.String(required=True)
    datasource_interpreter = fields.String(required=True)
    prediction_result_interpreter = fields.String(required=True)


class CompanyConfigurationSchema(BaseModelSchema):
    company_id = fields.Integer()
    configuration = fields.Nested(OracleConfigurationSchema, many=False)


class CustomerActionSchema(BaseModelSchema):
    action = fields.String()


class PredictionTaskStatusSchema(BaseModelSchema):
    state = fields.String()
    message = fields.String(allow_none=True)


class PredictionTaskSchema(BaseModelSchema):
    name = fields.String()
    company_id = fields.Integer()
    task_code = fields.String()
    status = fields.String(allow_none=True)
    is_completed = fields.Boolean()
    statuses = fields.Nested(PredictionTaskStatusSchema, many=True, default=[])
    datasource = fields.Nested(DataSourceSchema)
    prediction_request = fields.Nested(PredictionRequestSchema, allow_none=True)


class CompanySchema(BaseModelSchema):
    name = fields.String()
    domain = fields.String()
    data_sources = fields.Nested(DataSourceSchema, many=True, default=[])
    current_configuration = fields.Nested(CompanyConfigurationSchema, default=None, allow_none=True)
    actions = fields.Nested(CustomerActionSchema, many=True, default=[])
    tasks = fields.Nested(PredictionTaskSchema, many=True, default=[])
    results = fields.Nested(PredictionResultSchema, many=True, default=[])

    @validates('domain')
    def validate_domain(self, value):
        if not re.match(r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$', value):
            raise ValidationError("Invalid domain name")


class UserProfileSchema(BaseModelSchema):
    pass


class UserSchema(BaseModelSchema):
    email = fields.Email()
    confirmed = fields.Boolean(allow_none=True)
    company_id = fields.Integer()
    company = fields.Nested(CompanySchema, many=False)
    current_data_source = fields.Nested(DataSourceSchema, allow_none=True)
    data_sources = fields.Nested(DataSourceSchema, many=True, default=[])
    permissions = EnumField(UserPermissions)


class TrainingTaskSchema(BaseModelSchema):
    task_code = fields.String()
    company_id = fields.Integer()
    datasource_id = fields.Integer()
    datasource = fields.Nested(DataSourceSchema)
    status = fields.String(allow_none=True)
    statuses = fields.Nested(PredictionTaskStatusSchema, many=True)
