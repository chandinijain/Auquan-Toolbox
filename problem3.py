import pandas as pd
import numpy as np
from pythonToolbox import backtest

def settings():
    case = 3                    # Problem Number
    exchange = "nasdaq"         # Exchange to download data for
    markets = ['AAPL','ALL']    # Stocks to download data for
    date_start = '2013-11-01'   # Date to start the backtest
    date_end = '2016-11-30'     # Date to end the backtest
    lookback = 90               # Number of days you want historical data for

    """ To make a decision for day t, your algorithm will have historical data
    from t-lookback to t-1 days"""
    return [case, exchange, markets, date_start, date_end, lookback]

def problem(lookback_data):
    """
    Answer to the second problem
    :param lookback_data: Historical Data for the past "lookback" number of days as set in the main settings.
     It is a dictionary of features such as,
     'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME', 'SLIPPAGE', 'POSITION', 'ORDER',
     'FILLED_ORDER', 'DAILY_PNL', 'TOTAL_PNL', 'FUNDS', 'VALUE'
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
    :return: An array of quantity of each stock you want to trade.
    System will buy the specified quantity of stock if it's price <= price specified here
    System will sell min(specified quantity, current long position) of a stock if it's price >= price specified here
    """

    """IMPORTANT: Please make sure you have enough funds to buy or sell. 
        Order is cancelled if order_value > available funds(both buy and short sell)"""

    signal = np.ones(lookback_data['POSITION'].columns.size)
    prices = np.ones(lookback_data['POSITION'].columns.size)
    quantity = np.ones(lookback_data['POSITION'].columns.size)

    ##YOUR CODE HERE

    period1 = 90
    period2 = 60
    period3 = 30
    period4 = 20

    lookback_data['F1'] = pd.DataFrame(0, index=lookback_data['POSITION'].index, columns=lookback_data['POSITION'].columns)
    lookback_data['F2'] = pd.DataFrame(0, index=lookback_data['POSITION'].index, columns=lookback_data['POSITION'].columns)
    lookback_data['F3'] = pd.DataFrame(0, index=lookback_data['POSITION'].index, columns=lookback_data['POSITION'].columns)
    lookback_data['F4'] = pd.DataFrame(0, index=lookback_data['POSITION'].index, columns=lookback_data['POSITION'].columns)

    markets_close = lookback_data['CLOSE']
    market_open = lookback_data['OPEN']
    avg_p1 = markets_close[-period1 : ].sum() / period1
    avg_p2 = markets_close[-period2 : ].sum() / period2
    avg_p3 = markets_close[-period3 : ].sum() / period3
    avg_p4 = markets_close[-period4 : ].sum() / period4

    lookback_data['F1'] = avg_p1-avg_p3
    lookback_data['F2'] = avg_p1-avg_p4
    lookback_data['F3'] = avg_p2-avg_p3
    lookback_data['F4'] = avg_p3-avg_p4


    return signal, prices, quantity


if __name__ == '__main__':
    [case, exchange, markets, date_start, date_end, lookback] = settings()
    backtest(case, exchange, markets, problem, date_start, date_end, lookback)#,verbose=True)
