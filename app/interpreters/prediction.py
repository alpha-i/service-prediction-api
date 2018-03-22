import abc

import pandas as pd
from dateutil import parser

from app.core.utils import import_class, MissingFieldsStringFormatter


class AbstractPredictionResultInterpreter(metaclass=abc.ABCMeta):
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


class CrocubotResultInterpreter(AbstractPredictionResultInterpreter):
    MEAN_VECTOR_ATTRIBUTE = 'mean_vector'
    UPPER_BOUND_ATTRIBUTE = 'prediction_timestamp'
    LOWER_BOUND_ATTRIBUTE = 'covariance_matrix'


class CromulonResultInterpreter(AbstractPredictionResultInterpreter):
    MEAN_FORECAST_ATTRIBUTE = 'mean_forecast'
    UPPER_BOUND_ATTRIBUTE = 'upper_bound'
    LOWER_BOUND_ATTRIBUTE = 'lower_bound'


def get_prediction_interpreter(company_configuration):
    return import_class(company_configuration.configuration['prediction_result_interpreter'])


def prediction_interpreter(prediction_result):
    """
    We're in a stage where the oracle may output *two* different result classes:
    - Crocubot uses a PredictionResult(mean_vector, covariance_matrix, prediction_timestamp, target_timestamp)
    - Cromulon uses OraclePrediction(mean_forecast, lower_bound, upper_bound, current_timestamp)
    """
    if prediction_result.__class__.__name__ == 'PredictionResult':  # TODO: changeme!
        return CrocubotResultInterpreter(prediction_result)()
    elif prediction_result.__class__.__name__ == 'OraclePrediction':
        return CromulonResultInterpreter(prediction_result)()
    else:
        raise ValueError("No interpreter available for %s", prediction_result.__class__)


def prediction_result_to_dataframe(prediction):
    fmt = MissingFieldsStringFormatter(missing='N/A')
    result = []
    if prediction.prediction_result:
        for prediction_element in prediction.prediction_result.result['datapoints']:
            result_timestamp = parser.parse(prediction_element['timestamp'])

            result_row = {
                'timestamp': result_timestamp
            }
            for prediction_data in prediction_element['prediction']:
                result_row.update({
                    prediction_data['symbol']: fmt.format(
                        '{:.2f};{:.2f};{:.2f}',
                        prediction_data['lower'],
                        prediction_data['value'],
                        prediction_data['upper'])
                })
            result.append(result_row)

        return pd.DataFrame.from_dict(result).set_index('timestamp')

    return None


def metacrocubot_prediction_interpreter(metacrocubot_prediction) -> dict:
    """
    :type metacrocubot_prediction: OraclePrediction
    """
    mean_vector_values = getattr(metacrocubot_prediction, 'mean_vector')
    upper_bounds = getattr(metacrocubot_prediction, 'upper_bound')
    lower_bounds = getattr(metacrocubot_prediction, 'lower_bound')
    feature_sensitivity = getattr(metacrocubot_prediction, 'features_sensitivity')
    target_timestamp = getattr(metacrocubot_prediction, 'target_timestamp')

    result_list = []

    for timestamp in [target_timestamp]:  # metacrocubot only gives ONE datapoint
        datapoint = {}
        datapoint['timestamp'] = str(timestamp)
        datapoint['prediction'] = []

        # Drop NaNs from the results
        # otherwise we can't save results to a DB...
        mean_vector_values = mean_vector_values.where(pd.notnull(mean_vector_values), None)
        upper_bounds = upper_bounds.where(pd.notnull(upper_bounds), None)
        lower_bounds = lower_bounds.where(pd.notnull(lower_bounds), None)

        for symbol in mean_vector_values.index:
            datapoint['prediction'].append(
                {'symbol': symbol,
                 'value': round(mean_vector_values[symbol], 2) if mean_vector_values[symbol] else None,
                 'upper': round(upper_bounds[symbol], 2) if upper_bounds[symbol] else None,
                 'lower': round(lower_bounds[symbol], 2) if lower_bounds[symbol] else None
                 })
        result_list.append(datapoint)

    result = {}
    result['datapoints'] = result_list
    result['factors'] = {}

    for feature, sensitivity in feature_sensitivity.items():
        result['factors'][feature] = sensitivity

    return result
