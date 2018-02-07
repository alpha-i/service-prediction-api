from marshmallow import Schema, fields


class NestedDict(fields.Nested):
    def __init__(self, nested, key, *args, **kwargs):
        super(NestedDict, self).__init__(nested, many=True, *args, **kwargs)
        self.key = key

    def _serialize(self, nested_obj, attr, obj):
        nested_list = super(NestedDict, self)._serialize(nested_obj, attr, obj)
        nested_dict = {item[self.key]: item for item in nested_list}
        return nested_dict

    def _deserialize(self, value, attr, data):
        raw_list = [item for key, item in value.items()]
        nested_list = super(NestedDict, self)._deserialize(raw_list, attr, data)
        return nested_list


class DataPointSchema(Schema):
    timestamp = fields.DateTime(required=True)
    value = fields.DateTime(required=True)
    confidence = fields.Float()


class PredictionRequestSchema(Schema):
    feature = fields.String(required=True)
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)


prediction_request_schema = PredictionRequestSchema()


class PredictionResultSchema(Schema):
    customer_id = fields.String(required=True)
    task_id = fields.UUID(required=True)
    feature = fields.String(required=True)
    prediction = NestedDict(DataPointSchema, key='timestamp')


prediction_result_schema = PredictionResultSchema()
