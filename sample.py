import pandas as pd
import numpy as np
from pythonToolbox import backtest

def settings():
    exchange = "nasdaq"         # Exchange to download data for
    markets = ['AAPL','ALL']    # Stocks to download data for
    date_start = '2016-11-01'   # Date to start the backtest
    date_end = '2016-11-30'     # Date to end the backtest
    lookback = 90               # Number of days you want historical data for

    """ To make a decision for day t, your algorithm will have historical data
    from t-lookback to t-1 days"""
    return [exchange, markets, date_start, date_end, lookback]

def trading_strategy(lookback_data):
    """
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
    :return: A pandas dataframe with markets you are trading as index(row) and 
    signal, price and quantity as columns
    order['SIGNAL']:buy (+1), hold (0) or sell (-1) trading signals for all securities in markets[]
    order['PRICE']: The price where you want to trade each security. Buy orders are executed at or below the price and sell orders are executed at or above the price
    order['QUANTITY']: The quantity of each stock you want to trade.
    System will buy the specified quantity of stock if it's price <= price specified here
    System will sell the specified quantity of a stock if it's price >= price specified here
    """

    """IMPORTANT: Please make sure you have enough funds to buy or sell. 
        Order is cancelled if order_value > available funds(both buy and short sell)"""

    order = pd.DataFrame(0, index=lookback_data['POSITION'].columns, columns = ['SIGNAL','QUANTITY','PRICE'])

    ##YOUR CODE HERE

    period1 = 90
    period2 = 20

    markets_close = lookback_data['CLOSE']
    market_open = lookback_data['OPEN']
    avg_p1 = markets_close[-period1 : ].sum() / period1
    avg_p2 = markets_close[-period2 : ].sum() / period2

    order['SIGNAL'][avg_p1-avg_p2>0] = 1
    order['SIGNAL'][avg_p1-avg_p2<0] = -1

    order['PRICE']=lookback_data['CLOSE'].iloc[-1]

    order['QUANTITY']=10

    return order

if __name__ == '__main__':
    [exchange, markets, date_start, date_end, lookback] = settings()
    backtest(exchange, markets, trading_strategy, date_start, date_end, lookback)#,verbose=True)