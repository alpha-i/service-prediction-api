import os
import pickle
import unittest

from app import interpreters

HERE = os.path.join(os.path.dirname(__file__))

DUMMY_PREDICTION_PICKLE_FILE = os.path.join(HERE, '../resources/dummy_prediction.pickle')
DUMMY_ORACLE_RESULTS_PICKLE_FILE = os.path.join(HERE, '../resources/dummy_oracle_result.pickle')


class TestPredictionResult(unittest.TestCase):
    def setUp(self):
        pickle_file = open(DUMMY_PREDICTION_PICKLE_FILE, 'rb')
        self.prediction_result = pickle.load(pickle_file)
        pickle_file.close()

    def test_gets_a_prediction_result_out_of_a_prediction_result(self):
        result = interpreters.prediction.prediction_interpreter(self.prediction_result)

        assert result[0]['timestamp'] == '2008-01-02 02:02:02'
        assert result[0]['prediction'] == [
            {'feature': 'UCB', 'value': 12.23, 'upper': 13.73, 'lower': 10.73},
            {'feature': 'Santa Cruz', 'value': 13.1, 'upper': 14.6, 'lower': 11.6}
        ]


class TestOracleResult(unittest.TestCase):
    def setUp(self):
        picke_file = open(DUMMY_ORACLE_RESULTS_PICKLE_FILE, 'rb')
        self.prediction_result = pickle.load(picke_file)
        picke_file.close()

    def test_gets_a_prediction_for_an_oracle_result(self):
        result = interpreters.prediction.prediction_interpreter(self.prediction_result)

        assert result[0]['timestamp'] == '2008-01-02 02:02:02'
        assert result[0]['prediction'] == [
            {'feature': 'UCB', 'value': 9.58, 'upper': 11.08, 'lower': 8.08},
            {'feature': 'Santa Cruz', 'value': 6.74, 'upper': 8.24, 'lower': 5.24}
        ]
