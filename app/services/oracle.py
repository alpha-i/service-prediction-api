import time

from app.core.utils import import_class


def get_oracle_for_configuration(company_configuration):
    oracle_class = company_configuration.configuration['oracle_class']
    calendar_name = company_configuration.configuration['calendar_name']

    try:
        oracle = import_class(oracle_class)
    except ImportError:
        raise ImportError("No available oracle found for %s", oracle_class)

    return oracle(
        calendar_name=calendar_name,
        scheduling_configuration=company_configuration.configuration['scheduling'],
        oracle_configuration=company_configuration.configuration['oracle']
    )


def predict(prediction_request, data_dict, company_configuration):
    start_time = prediction_request['start_time']
    oracle = get_oracle_for_configuration(company_configuration)
    oracle.train(data_dict, start_time)
    oracle_prediction_result = oracle.predict(
        data=data_dict,
        current_timestamp=start_time,
        target_timestamp=None  # target_timestamp is decided by the FGL
    )
    return oracle_prediction_result


def train(data_dict, company_configuration):
    # oracle = get_oracle_for_configuration(company_configuration)
    time.sleep(1)
