import pandas as pd
import numpy as np
from pythonToolbox import backtest

def settings():
    case = 1                    # Problem Number
    exchange = "nasdaq"         # Exchange to download data for
    markets = ['AAPL']    # Stocks to download data for
    date_start = '2015-11-30'   # Date to start the backtest
    date_end = '2016-11-30'     # Date to end the backtest
    lookback = 45                # Number of days you want historical data for
    """ To make a decision for day t, your algorithm will have historical data
    from t-lookback to t-1 days"""
    return [case, exchange, markets, date_start, date_end, lookback]

def problem(lookback_data):
    """ :param lookback_data: Historical Data for the past "lookback" number of days as set in the main settings.
     It is a dictionary of features such as,
     'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME', 'SLIPPAGE', 'FUNDS', 'PORTFOLIO VALUE'
     Any feature data can be accessed as:lookback_data['OPEN']
     The output is a pandas dataframe with dates as the index (row) and markets as columns. 
    """"""""""""""""""""""""""
    To see a complete list of features, uncomment the line below"""
    #print(lookback_data.keys())
    
    """""""""""""""""""""""""""
    :return: An array of trading signals for all securities in markets[], buy (+1), hold (0) or sell (-1)
    """""""""""""""""""""""""""
    signal = pd.Series(0, index=lookback_data['POSITION'].columns)

    ## WRITE YOUR CODE HERE
    
    sma_long_period = 45
    sma_short_period = 10
    markets_close = lookback_data['CLOSE']
    avg_long_curr = markets_close[-sma_long_period : ].sum() / sma_long_period
    avg_short_curr = markets_close[-sma_short_period : ].sum() / sma_short_period
    signal[avg_long_curr>avg_short_curr] = 1
    signal[avg_long_curr<avg_short_curr] = -1

    return signal


if __name__ == '__main__':
    [case, exchange, markets, date_start, date_end, lookback] = settings()
    backtest(case, exchange, markets, problem, date_start, date_end, lookback)#,verbose=True)
