import pandas as pd
import numpy as np
from pandas.tseries.offsets import BDay
import os
import csv
import json
from pythonToolbox.dataloader import load_data
from pythonToolbox.resultviewer import loadgui
import matplotlib.pyplot as plt

def settings():
    case = 3                    # Problem Number
    exchange = "nasdaq"         # Exchange to download data for
    markets = ['AAPL']    		# Stocks to download data for
    date_start = '2015-11-30'   # Date to start the backtest
    date_end = '2016-11-30'     # Date to end the backtest
    lookback = 90               # Number of days you want historical data for

    """ To make a decision for day t, your algorithm will have historical data
    from t-lookback to t-1 days"""
    return [case, exchange, markets, date_start, date_end, lookback]

def test(case, exchange, markets, answer, date_start, date_end, lookback, budget=100000, verbose=False, base_index='INX'):

	(lookback_data, date_range) = load_data(exchange, markets, date_start, date_end, lookback)

	period1 = 90
    period2 = 60
    period3 = 30
    period4 = 20

    lookback_data['X1'] = pd.DataFrame(0, index=lookback_data['CLOSE'].index, columns=lookback_data['CLOSE'].columns)
    lookback_data['X2'] = pd.DataFrame(0, index=lookback_data['CLOSE'].index, columns=lookback_data['CLOSE'].columns)
    lookback_data['X3'] = pd.DataFrame(0, index=lookback_data['CLOSE'].index, columns=lookback_data['CLOSE'].columns)
    lookback_data['X4'] = pd.DataFrame(0, index=lookback_data['CLOSE'].index, columns=lookback_data['CLOSE'].columns)
    lookback_data['Y'] = pd.DataFrame(0, index=lookback_data['CLOSE'].index, columns=lookback_data['CLOSE'].columns)

    markets_close = lookback_data['CLOSE']
    market_open = lookback_data['OPEN']

    for end in range(max(period1,period2,period3,period4), lookback_data['CLOSE'].index.size):
        start = end - lookback
    	avg_p1 = markets_close[end-period1 : end].sum() / period1
    	avg_p2 = markets_close[end-period2 : end].sum() / period2
    	avg_p3 = markets_close[end-period3 : end].sum() / period3
    	avg_p4 = markets_close[end-period4 : end].sum() / period4

    	lookback_data['X1'].iloc[end] = avg_p1-avg_p3
    	lookback_data['X2'].iloc[end] = avg_p1-avg_p4
    	lookback_data['X3'].iloc[end] = avg_p2-avg_p3
    	lookback_data['X4'].iloc[end] = avg_p3-avg_p4
    	lookback_data['Y]'].iloc[end] = np.sign(markets_close[end]-markets_close[end-1])

    print(lookback_data['F4'])
    print(lookback_data['Y'])