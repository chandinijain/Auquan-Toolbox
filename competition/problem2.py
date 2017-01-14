import pandas as pd
import numpy as np
from pythonToolbox import backtest

def settings():
    case = 2                    # Problem Number
    exchange = "nasdaq"         # Exchange to download data for
    markets = ['AAPL','ALL']    # Stocks to download data for
    date_start = '2016-09-05'   # Date to start the backtest
    date_end = '2016-11-10'     # Date to end the backtest
    lookback = 5                # Number of days you want historical data for

    """ To make a decision for day t, your algorithm will have historical data
    from t-lookback to t-1 days"""

    return [case, exchange, markets, date_start, date_end, lookback]

def problem(lookback_data):
    """
    Answer to the second problem
    :param lookback_data: Historical Data for the past "lookback" number of days as set in the main settings.
     It is a dictionary of features such as,
     'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME', 'SLIPPAGE', 'POSITION', 'ORDER',
     'FILLED_ORDER', 'DAILY_PNL', 'TOTAL_PNL', 'FUNDS', 'PORTFOLIO VALUE'
     Any feature data can be accessed as:lookback_data['OPEN']
     The output is a pandas dataframe with dates as the index (row)
     and markets as columns. 
    """"""""""""""""""""""""""
    """""""""""""""""""""""""" 
    To see a complete list of features, uncomment the line below"""
    #print(lookback_data.keys())
    
    """""""""""""""""""""""""""
    :return: An array of trading signals for all securities in markets[], buy (+1), hold (0) or sell (-1)
    :return: An array of prices where you want to trade.
    System will buy a stock if it's price <= price specified here
    System will sell a stock if it's price >= price specified here
    """
    signal = np.zeros(lookback_data['POSITION'].columns.size)
    prices = np.zeros(lookback_data['POSITION'].columns.size)

    ##YOUR CODE HERE
    signal = np.random.randint(-1, 2, size=(lookback_data['LOW'].columns.size))
    prices = lookback_data['LOW'].iloc[-1]

    return signal, prices


if __name__ == '__main__':
    [case, exchange, markets, date_start, date_end, lookback] = settings()
    backtest(case, exchange, markets, problem, date_start, date_end, lookback)#,verbose=True)