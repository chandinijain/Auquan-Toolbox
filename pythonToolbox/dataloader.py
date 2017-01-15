from __future__ import absolute_import, division, print_function, unicode_literals
try:
    from urllib import urlretrieve, urlopen
except ImportError:
    from urllib.request import urlretrieve, urlopen
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
import os

def download(exchange, ticker, file_name,logger):
    url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/%s/historicalData/%s.csv'%(exchange.lower(), ticker.lower())
    status = urlopen(url).getcode()
    if status == 200:
        logger.info('Downloading %s data to file: %s'%(ticker, file_name))
        urlretrieve(url, file_name)
        return True
    else:
        logger.info('File not found. Please check settings!')
        return False

def data_available(exchange, markets,logger):
    dir_name = '%s/historicalData/'%exchange.lower()
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    for m in markets:
        file_name = '%s%s.csv'%(dir_name, m.lower())
        if not os.path.exists(file_name):
            try:
                assert(download(exchange, m, file_name,logger))
            except AssertionError:
                logger.exception("%s not found. Ommitting!"%file_name)   
    return True

def download_security_list(exchange, logger):
    dir_name = '%s/'%exchange.lower()
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    file_name = '%s%s.txt'%(dir_name, exchange.lower())
    if not os.path.exists(file_name):
        url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/%s'%(file_name)
        status = urlopen(url).getcode()
        if status == 200:
            logger.info('Downloading data to file: %s'%file_name)
            urlretrieve(url, file_name)
            return True
        else:
            logger.info('File not found. Please check exchange settings!')
        return False
    else:
        return True

def load_data(exchange, markets, start, end, lookback, budget, logger, random=False):

    logger.info("Loading Data from %s to %s...."%(start,end))

    # because there are some holidays adding some cushion to lookback
    try:
        dates = [pd.to_datetime(start)-BDay(lookback* 1.10), pd.to_datetime(end)]
    except ValueError:
        logger.exception("%s or %s is not valid date. Please check settings!"%(start, end))
        raise ValueError("%s or %s is not valid date. Please check settings!"%(start, end))

    try:
        assert(dates[1]>dates[0]),"Start Date is after End Date"
    except AssertionError:
        logger.exception("Start Date is after End Date")
        raise

    #Download list of securities
    assert(download_security_list(exchange, logger))
    if len(markets)==0:
        file_name = '%s/%s.txt'%(exchange.lower(), exchange.lower())
        markets = [line.strip() for line in open(file_name)]

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
        market_to_drop = []
        for market in markets:
            assert data_available(exchange, market, logger)
            logger.info('Reading %s.csv'%market)
            csv = pd.read_csv('%s/historicalData/%s.csv'%(exchange.lower(), market.lower()), index_col=0)
            csv.index = pd.to_datetime(csv.index)
            csv.columns = [col.upper() for col in csv.columns]
            csv = csv.reindex(index=csv.index[::-1])
            features = [col.upper() for col in csv.columns]
            for feature in features:
                null_dates = pd.Series(False, index=date_range)
                try:
                    if not(back_data.has_key(feature)):
                        back_data[feature] = pd.DataFrame(index=date_range, columns=markets)
                except:
                    if feature not in back_data:
                        back_data[feature] = pd.DataFrame(index=date_range, columns=markets)
                back_data[feature][market] = csv[feature][date_range]
                null_dates = pd.isnull(back_data[feature][market])
                if null_dates[dates[0]-BDay(1)+BDay(1)]:
                    if not market in market_to_drop:
                        market_to_drop.append(market)
                    

        for m in market_to_drop: 
            logger.info('Dropping %s. Not Enough Data'%m)
            markets.remove(m) 

        for feature in features:
            back_data[feature].drop(market_to_drop, axis=1, inplace=True)
        dates_to_drop = pd.Series(False, index=date_range)
        for feature in features:
            dates_to_drop |= pd.isnull(back_data[feature]).any(axis=1)

        dropped_dates = date_range[dates_to_drop]
        date_range = date_range[~dates_to_drop]
        for feature in features:
            back_data[feature] = back_data[feature].drop(dropped_dates)

    back_data['COST TO TRADE'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['POSITION'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['ORDER'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['FILLED_ORDER'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['DAILY_PNL'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['TOTAL_PNL'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['FUNDS'] = pd.Series(budget, index=date_range)
    back_data['VALUE'] = pd.Series(budget, index=date_range)
    back_data['MARGIN'] = pd.Series(0, index=date_range)

    if date_range[0] > dates[0]:
        logger.info("Lookback exceeds Available data. Data starts from %s"%date_range[0])

    return back_data, date_range
