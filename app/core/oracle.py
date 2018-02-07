import random

from dateutil import rrule


class Oracle:
    def train(self, *args, **kwargs):
        return {}

    def predict(self, data, *args, **kwargs):
        # Completely bogus prediction
        start = data['start_time']
        end = data['end_time']
        list_of_days = list(rrule.rrule(freq=rrule.DAILY, dtstart=start, until=end))

        return [{'timestamp': day.strftime('%Y-%m-%d'),
                 'value': random.randint(1, 100),
                 'confidence': random.random()}
                for day in list_of_days]
