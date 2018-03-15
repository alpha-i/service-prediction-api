import abc

import pandas as pd


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
