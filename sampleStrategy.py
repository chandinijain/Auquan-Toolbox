import pandas as pd
import numpy as np

def settings():
    case = 3
    exchange = "nasdaq"
    markets = ['AAPL','ALL']
    date_start = '2016-11-05'
    date_end = '2016-11-10'
    lookback = 5
    return [case, exchange, markets, date_start, date_end, lookback]

def answer1(lookback_data):
    """
    Answer to the first problem
    :param lookback_data: Historical Data for the past "lookback" number of days as set in the main settings.
     It is a dictionary of features such as,
     'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME', 'SLIPPAGE', 'POSITION', 'ORDER',
     'FILLED_ORDER', 'DAILY_PNL', 'TOTAL_PNL', 'FUNDS', 'PORTFOLIO VALUE'
     Any feature data can be accessed as:lookback_data['OPEN']
     The output is a pandas dataframe with dates as the index (row)
     and markets as columns. 
     To see a complete list of features, uncomment the line below"""
    #print(lookback_data.keys())
    """
    :return: An array of trading signals, buy (+1), hold (0) or sell (-1)
    """
    signal = np.zeros(lookback_data['POSITION'].columns.size)

    ##YOUR CODE HERE
    
    sma_long_period = 5
    sma_short_period = 2
    markets_close = lookback_data['CLOSE']
    avg_long_curr = markets_close[-sma_long_period : ].sum() / sma_long_period
    avg_short_curr = markets_close[-sma_short_period : ].sum() / sma_short_period
    signal = np.random.randint(-1, 2, size=(lookback_data['LOW'].columns.size))

    return signal

def answer2(lookback_data, signal):
    """
    Answer to the second problem
    :param lookback_data: Same as problem one
     To see a complete list of features, uncomment the line below"""
    #print(lookback_data.keys())
    """
    :param signal : Generated in problem one
    
    :return: An array of prices where you want to trade.
    System will buy a stock if it's price <= price specified here
    System will sell a stock if it's price >= price specified here
    """
    prices = np.zeros(lookback_data['POSITION'].columns.size)

    ##YOUR CODE HERE
    
    prices = lookback_data['LOW'].iloc[-1]

    return prices

def answer3(lookback_data, signal, prices):
    """
    Answer to the second problem
    :param lookback_data: Same as problem one
     To see a complete list of features, uncomment the line below"""
    #print(lookback_data.keys())
    """
    :param signal : Generated in problem one
    :param prices: Generated in problem two
    :return: An array of quantity of each stock you want to trade.
    System will buy the specified quantity of stock if it's price <= price specified here
    System will sell min(specified quantity, current long position) of a stock if it's price >= price specified here
    """

    """IMPORTANT: Please make sure you have enough funds to buy. Order is cancelled if order_value > available funds"""

    quantity = np.ones(lookback_data['POSITION'].columns.size)

    ##YOUR CODE HERE
    q = signal*prices
    q = q.sum()
    #q=int(lookback_data['FUNDS'].iloc[-1]/q)
    return quantity
    
def trading_strategy(lookback_data, markets, budget_curr):
    """
    Generate strategy from the answers
    """
    
    signal = answer1(lookback_data)
    prices = answer2(lookback_data, signal)
    quantity = answer3(lookback_data, signal, prices)
    order = pd.DataFrame(0, index=markets, columns = ['QUANTITY','PRICE'])
    order['QUANTITY'] =  signal    # buy
    if case ==3:
        order['QUANTITY'] =  signal*quantity

    if case!= 1:
        order['PRICE'] = prices

    return order


    

if __name__ == '__main__':
    import auquanToolbox.auquanToolbox as at
    [case, exchange, markets, date_start, date_end, lookback] = settings()
    at.backtest(case, exchange, markets, trading_strategy, date_start, date_end, lookback)#,verbose=True)
