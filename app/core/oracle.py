import random

from dateutil import rrule


class Oracle:
    def train(self, *args, **kwargs):
        return {}

    def predict(self, data, *args, **kwargs):
        # Completely bogus prediction
        start = data['start_time']
        end = data['end_time']
        feature = data['features']
        list_of_days = list(rrule.rrule(freq=rrule.DAILY, dtstart=start, until=end))

        prediction = []
        for day in list_of_days:
            datapoint = {}
            datapoint['timestamp'] = str(day)
            datapoint['prediction'] = []
            random_value = random.randint(1, 6)
            datapoint['prediction'].append(
                {
                    'feature': feature,
                    'value': random_value,
                    'upper': random_value + 1,
                    'lower': random_value - 1
                }
            )
            prediction.append(datapoint)

        return prediction
