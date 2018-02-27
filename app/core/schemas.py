import re

from marshmallow import Schema, fields, validates, ValidationError


class DataPointSchema(Schema):
    feature = fields.String()
    value = fields.Float()
    confidence = fields.Float()


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
    id = fields.Integer()
    created_at = fields.DateTime()
    last_update = fields.DateTime()


class DataSourceSchema(BaseModelSchema):
    upload_code = fields.String()
    type = fields.String()
    location = fields.String()
    filename = fields.String()
    start_date = fields.DateTime()
    end_date = fields.DateTime()


class CompanySchema(BaseModelSchema):
    name = fields.String()
    domain = fields.String()

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
    message = fields.String()


class ResultSchema(BaseModelSchema):
    task_code = fields.String()
    result = fields.Dict()


class TaskSchema(BaseModelSchema):
    name = fields.String()
    task_code = fields.String()


class UserSchema(BaseModelSchema):
    email = fields.Email()
    confirmed = fields.Boolean(allow_none=True)
    company = fields.Nested(CompanySchema, many=False)


user_schema = UserSchema()
