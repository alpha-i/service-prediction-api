from marshmallow import Schema, fields


class DataPointSchema(Schema):
    feature = fields.String()
    value = fields.Float()
    confidence = fields.Float()


class PredictionSchema(Schema):
    timestamp = fields.DateTime(required=True)
    prediction = fields.Nested(DataPointSchema, many=True)


class PredictionRequestSchema(Schema):
    features = fields.List(fields.String(), required=True)
    start_time = fields.Date(required=True)
    end_time = fields.Date(required=True)


prediction_request_schema = PredictionRequestSchema()


class PredictionResultSchema(Schema):
    customer_id = fields.String(required=True)
    task_code = fields.UUID(required=True)
    prediction = fields.Nested(PredictionSchema)


prediction_result_schema = PredictionResultSchema()
