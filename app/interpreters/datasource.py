import abc
from collections import namedtuple

import pandas as pd

InterpreterResult = namedtuple('InterpreterResult', 'result errors')


class AbstractDataSourceInterpreter(metaclass=abc.ABCMeta):
    COLUMNS = []
    INDEX_COLUMN = []

    def __init__(self):
        self.errors = []

    def from_csv_to_dataframe(self, csv_file):
        try:
            dataframe = pd.read_csv(csv_file, sep=',', index_col=self.INDEX_COLUMN, parse_dates=True)
        except Exception as e:
            dataframe = None
            self.errors.append(str(e))
        else:
            if not list(dataframe.columns) == self.COLUMNS:
                self.errors.append('Invalid columns!')
            if len(dataframe[dataframe.index >= pd.Timestamp.now()]) > 0:
                self.errors.append('Contains data in the future!')
        return InterpreterResult(dataframe, self.errors)

    @abc.abstractmethod
    def from_dataframe_to_data_dict(self, dataframe: pd.DataFrame) -> dict:
        raise NotImplementedError


class GymDataSourceInterpreter(AbstractDataSourceInterpreter):
    COLUMNS = ['number_people', 'timestamp', 'day_of_week', 'is_weekend', 'is_holiday',
               'temperature', 'is_start_of_semester', 'is_during_semester', 'month',
               'hour']
    INDEX_COLUMN = 'date'

    def from_dataframe_to_data_dict(self, dataframe):
        cols = dataframe.columns
        gym_names = ['UCBerkeley']
        data_dict = {}

        for col in cols:
            values = getattr(dataframe, col).values
            data_dict[col] = pd.DataFrame(data=values, index=dataframe.index, columns=gym_names, dtype='float32')

        return data_dict


class StockDataSourceInterpreter(AbstractDataSourceInterpreter):
    COLUMNS = ['Shares', 'Ticker', 'Returns', 'Beta to J203', 'Beta to USDZAR',
               'Beta to RBAS', 'Beta to RLRS', 'Beta to FSPI', 'Specific Risk',
               'Debt to Equity', 'Debt to Equity Trend', 'Interest Cover Trend',
               'log Market Cap', 'log Trading Volume', 'Earnings Yield',
               'Earnings Yield Trend', 'Bookvalue to Price',
               'Bookvalue to Price Trend', 'Dividend Yield', 'Dividend Yield Trend',
               'Cashflow to Price', 'Cashflow to Price Trend', 'Sales to Price',
               'Sales to Price Trend', 'Profit Margin', 'Capital Turnover',
               'Capital Turnover Trend', 'Return on Assets', 'Return on Assets Trend',
               'Return on Equity', '3 Month Return', '6 Month Return',
               '12 Month Return', '24 Month Return', '36 Month Return', 'Resource',
               'Financial']
    INDEX_COLUMN = 'DateStamps'

    def from_dataframe_to_data_dict(self, dataframe):
        features = set(dataframe.columns) - {'DateStamps', 'Ticker'}
        return {feature: dataframe.pivot(columns='Ticker', values=feature) for feature in features}
