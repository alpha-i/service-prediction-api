import abc
from collections import defaultdict

import pandas as pd

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


def prediction_result_to_dataframe_with_error(prediction):
    fmt = MissingFieldsStringFormatter(missing='N/A')
    result = []
    if prediction.prediction_result:
        for prediction_element in prediction.prediction_result.result['datapoints']:
            result_timestamp = prediction_element['timestamp']

            result_row = {
                'timestamp': result_timestamp
            }
            for prediction_data in prediction_element['prediction']:
                if not prediction_data['value']:
                    # We won't show data where the value is none
                    continue
                result_row.update({
                    prediction_data['symbol']: fmt.format(
                        '{:.3f};{:.3f};{:.3f}',
                        prediction_data['lower'],
                        prediction_data['value'],
                        prediction_data['upper'])
                })
            result.append(result_row)

        return pd.DataFrame.from_dict(result).set_index('timestamp')

    return None


def prediction_result_to_dataframe(prediction):
    fmt = MissingFieldsStringFormatter(missing='N/A')
    result = []
    if prediction.prediction_result:
        for prediction_element in prediction.prediction_result.result['datapoints']:
            result_timestamp = prediction_element['timestamp']

            result_row = {
                'timestamp': result_timestamp
            }
            for prediction_data in prediction_element['prediction']:
                if prediction_data['value']:
                    result_row.update({
                        prediction_data['symbol']: fmt.format(
                            '{:.3f}',
                            prediction_data['value'])
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
    feature_sensitivity_per_symbol = getattr(metacrocubot_prediction, 'features_per_symbol_sensitivity')
    feature_sensitivity_average = getattr(metacrocubot_prediction, 'features_average_sensitivity')

    target_timestamp = getattr(metacrocubot_prediction, 'target_timestamp')

    result_list = []

    for timestamp in [target_timestamp]:  # metacrocubot only gives ONE datapoint
        datapoint = {}
        datapoint['timestamp'] = str(timestamp)
        datapoint['prediction'] = []

        # Change NaNs in None from the results
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

    for feature, sensitivity in feature_sensitivity_per_symbol.items():
        if not result['factors'].get(feature):
            result['factors'][feature] = {}
        result['factors'][feature]['symbols'] = sensitivity.dropna().to_dict()

    for feature, sensitivity in feature_sensitivity_average.items():
        if not result['factors'].get(feature):
            result['factors'][feature] = {}
        result['factors'][feature]['average'] = sensitivity

    return result


def clean_feature_name(name):
    splitted_feature_name = name.split("_")
    return "".join(splitted_feature_name[:-1])


def calculate_factor_percentage(factors):
    total = sum([value for value in factors.values()])
    percent_factors = {key: round(value * 100 / total, 2) for key, value in factors.items()}
    return sorted(percent_factors.items(), key=lambda x: x[1], reverse=True)


def calculate_average_factors_percentage(factors):
    factors = {clean_feature_name(key): value for key, value in factors.items()}
    average_factors = {}
    for feature, value in factors.items():
        average_factors[feature] = factors[feature]['average']
    return dict(calculate_factor_percentage(average_factors))


def calculate_per_symbol_factors_percentage(factors):
    factors = {clean_feature_name(key): value for key, value in factors.items()}

    # first fetch all the symbols' values, discarding the average
    symbols_factors_normalise = defaultdict(dict)
    for feature, value in factors.items():
        for symbol, value in factors[feature]['symbols'].items():
            symbols_factors_normalise[symbol][feature] = value

    # the normalise at % the values for every feature per stock
    for symbol, value in symbols_factors_normalise.items():
        total_for_symbol = sum([value for value in value.values()])
        symbols_factors_normalise[symbol] = {key: round(value * 100 / total_for_symbol, 2)
                                             for key, value in value.items()}

    # restructure the output dict to be [feature][symbol]
    final_symbols_factors = defaultdict(dict)
    for symbol, values in symbols_factors_normalise.items():
        for feature, value in values.items():
            final_symbols_factors[feature][symbol] = symbols_factors_normalise[symbol][feature]

    return final_symbols_factors


def combine_average_and_symbols_sensitivities(factors):
    average_percent_factors = calculate_average_factors_percentage(factors)
    per_symbol_percent_factors = calculate_per_symbol_factors_percentage(factors)
    prediction_factors = defaultdict(dict)
    for feature, value in per_symbol_percent_factors.items():
        prediction_factors[feature]['average'] = average_percent_factors[feature]
        prediction_factors[feature].update(per_symbol_percent_factors[feature])
    return prediction_factors
