import abc

from alphai_delphi.oracle import PredictionResult


class AbstractInterpreter(metaclass=abc.ABCMeta):

    MEAN_FORECAST_ATTRIBUTE = 'mean_vector'
    UPPER_BOUND_ATTRIBUTE = 'prediction_timestamp'
    LOWER_BOUND_ATTRIBUTE = 'covariance_matrix'

    def __init__(self, prediction_result):
        values = getattr(prediction_result, self.MEAN_FORECAST_ATTRIBUTE)

        # we'll discard these from now
        upper_bounds = getattr(prediction_result, self.UPPER_BOUND_ATTRIBUTE)
        lower_bounds = getattr(prediction_result, self.LOWER_BOUND_ATTRIBUTE)

        self._result = []
        for timestamp in values.index:
            datapoint = {}
            datapoint['timestamp'] = str(timestamp)
            datapoint['prediction'] = []
            for symbol in values.loc[timestamp].index:
                datapoint['prediction'].append(
                    {'feature': symbol,
                     'value': round(values.loc[timestamp][symbol], 2),
                     'upper': round(upper_bounds.loc[timestamp][symbol], 2),
                     'lower': round(lower_bounds.loc[timestamp][symbol], 2)
                     })
            self._result.append(datapoint)

    def __call__(self, *args, **kwargs):
        return self._result


class PredictionResultInterpreter(AbstractInterpreter):

    MEAN_VECTOR_ATTRIBUTE = 'mean_vector'
    UPPER_BOUND_ATTRIBUTE = 'prediction_timestamp'
    LOWER_BOUND_ATTRIBUTE = 'covariance_matrix'


class OraclePredictionInterpreter(AbstractInterpreter):
    MEAN_FORECAST_ATTRIBUTE = 'mean_forecast'
    UPPER_BOUND_ATTRIBUTE = 'upper_bound'
    LOWER_BOUND_ATTRIBUTE = 'lower_bound'


def prediction_interpreter(prediction_result):
    """
    We're in a stage where the oracle may output *two* different result classes:
    - Crocubot uses a PredictionResult(mean_vector, covariance_matrix, prediction_timestamp, target_timestamp)
    - Cromulon uses OraclePrediction(mean_forecast, lower_bound, upper_bound, current_timestamp)
    """
    if isinstance(prediction_result, PredictionResult):
        return PredictionResultInterpreter(prediction_result)()
    # elif isinstance(prediction_result, OraclePrediction):
    #     return OraclePredictionInterpreter(prediction_result)()
    else:
        raise ValueError("No interpreter available for %s", prediction_result.__class__.name)
