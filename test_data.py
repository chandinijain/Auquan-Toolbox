from __future__ import absolute_import, division, print_function, unicode_literals
try:
    from urllib import urlretrieve, urlopen
except ImportError:
    from urllib.request import urlretrieve, urlopen
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
import os
import datetime as dt
import logging

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
                assert(download(exchange, m, file_name,logger)),"%s not found. Please check settings!"%file_name
            except AssertionError:
                logger.exception("%s not found. Please check settings!"%file_name)
                raise      
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

def get_logger():
	logger_name = dt.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
	logger = logging.getLogger(logger_name)
	logger.setLevel(logging.DEBUG)
	logger_dir = 'runLogs/'
	logger_file = '%srun-%s.txt'%(logger_dir,logger_name)
	if not os.path.exists(logger_dir):
	    os.makedirs(logger_dir)
	formatter = logging.Formatter('%(message)s')
	file_handler = logging.FileHandler(logger_file)
	console_handler = logging.StreamHandler()
	file_handler.setFormatter(formatter)
	console_handler.setFormatter(formatter)
	logger.addHandler(file_handler)
	logger.addHandler(console_handler)
	return logger


start = '2001-03-03'
end = '2016-11-01'
logger = get_logger()
exchange = 'nyse'
markets = []
logger.info("Loading Data from %s to %s...."%(start,end))
try:
	dates = [pd.to_datetime(start), pd.to_datetime(end)]
except ValueError:
    logger.exception("%s or %s is not valid date. Please check settings!"%(start, end))
    raise ValueError("%s or %s is not valid date. Please check settings!"%(start, end))

try:
    assert(dates[1]>dates[0]),"Start Date is after End Date"
except AssertionError:
    logger.exception("Start Date is after End Date")
    raise

if len(markets)==0:
	assert download_security_list(exchange, logger)
	file_name = '%s/%s.txt'%(exchange.lower(), exchange.lower())
	markets = [line.strip() for line in open(file_name)]
    # with open(file_name) as f:
    #     markets = f.read().splitlines()


markets = [m.upper() for m in markets]
features = ['OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME']
back_data = {}

assert data_available(exchange, markets,logger)
for market in markets:
	date_range = pd.date_range(start=dates[0]-BDay(1), end=dates[1], freq='B')
	logger.info('Reading %s.csv'%market)
	csv = pd.read_csv('%s/historicalData/%s.csv'%(exchange.lower(), market.lower()), index_col=0)
	csv.index = pd.to_datetime(csv.index)
	csv.columns = [col.upper() for col in csv.columns]
	csv = csv.reindex(index=csv.index[::-1])
	back_data[market] = pd.DataFrame(index=date_range, columns=features)
	try:
		for feature in features:
			back_data[market][feature] = csv[feature][date_range]


		dates_to_drop = pd.Series(False, index=date_range)
		dates_to_drop |= pd.isnull(back_data[market]['OPEN'])
		dropped_dates = date_range[dates_to_drop]
		date_range = date_range[~dates_to_drop]
		print(date_range[0])
		if date_range[0] > dates[0]:
			logger.info("Not Enough data for  %s"%market)
			markets.remove(market)
		else:
			try:
				temp = pd.Series(0, index=date_range)
				for feature in features:
					temp += back_data[market][feature]
			except:
				logger.info("Data not float for  %s"%market)
				markets.remove(market)
	except:
		logger.info("Corrupt data for  %s"%market)
		markets.remove(market)
    

file_name = '%s/%s_new11.txt'%(exchange.lower(), exchange.lower())
f = open(file_name,'w')
for m in markets:
	print(m)
	f.write('%s'%m)
	f.write('\n')

print('Done')
