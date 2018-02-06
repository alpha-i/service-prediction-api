from marshmallow import Schema, fields


class PredictionRequestSchema(Schema):
    customer_id = fields.String(required=True)
    # more to follow


class PredictionResultSchema(Schema):
    customer_id = fields.String(required=True)
    task_id = fields.UUID(required=True)
    # more to follow
