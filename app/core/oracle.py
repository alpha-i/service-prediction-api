import random

from dateutil import rrule


class Oracle:
    def train(self, *args, **kwargs):
        return {}

    def predict(self, data, *args, **kwargs):
        # Completely bogus prediction
        start = data['start_time']
        end = data['end_time']
        features = data['features']
        list_of_days = list(rrule.rrule(freq=rrule.DAILY, dtstart=start, until=end))

        prediction = []
        for day in list_of_days:
            prediction.append(
                {
                    'timestamp': day.strftime('%Y-%m-%d'),
                    'prediction': [
                        {'feature': feature,
                         'value': random.randint(1, 6),
                         'confidence': random.random()
                         } for feature in features]
                }
            )

        return prediction
