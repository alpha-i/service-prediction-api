import time

import datetime
from alphai_delphi import AbstractOracle
import pandas as pd
import numpy as np


class OraclePrediction:
    def __init__(self, mean_vector, lower_bound, upper_bound, prediction_timestamp, target_timestamp):
        """ Container for the oracle predictions.

        :param mean_vector: Prediction values for various series at various times
        :type mean_vector: pd.DataFrame
        :param lower_bound: Lower edge of the requested confidence interval
        :type lower_bound: pd.DataFrame
        :param upper_bound: Upper edge of the requested confidence interval
        :type upper_bound: pd.DataFrame
        :param prediction_timestamp: Timestamp when the prediction was made
        :type target_timestamp: datetime.datetime
        """
        self.target_timestamp = target_timestamp
        self.mean_vector = mean_vector
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.prediction_timestamp = prediction_timestamp
        self.covariance_matrix = pd.DataFrame()
        self._feature_sensitivity = {}

    def add_feature_sensitivity(self, feature, sensitivity):
        """
        Add feature sensitivity value
        :param feature:
        :param sensitivity:
        :return:
        """
        self._feature_sensitivity[feature] = sensitivity

    @property
    def features_sensitivity(self):
        return self._feature_sensitivity

    def __repr__(self):
        return "<Oracle prediction: {}>".format(self.__dict__)



class MockMetaCrocubot(AbstractOracle):
    def _sanity_check(self):
        pass

    def save(self):
        pass

    def load(self):
        pass

    def train(self, data, current_timestamp):
        time.sleep(1)

    def predict(self, data, current_timestamp, target_timestamp):
        # Initialize a random prediction...
        today = datetime.datetime.now()
        days_range = pd.date_range(today, today + datetime.timedelta(days=30), freq='D')
        np.random.seed(seed=10)
        mean_vector_data = np.random.randint(1, high=100, size=len(days_range))
        mean_vector_df = pd.DataFrame({'timestamp': days_range, 'means': mean_vector_data})
        mean_vector_df = mean_vector_df.set_index('timestamp')
        prediction = OraclePrediction(
            mean_vector=mean_vector_df,
            lower_bound=mean_vector_df,
            upper_bound=mean_vector_df,
            prediction_timestamp=today,
            target_timestamp=today + datetime.timedelta(days=30)
        )
        prediction.add_feature_sensitivity('returns', 0.1)
        return prediction

    def resample(self, data):
        pass

    def fill_nan(self, data):
        pass

    def global_transform(self, data):
        pass

    def get_universe(self, data):
        pass

    @property
    def target_feature(self):
        return 'whatever'

    @property
    def target_feature_name(self):
        return 'Returns'
