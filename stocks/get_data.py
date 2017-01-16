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

def download(ticker, file_name,logger):
    url = 'http://www.google.com/finance/historical?startdate=%s&enddate=%s&output=csv&q=%s'%('Jan 03, 2000','Dec 31, 2016',ticker.lower())
    status = urlopen(url).getcode()
    if status == 200:
        logger.info('Downloading %s data to file: %s'%(ticker, file_name))
        urlretrieve(url, file_name)
        return True
    else:
        logger.info('File not found. Please check settings!')
        return False

def data_available(m,logger):
    dir_name = 'historicalData/'
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    file_name = '%s%s.csv'%(dir_name, m.lower())
    if os.path.exists(file_name):
        print('%s exists'%file_name)
        return True
    else:
        try:
            assert(download(m, file_name,logger))
            return True
        except AssertionError:
            logger.exception("%s not found. Ommitting!"%file_name)
            return False   

def download_security_list(exchange, logger):

    file_name = '%s.txt'%exchange.lower()
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


logger = get_logger()
markets = []
exchange='stocks'
#Download list of securities
assert(download_security_list(exchange, logger))
if len(markets)==0:
    file_name = '%s.txt'% exchange.lower()
    markets = [line.strip() for line in open(file_name)]

print(markets)
market_to_drop = []
for market in markets:
    print('checking %s'%market)
    is_avail = data_available( market, logger)
    print(' %s available'%market)
    if not is_avail:
        markets.remove(market)

file_name = '%s_update.txt'% exchange.lower()
f = open(file_name,'w')
for m in markets:
    print(m)
    f.write('%s'%m)
    f.write('\n')

print('Done')



