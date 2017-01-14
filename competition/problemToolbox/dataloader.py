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
