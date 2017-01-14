from __future__ import absolute_import, division, print_function, unicode_literals
try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
import matplotlib
import os
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import style
import matplotlib.pyplot as plt
import csv
import json

def download(exchange, ticker, file_name):
    url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/%s/historicalData/%s.csv'%(exchange.lower(), ticker.lower())
    print('Downloading %s data to file: %s'%(ticker, file_name))
    urlretrieve(url, file_name)

def data_available(exchange, markets):
    dir_name = '%s/historicalData/'%exchange.lower()
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    for m in markets:
        file_name = '%s%s.csv'%(dir_name, m.lower())
        if not os.path.exists(file_name):
            download(exchange, m, file_name)
    return True

def load_data(exchange, markets, start, end, random=False):
    markets = [m.upper() for m in markets]
    features = ['OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME']
    date_range = pd.date_range(start=start, end=end, freq='B')
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
                back_data[feature][market] = csv[feature]

        dates_to_drop = pd.Series(False, index=date_range)
        for feature in features:
            dates_to_drop |= pd.isnull(back_data[feature]).any(axis=1)

        dropped_dates = date_range[dates_to_drop]
        date_range = date_range[~dates_to_drop]
        for feature in features:
            back_data[feature] = back_data[feature].drop(dropped_dates)

    back_data['SLIPPAGE'] = (back_data['HIGH'] - back_data['LOW']).abs() * 0.005
    back_data['POSITION'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['ORDER'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['FILLED_ORDER'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['DAILY_PNL'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['TOTAL_PNL'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['FUNDS'] = pd.Series(0, index=date_range)
    back_data['VALUE'] = pd.Series(0, index=date_range)
    return back_data, date_range

def commission():
    return 0.1

def backtest(case, exchange, markets, trading_strategy, start, end, lookback, budget=100000, verbose=False, base_index='INX'):

    #Load data for backtest
    print("Loading Data from %s to %s...."%(start,end))
    dates = [start, end]
    dates = [d.date() for d in pd.to_datetime(dates)]
    (back_data, date_range) = load_data(exchange, markets, dates[0]-BDay(lookback), dates[1])

    if date_range[0] > dates[0]-BDay(lookback):
        print("Lookback exceeds Available data. Backtest starts from %s"%date_range[0])
    print('Initial funds: %0.2f'%budget)
    print('------------------------------------')
    budget_curr = budget
    
    #csv_file =  open('data_problem%s.csv'%case, 'wb')
    #writer = csv.writer(csv_file)
    #s = ['DATE','STOCK','POSITION','ORDER','FILLED_ORDER','SLIPPAGE','DAILY_PNL','FUNDS','PORTFOLIO_VALUE']
    #writer.writerow(s)
    
    position_curr = back_data['POSITION'].iloc[lookback - 1]
    res = []
    for end in range(lookback, date_range.size):
        start = end - lookback

        # get order
        lookback_data = {feature: data[start: end] for feature, data in back_data.items()}
        order = trading_strategy(lookback_data, markets, budget_curr)

        # evaluate new position based on order and budget
        price_curr = back_data['OPEN'].iloc[end]
        slippage = back_data['SLIPPAGE'].iloc[end - 1]
        position_last = back_data['POSITION'].iloc[end - 1]
        (position_curr, budget_curr, cost_to_trade) = execute_order(case,order, position_last, slippage, price_curr, budget_curr)

        # set info in back data
        back_data['POSITION'].iloc[end] = position_curr
        back_data['ORDER'].iloc[end] = order['QUANTITY']
        filled_order = position_curr - position_last
        back_data['FILLED_ORDER'].iloc[end] = filled_order

        open_curr = back_data['OPEN'].iloc[end]
        close_curr = back_data['CLOSE'].iloc[end]
        open_last = back_data['OPEN'].iloc[end-1]
        close_last = back_data['CLOSE'].iloc[end-1]

        # calculate pnl
        pnl_curr = (position_curr * (close_curr  - open_curr) + position_last * (open_curr - close_last)) - cost_to_trade
        back_data['DAILY_PNL'].iloc[end] = pnl_curr
        back_data['TOTAL_PNL'].iloc[end] = pnl_curr + back_data['TOTAL_PNL'].iloc[end - 1]

        # available funds
        back_data['FUNDS'].iloc[end] = budget_curr

        #portfolio value
        value_curr = budget + back_data['TOTAL_PNL'].iloc[end].sum()
        back_data['VALUE'].iloc[end] = value_curr

        #print to STDOUT
        print(date_range[end].strftime('Trading date :%d %b %Y'))
        if verbose:
            print('stocks         : %s'%markets)
            print('today open     : %s'%open_curr.values)
            print('today close    : %s'%close_curr.values)
            print('order          : %s'%order['QUANTITY'].values)
            print('position       : %s'%position_curr.values)
            print('cost to trade  : %0.2f'%cost_to_trade)
            print('pnl            : %0.2f'%pnl_curr.sum())
        print('Available funds: %0.2f'%budget_curr)
        print('Portfolio Value: %0.2f'%value_curr)
        print('------------------------------------')
        #s = [date_range[end].strftime('%d %b %Y'),markets,position_curr.values,order['QUANTITY'].values,filled_order.values,slippage.values,pnl_curr.values,budget_curr,value_curr]
        #writer.writerow(s)

    #csv_file.close()
    print('Final Portfolio Value: %0.2f'%value_curr)
    plot(case,back_data['DAILY_PNL'], back_data['TOTAL_PNL'], exchange, base_index, budget)
    writejson(back_data,case,budget)
    writecsv(back_data,case,budget)

def writecsv(back_data,case,budget):

    daily_return = back_data['DAILY_PNL']
    total_return = back_data['TOTAL_PNL']

    if case == 3:
        daily_return = daily_return*100/budget
        total_return = total_return*100/budget
    csv_file =  open('OUTPUT_Problem%s.csv'%case, 'wb')
    writer = csv.writer(csv_file)
    writer.writerow(['Dates']+back_data['DAILY_PNL'].index.format())
    writer.writerow(['Daily Pnl']+daily_return.sum(axis=1).values.tolist())
    writer.writerow(['Total PnL']+total_return.sum(axis=1).values.tolist())
    if case == 3:
        writer.writerow(['Funds']+back_data['FUNDS'].values.tolist())
        writer.writerow(['Portfolio Value']+back_data['VALUE'].values.tolist())
    for stock in back_data['DAILY_PNL'].columns.tolist():
        writer.writerow(['%s Position'%stock]+back_data['POSITION'][stock].values.tolist())
        writer.writerow(['%s Order'%stock]+back_data['ORDER'][stock].values.tolist())
        writer.writerow(['%s Filled Order'%stock]+back_data['FILLED_ORDER'][stock].values.tolist())
        writer.writerow(['%s Slippage'%stock]+back_data['SLIPPAGE'][stock].values.tolist())
        writer.writerow(['%s PnL'%stock]+back_data['DAILY_PNL'][stock].values.tolist())
    csv_file.close()

def writejson(back_data,case,budget):

    daily_return = back_data['DAILY_PNL']
    total_return = back_data['TOTAL_PNL']

    if case == 3:
        daily_return = daily_return*100/budget
        total_return = total_return*100/budget

    d = {'dates':back_data['DAILY_PNL'].index.format(),\
         'daily PnL':daily_return.sum(axis=1).values.tolist(),\
         'total PnL':total_return.sum(axis=1).values.tolist(),\
         'stocks':back_data['DAILY_PNL'].columns.tolist(),\
         'stock PnL':daily_return.values.tolist(),\
         'stock Position':back_data['POSITION'].values.tolist()}
    print(json.dumps(d))

def execute_order(case,order, position, slippage, price, budget):
    if pd.isnull(price[order['QUANTITY'] != 0]).values.any():
        print('Cannot place order for markets with price unavailable! Order cancelled.')
        return position, budget, 0
    else:
        (position_after_sell, budget_after_sell, cost_to_sell) = execute_sell(case,order, position, slippage, price, budget)
        (position_after_buy, budget_after_buy, cost_to_buy) = execute_buy(case,order, position_after_sell, slippage, price, budget_after_sell)
        return position_after_buy, budget_after_buy, cost_to_sell+cost_to_buy

def execute_sell(case, order, position, slippage, price, budget):
    position_curr = position.copy()
    trade_criteria_1 = order['QUANTITY'] < 0
    trade_criteria_2 = (order['PRICE'] <= price[order.index])
    if case == 1:
        position_curr[trade_criteria_1] += order['QUANTITY'][trade_criteria_1]
    else:
        position_curr[trade_criteria_1 & trade_criteria_2] += order['QUANTITY'][trade_criteria_1 & trade_criteria_2]

    if case == 3 and (position_curr < 0).any():
            print('Short selling not supported! Selling available quantity.')
            position_curr[position_curr < 0] = 0

    total_commission = (position - position_curr).sum() * commission()
    slippage_adjusted_price = price - slippage
    slippage_adjusted_price[slippage_adjusted_price < 0] = 0
    total_slippage = ((position - position_curr)*(price - slippage_adjusted_price)).sum()
    order_value = ((position_curr-position) * price).sum()

    if case == 1:
        total_commission = 0
        total_slippage = 0

    if case == 3 and total_commission > budget:
        print('Sell order exceeds budget! Sell order cancelled.')
        return position, budget, 0
    else:   
        cost_to_sell = total_commission + total_slippage
        return position_curr, budget + order_value - total_commission - total_slippage, cost_to_sell

def execute_buy(case,order, position, slippage, price, budget):
    position_curr = position.copy()
    trade_criteria_1 = order['QUANTITY'] > 0
    trade_criteria_2 = (order['PRICE'] >= price[order.index])
    if case == 1:
        position_curr[trade_criteria_1] += order['QUANTITY'][trade_criteria_1]
    else:
        position_curr[trade_criteria_1 & trade_criteria_2] += order['QUANTITY'][trade_criteria_1 & trade_criteria_2]
    
    total_commission = (position_curr-position).sum() * commission()
    total_slippage = ((position_curr-position) * slippage).sum()
    order_value = ((position_curr-position) * price).sum()

    if case == 1:
        total_commission = 0
        total_slippage = 0

    if case == 3 and (order_value + total_commission + total_slippage) > budget:
        print('Buy order exceeds budget! Buy order cancelled.')
        return position, budget, 0
    else:
        cost_to_buy = total_commission + total_slippage
        return position_curr, budget - order_value - total_commission - total_slippage, cost_to_buy

def plot(case,daily_pnl, total_pnl, exchange, base_index, budget):
    
    daily_return = daily_pnl.sum(axis=1)
    total_return = total_pnl.sum(axis=1)

    plt.close('all')
    zero_line = np.zeros(daily_pnl.index.size)
    f, plot_arr = plt.subplots(2, sharex=True)
    
    if case !=3:
        stats = 'total pnl: %0.2f'%(total_pnl.iloc[total_pnl.index.size-1].sum())
        plot_arr[0].set_title('Daily PnL')
        plot_arr[1].set_title('Total PnL')

    if case == 3:
        daily_return = daily_return*100/budget
        total_return = total_return*100/budget
        baseline_data = baseline(exchange, base_index, total_pnl.index)
        
        stats = 'total pnl: %0.2f'%(total_pnl.iloc[total_pnl.index.size-1].sum()) + '\n' + \
            'annualized return: %0.2f%%'%annualized_return(daily_return) + '\n' + \
            'annual vol: %0.2f%%'%annual_vol(daily_return) + '\n' + \
            'beta: %0.2f'%beta(daily_return,baseline_data['DAILY_PNL']) + '\n' + \
            'sharpe ratio: %0.2f'%sharpe_ratio(daily_return) + '\n' + \
            'sortino ratio: %0.2f'%sortino_ratio(daily_return) + '\n' + \
            'max drawdown: %0.2f'%max_drawdown(daily_return)
        plot_arr[0].set_title('Daily % PnL')
        plot_arr[1].set_title('Total % PnL')
        plot_arr[0].plot(daily_pnl.index, baseline_data['DAILY_PNL'], label='s&p500')
        plot_arr[1].plot(daily_pnl.index, baseline_data['TOTAL_PNL'], label='s&p500')
        

    f.text(0.01, 0.99, stats, transform=plot_arr[0].transAxes, fontsize=12,
           verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    plot_arr[0].plot(daily_pnl.index, zero_line)
    plot_arr[0].plot(daily_pnl.index, daily_return.values, label='strategy')
    plot_arr[0].legend(loc='upper left')
    plot_arr[1].plot(total_pnl.index, zero_line)
    plot_arr[1].plot(total_pnl.index, total_return.values, label='strategy')
    plot_arr[1].legend(loc='upper left')

    plt.show()

    print(stats)

def annualized_return(daily_return):
    total_return = daily_return.sum()
    total_days = daily_return.index.size
    return (1 + total_return)**(252 / total_days) - 1

def annualized_std(daily_return):
    return np.sqrt(252)*np.std(daily_return)

def annualized_downside_std(daily_return):
    mar = 0
    downside_return = daily_return.copy()
    downside_return[downside_return > 0]= 0
    return np.sqrt(252)*np.std(downside_return)

def annual_vol(daily_return):
    return annualized_std(daily_return)

def sharpe_ratio(daily_return):
    stdev = annualized_std(daily_return)
    if stdev == 0:
        return np.nan
    else:
        return annualized_return(daily_return)/stdev

def sortino_ratio(daily_return):
    stdev = annualized_downside_std(daily_return)
    if stdev == 0:
        return np.nan
    else:
        return annualized_return(daily_return)/stdev

def max_drawdown(daily_return):
    return np.max(np.maximum.accumulate(daily_return) - daily_return)

def beta(daily_return, baseline_daily_return):
    stdev = np.std(baseline_daily_return)
    if stdev == 0:
        return np.nan
    else:
        return np.corrcoef(daily_return, baseline_daily_return)[0,1]*np.std(daily_return)/stdev

def alpha(daily_return, baseline_daily_return,beta):
    return annualized_return(daily_return) - beta*annualized_return(baseline_daily_return)

def baseline(exchange, base_index, date_range):
    features = ['OPEN', 'CLOSE']
    baseline_data = {}

    assert data_available(exchange, [base_index])
    csv = pd.read_csv('nasdaq/historicalData/%s.csv'%base_index.lower(), index_col=0)
    csv.index = pd.to_datetime(csv.index)
    csv.columns = [col.upper() for col in csv.columns]
    csv = csv.reindex(index=csv.index[::-1])
    #features = [col.upper() for col in csv.columns]

    for feature in features:
        baseline_data[feature] = pd.Series(index=date_range)
        baseline_data[feature] = csv[feature]

    baseline_data['DAILY_PNL'] = pd.Series(0, index=date_range)
    baseline_data['TOTAL_PNL'] = pd.Series(0, index=date_range)

    open_start = baseline_data['OPEN'].iloc[0]
    for end in range(0, date_range.size):
        close_curr = baseline_data['CLOSE'].iloc[end]
        close_last = baseline_data['CLOSE'].iloc[end-1]
        if end == 0:
            close_last = open_start
        pnl_curr = (close_curr - close_last) * 100 / open_start

        baseline_data['DAILY_PNL'].iloc[end] = pnl_curr
        baseline_data['TOTAL_PNL'].iloc[end] = pnl_curr + baseline_data['TOTAL_PNL'].iloc[end - 1]

    return baseline_data

def analyze(exchange, markets, start, end):
    (back_data, days) = load_data(exchange, markets, start, end)
    plt.close('all')
    f, plot_arr = plt.subplots(2, sharex=True)
    plot_arr[0].set_title('Open')
    plot_arr[1].set_title('Close')
    for m in markets:
        plot_arr[0].plot(back_data['OPEN'].index, back_data['OPEN'][m], label=m)
        plot_arr[1].plot(back_data['OPEN'].index, back_data['CLOSE'][m], label=m)
    plot_arr[0].legend(loc='upper center')
    plot_arr[1].legend(loc='upper center')
    plt.show()
