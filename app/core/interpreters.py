import abc
from datetime import datetime, timedelta

import pandas as pd
import pytz
from alphai_cromulon_oracle.oracle import OraclePrediction
from alphai_delphi.oracle.abstract_oracle import PredictionResult
from dateutil import parser

from config import DATE_FORMAT

DEFAULT_TIME_RESOLUTION = '15T'


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
    elif isinstance(prediction_result, OraclePrediction):
        return OraclePredictionInterpreter(prediction_result)()
    else:
        raise ValueError("No interpreter available for %s", prediction_result.__class__)


class DataSourceInterpreter(metaclass=abc.ABCMeta):
    pass


class CromulonDataSourceInterpreter(DataSourceInterpreter):
    """
    Given a dataframe-from-csv data source, output something that can be used for Cromulon
    """

    def __init__(self, datasource_frame: pd.DataFrame):
        self._result = make_dict_from_dataframe(datasource_frame)

    def __call__(self, *args, **kwargs):
        return self._result


def datasource_interpreter(data_source):
    # this has to take into account
    # the test data and the actual data
    # FIXME
    if isinstance(data_source, pd.DataFrame):
        if not isinstance(data_source.index, pd.DatetimeIndex):
            df = data_source.set_index(data_source.date)
        else:
            df = data_source
        df.index = pd.to_datetime(df.index, utc=True).round('15T')
        try:
            df.index = df.index.tz_localize(pytz.utc)
        except:
            # already timezone aware
            pass

        df = df.loc[~df.index.duplicated(keep='first')]  # Remove duplicate entries

        df['date'] = df.index
        # One hot encode categorical columns
        columns = ["day_of_week", "month", "hour"]
        df = pd.get_dummies(df, columns=columns)

        return CromulonDataSourceInterpreter(df)()


def make_dict_from_dataframe(df):
    """ Takes the csv-derived dataframe and splits into dict where each key is a column from the ."""

    cols = df.columns
    gym_names = ['UCBerkeley']
    data_dict = {}

    for col in cols:
        values = getattr(df, col).values
        data_dict[col] = pd.DataFrame(data=values, index=df.index, columns=gym_names, dtype='float32')

    return data_dict


def prediction_result_to_dataframe(prediction):
    start = prediction.prediction_request['start_time']
    prediction_start = datetime.strptime(start, DATE_FORMAT).astimezone(pytz.utc)

    end = prediction.prediction_request['end_time']
    prediction_end = datetime.strptime(end, DATE_FORMAT).astimezone(pytz.utc) + timedelta(days=1)

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


class AbstractDataSourceInterpreter(metaclass=abc.ABCMeta):
    @staticmethod
    @abc.abstractmethod
    def from_csv_to_dataframe(csv_file):
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def from_dataframe_to_data_dict(dataframe):
        raise NotImplementedError


class GymDataSourceInterpreter(AbstractDataSourceInterpreter):
    
    @staticmethod
    def from_csv_to_dataframe(csv_file):
        return pd.read_csv(csv_file, sep=',', index_col='date', parse_dates=True)

    @staticmethod
    def from_dataframe_to_data_dict(dataframe):
        cols = dataframe.columns
        gym_names = ['UCBerkeley']
        data_dict = {}

        for col in cols:
            values = getattr(dataframe, col).values
            data_dict[col] = pd.DataFrame(data=values, index=dataframe.index, columns=gym_names, dtype='float32')

        return data_dict


class StockDataSourceInterpreter(AbstractDataSourceInterpreter):

    @staticmethod
    def from_csv_to_dataframe(csv_file):
        return pd.read_csv(csv_file, sep=',', index_col='DateStamps', parse_dates=True)

    @staticmethod
    def from_dataframe_to_data_dict(dataframe):
        features = set(dataframe.columns) - {'DateStamps', 'Ticker'}
        return {feature: dataframe.pivot(columns='Ticker', values=feature) for feature in features}
