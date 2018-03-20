import abc
import datetime
from typing import List

import pandas as pd
import pytz
from dateutil import parser

from app.core.utils import import_class
from app.oracle import OraclePrediction
from config import DATE_FORMAT


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
    start = prediction.prediction_request['start_time']
    prediction_start = datetime.strptime(start, DATE_FORMAT).astimezone(pytz.utc)

    end = prediction.prediction_request['end_time']
    prediction_end = datetime.strptime(end, DATE_FORMAT).astimezone(pytz.utc) + datetime.timedelta(days=1)

    result = []
    if prediction.prediction_result:
        for prediction_element in prediction.prediction_result.result:
            result_timestamp = parser.parse(prediction_element['timestamp'])
            is_result_in_prediction_time = prediction_start < result_timestamp <= prediction_end
            if is_result_in_prediction_time:
                result_row = {
                    'timestamp': result_timestamp
                }
                for prediction_data in prediction_element['prediction']:
                    result_row.update({
                        prediction_data['feature']: "{:.2f};{:.2f};{:.2f}".format(
                            prediction_data['lower'],
                            prediction_data['value'],
                            prediction_data['upper']
                        )
                    })
                result.append(result_row)

        return pd.DataFrame.from_dict(result).set_index('timestamp')

    return None


def mock_crocubot_prediction_interpreter(mock_crocubot_prediction: OraclePrediction) -> List[dict]:
    mean_vector_values = getattr(mock_crocubot_prediction, 'mean_vector')
    upper_bounds = getattr(mock_crocubot_prediction, 'upper_bound')
    lower_bounds = getattr(mock_crocubot_prediction, 'lower_bound')

    result_list = []
    for timestamp in mean_vector_values.index:
        datapoint = {}
        datapoint['timestamp'] = str(timestamp)
        datapoint['prediction'] = []
        for symbol in mean_vector_values.loc[timestamp].index:
            datapoint['prediction'].append(
                {'feature': symbol,
                 'value': round(mean_vector_values.loc[timestamp][symbol], 2),
                 'upper': round(upper_bounds.loc[timestamp][symbol], 2),
                 'lower': round(lower_bounds.loc[timestamp][symbol], 2)
                 })
        result_list.append(datapoint)

    return result_list
