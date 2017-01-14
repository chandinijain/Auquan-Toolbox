from __future__ import absolute_import, division, print_function, unicode_literals
try:
    from urllib import urlretrieve, urlopen
except ImportError:
    from urllib.request import urlretrieve
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
import os

def download(exchange, ticker, file_name):
    url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/%s/historicalData/%s.csv'%(exchange.lower(), ticker.lower())
    status = urlopen(url).getcode()
    if status == 200:
        print('Downloading %s data to file: %s'%(ticker, file_name))
        urlretrieve(url, file_name)
        return True
    else:
        print('File not found. Please check settings!')
        return False

def data_available(exchange, markets):
    dir_name = '%s/historicalData/'%exchange.lower()
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    for m in markets:
        file_name = '%s%s.csv'%(dir_name, m.lower())
        if not os.path.exists(file_name):
            assert(download(exchange, m, file_name)),"%s not found. Please check settings!"%file_name
    return True

def load_data(exchange, markets, start, end, lookback, random=False):

    print("Loading Data from %s to %s...."%(start,end))

    dates = [pd.to_datetime(start)-BDay(lookback), pd.to_datetime(end)]

    markets = [m.upper() for m in markets]
    features = ['OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME']
    date_range = pd.date_range(start=dates[0], end=dates[1], freq='B')
    back_data = {}
    
    if random:
        for feature in features:
            back_data[feature] = pd.DataFrame(np.random.randint(10, 50, size=(date_range.size,len(markets))),
                                              index=date_range,
                                              columns=markets)
    else:
        assert data_available(exchange, markets)
        for market in markets:
            csv = pd.read_csv('%s/historicalData/%s.csv'%(exchange.lower(), market.lower()), index_col=0)
            csv.index = pd.to_datetime(csv.index)
            csv.columns = [col.upper() for col in csv.columns]
            csv = csv.reindex(index=csv.index[::-1])
            features = [col.upper() for col in csv.columns]
            for feature in features:
                if not(back_data.has_key(feature)):
                    back_data[feature] = pd.DataFrame(index=date_range, columns=markets)
                back_data[feature][market] = csv[feature][date_range]

        dates_to_drop = pd.Series(False, index=date_range)
        for feature in features:
            dates_to_drop |= pd.isnull(back_data[feature]).any(axis=1)

        dropped_dates = date_range[dates_to_drop]
        date_range = date_range[~dates_to_drop]
        for feature in features:
            back_data[feature] = back_data[feature].drop(dropped_dates)

    back_data['SLIPPAGE'] = (back_data['HIGH'] - back_data['LOW']).abs() * 0.01
    back_data['POSITION'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['ORDER'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['FILLED_ORDER'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['DAILY_PNL'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['TOTAL_PNL'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['FUNDS'] = pd.Series(0, index=date_range)
    back_data['VALUE'] = pd.Series(0, index=date_range)
    back_data['MARGIN'] = pd.Series(0, index=date_range)

    if date_range[0] > dates[0]:
        print("Lookback exceeds Available data. Data starts from %s"%date_range[0])

    return back_data, date_range

import pandas as pd
import numpy as np
from pandas.tseries.offsets import BDay
import os
import csv
import json
from pythonToolbox.dataloader import load_data
from pythonToolbox.resultviewer import loadgui
import matplotlib.pyplot as plt
#from sklearn import linear_model

def settings():
    exchange = "nasdaq"         # Exchange to download data for
    markets = ['AAPL']    		# Stocks to download data for
    date_start = '2015-11-30'   # Date to start the backtest
    date_end = '2016-11-30'     # Date to end the backtest
    lookback = 90               # Number of days you want historical data for

    """ To make a decision for day t, your algorithm will have historical data
    from t-lookback to t-1 days"""
    return [exchange, markets, date_start, date_end, lookback]

def test(exchange, markets, date_start, date_end, lookback, budget=100000, verbose=False, base_index='INX'):

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
		lookback_data['Y'].iloc[end] = np.sign(markets_close.iloc[end]-markets_close.iloc[end-1])

    #X_train = lookback_data['X4'][:-50]
    # train = lookback_data['X4'][:-50]
    # X_test = lookback_data['X4'][-50:]

    # # Split the targets into training/testing sets
    #     Y_train = lookback_data['Y'][:-50]
    #     Y_test = lookback_data['Y'][-50:]
    #     #regr = linear_model.LinearRegression()
    #     #regr.fit(X_train, Y_train)

    #     # The coefficients
    #     #print('Coefficients: \n', regr.coef_)
    #     # The mean squared error
    #     #print("Mean squared error: %.2f"
    #     #% np.mean((regr.predict(X_test) - Y_test) ** 2))
    #     # Explained variance score: 1 is perfect prediction
    #     #print('Variance score: %.2f' % regr.score(X_test, Y_test))

    # # Plot outputs

    #     print(X_test[m].values)
    #     print(Y_test[m].values)

    #     plt.scatter(X_test[m].values, Y_test[m].values,  color='black')
    #     plt.plot(diabetes_X_test, regr.predict(diabetes_X_test), color='blue',linewidth=3)
    #     plt.show()]


if __name__ == '__main__':
    [exchange, markets, date_start, date_end, lookback] = settings()
    test(exchange, markets, date_start, date_end, lookback)
