from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
import os
import csv
import json
import logging
import datetime as dt
from pythonToolbox.dataloader import load_data
from pythonToolbox.resultviewer import loadgui
import matplotlib.pyplot as plt


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


exchange = "stocks"           # Exchange to download data for (nyse or nasdaq)
markets = []
date_start = '2010-01-01'   # Date to start the backtest
date_end = '2016-11-06'     # Date to end the backtest
lookback = 120               # Number of days you want historical data for  
budget=10000000
logger = get_logger()
(back_data, date_range) = load_data(exchange, markets, date_start, date_end, lookback, budget, logger)
start_index = -1
bugs=[]
markets = back_data['OPEN'].columns.values.tolist()
for startDate in pd.date_range(start=date_start, end=date_end, freq='B'):
    if startDate not in date_range:
        continue
    end = date_range.get_loc(startDate)
    if start_index < 0:
        start_index = end

    start = end - lookback
    if start < 0:
        start = 0
    try:
        open_last = back_data['OPEN'].iloc[end-1].astype(float)
        close_last = back_data['CLOSE'].iloc[end-1].astype(float)
        high = back_data['HIGH'].iloc[end - 1].astype(float)
        low = back_data['LOW'].iloc[end - 1].astype(float)
        vol = back_data['VOLUME'].iloc[end - 1].astype(int)
    except ValueError:
        for m in markets:
            try:
                open_last[m] = back_data['OPEN'][m].iloc[end-1].astype(float)
                close_last[m] = back_data['CLOSE'][m].iloc[end-1].astype(float)
                high[m] = back_data['HIGH'][m].iloc[end - 1].astype(float)
                low[m] = back_data['LOW'][m].iloc[end - 1].astype(float)
                vol[m] = back_data['VOLUME'][m].iloc[end - 1].astype(int)
            except:
                bugs.append(m)
                markets.remove(m)

print(bugs)
