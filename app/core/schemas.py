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


#  NEW STUFF


class DataSourceSchema(Schema):
    upload_code = fields.String()
    type = fields.String()
    location = fields.String()
    filename = fields.String()
    start_date = fields.DateTime()
    end_date = fields.DateTime()


class CompanySchema(Schema):
    name = fields.String()
    domain = fields.String()

    @validates('domain')
    def validate_domain(self, value):
        if not re.match(r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$', value):
            raise ValidationError("Invalid domain name")


class CustomerActionSchema(Schema):
    action = fields.String()


class UserProfileSchema(Schema):
    pass


class TaskStatusSchema(Schema):
    state = fields.String()
    message = fields.String()


class ResultSchema(Schema):
    task_code = fields.String()
    result = fields.Dict()


class TaskSchema(Schema):
    name = fields.String()
    task_code = fields.String()


class UserSchema(Schema):
    email = fields.Email()
    confirmed = fields.Boolean(allow_none=True)


user_schema = UserSchema()
