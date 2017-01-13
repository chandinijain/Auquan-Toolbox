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


def backtest(exchange, markets, trading_strategy, date_start, date_end, lookback, budget=1000000, verbose=False, base_index='INX'):

    logger = get_logger()

    #Verify Settings

    try:
        assert(isinstance(lookback, int)),"Lookback is invalid"
    except AssertionError:
            logger.exception("Lookback is invalid")
            raise

    #Load data for backtest
   
    (back_data, date_range) = load_data(exchange, markets, date_start, date_end, lookback,logger)
    logger.info('Initial funds: %0.2f'%budget)
    logger.info('------------------------------------')
    logger.info('Evaluating...')

    budget_curr = budget
    
    position_curr = back_data['POSITION'].iloc[lookback - 1]
    margin_curr = back_data['MARGIN'].iloc[lookback - 1]
    back_data['VALUE'].iloc[0:lookback] = budget
    back_data['FUNDS'].iloc[0:lookback] = budget
    res = []
    for end in range(lookback, date_range.size):
        start = end - lookback

        # get order and verify
        lookback_data = {feature: data[start: end] for feature, data in back_data.items()}
        order = trading_strategy(lookback_data)
        order['QUANTITY'] = order['QUANTITY'].astype(int)
        try:
            assert((order['SIGNAL'].isin([-1,0,1])).all())
        except AssertionError:
            logger.info("Signal can only be -1(sell), 0(hold) or 1(buy)")
            raise
        try:
            assert((order['PRICE']>=0).all())
            assert((order['QUANTITY']>=0).all()),"Quantity cannot be negative"
        except AssertionError:
            logger.info("Price cannot be negative")
            raise
        try:
            assert((order['QUANTITY']>=0).all())
        except AssertionError:
            logger.info("Quantity cannot be negative")
            raise

        # evaluate new position based on order and budget
        
        slippage = back_data['LOW'].iloc[end - 1]
        price_curr = back_data['OPEN'].iloc[end]
        open_curr = back_data['OPEN'].iloc[end]
        close_curr = back_data['CLOSE'].iloc[end]
        open_last = back_data['OPEN'].iloc[end-1]
        close_last = back_data['CLOSE'].iloc[end-1]
        high = back_data['HIGH'].iloc[end - 1]
        low = back_data['LOW'].iloc[end - 1]
        slippage = (high - low)* 0.05
        position_last = back_data['POSITION'].iloc[end - 1]
        pv_last = back_data['VALUE'].iloc[end-1]
        (position_curr, budget_curr, margin_curr, cost_to_trade) = execute_order(order, position_last, slippage, price_curr, budget_curr,margin_curr,logger)

        # set info in back data
        back_data['POSITION'].iloc[end] = position_curr
        back_data['ORDER'].iloc[end] = order['QUANTITY']*order['SIGNAL']
        filled_order = position_curr - position_last
        back_data['FILLED_ORDER'].iloc[end] = filled_order



        # calculate pnl
        pnl_curr = (position_curr * (close_curr  - open_curr) + position_last * (open_curr - close_last)) - cost_to_trade
        back_data['DAILY_PNL'].iloc[end] = pnl_curr
        back_data['TOTAL_PNL'].iloc[end] = pnl_curr + back_data['TOTAL_PNL'].iloc[end - 1]

        # available funds
        back_data['FUNDS'].iloc[end] = budget_curr

        #funds used as margin
        back_data['MARGIN'].iloc[end] = margin_curr

        #portfolio value
        value_curr = budget_curr + margin_curr + (position_curr * close_curr).sum()#back_data['TOTAL_PNL'].iloc[end].sum()
        back_data['VALUE'].iloc[end] = value_curr

        #cost
        back_data['COST TO TRADE'].iloc[end] = cost_to_trade

        #print to STDOUT
        logger.info(date_range[end].strftime('Trading date :%d %b %Y'))
        if verbose:
            s = 'stocks         : %s'%markets+'\n'+\
            'today open     : %s'%open_curr.values+'\n'+\
            'today close    : %s'%close_curr.values+'\n'+\
            'order          : %s'%(order['QUANTITY']*order['SIGNAL']).values+'\n'+\
            'position       : %s'%position_curr.values+'\n'+\
            'cost to trade  : %0.2f'%cost_to_trade.sum()+'\n'+\
            'Available funds: %0.2f'%budget_curr+'\n'+\
            'Margin funds   : %0.2f'%margin_curr+'\n'+\
            'pnl            : %0.2f'%pnl_curr.sum()+'\n'+\
            'Portfolio Value: %0.2f'%value_curr+'\n'+\
            '------------------------------------'
            logger.info(s)
        
        if value_curr<=0:
            logger.info('Out of funds. Exiting!')
            break
            
    logger.info('Final Portfolio Value: %0.2f'%value_curr)
    #writejson(back_data,budget)
    writecsv({feature: data[lookback-1: end+1] for feature, data in back_data.items()},budget)

    logger.info('Plotting Results...')

    loadgui({feature: data[lookback-1: end+1] for feature, data in back_data.items()}, exchange, base_index, budget,logger)

        #back_data['DAILY_PNL'][date_start:date_end], back_data['TOTAL_PNL'][date_start:date_end], back_data['POSITION'][date_start:date_end], exchange, base_index, budget,logger)


def commission():
    return 0.1

def margin_perc():
    return 1

def execute_order(order, position, slippage, price, budget,margin,logger):
    if pd.isnull(price[order['QUANTITY'] != 0]).values.any():
        logger.info('Cannot place order for markets with price unavailable! Order cancelled.')
        return position, budget, margin,0*position
    elif budget <=0:
        logger.info('You do not have enough funds to trade! Order cancelled.')
        return position, budget, margin,0*position
    else:
        (position_after_sell, budget_after_sell, margin_after_sell, cost_to_sell) = execute_sell(order, position, slippage, price, budget,margin,logger)
        if budget_after_sell==0:
            logger.info(order['SIGNAL']*order['QUANTITY'])
            logger.info('You do not have any funds to trade! Buy Order cancelled.')
            return position_after_sell, budget_after_sell, margin_after_sell, cost_to_sell
        else:
            (position_after_buy, budget_after_buy, margin_after_buy, cost_to_buy) = execute_buy(order, position_after_sell, slippage, price, budget_after_sell, margin_after_sell,logger)
            return position_after_buy, budget_after_buy, margin_after_buy, cost_to_sell+cost_to_buy

def execute_sell(order, position, slippage, price, budget,margin,logger):
    position_curr = position.copy()
    trade_criteria_1 = order['SIGNAL'] < 0
    trade_criteria_2 = (order['PRICE'] <= price[order.index])
    trade_criteria_2[order['PRICE'] > price[order.index]] = order['PRICE'] ==0
    margin_call = 0

    position_curr[trade_criteria_1 & trade_criteria_2] -= order['QUANTITY'][trade_criteria_1 & trade_criteria_2]

    #identify shortsell orders and calculate margin
    margin_call = -(position_curr[position_curr < 0] * price[position_curr < 0]).sum()*margin_perc()
    if (margin_call-margin)*(1-1/float(margin_perc()))  > budget:
        logger.info(order['SIGNAL']*order['QUANTITY'])
        logger.info('Short Sell order value exceeds available funds! Short Sell order cancelled.')
        position_curr[ position_curr < 0] = position[ position_curr < 0]
        margin_call = -(position_curr[position_curr < 0] * price[position_curr < 0]).sum()*margin_perc()

    adj_commission = (position - position_curr) * commission()
    slippage_adjusted_price = price - slippage
    slippage_adjusted_price[slippage_adjusted_price < 0] = 0
    adj_slippage = ((position - position_curr)*(price - slippage_adjusted_price))
    order_value = ((position-position_curr) * price).sum()
    total_commission=adj_commission.sum()
    total_slippage = adj_slippage.sum()
   
    cost_to_sell = adj_commission + adj_slippage
    return position_curr, budget + (order_value - (margin_call-margin)) - total_commission - total_slippage, margin_call, cost_to_sell

def execute_buy(order, position, slippage, price, budget, margin,logger):
    position_curr = position.copy()
    trade_criteria_1 = order['SIGNAL'] > 0
    trade_criteria_2 = (order['PRICE'] >= price[order.index])
    trade_criteria_2[order['PRICE'] < price[order.index]] = order['PRICE'] ==0
    margin_call = 0

    position_curr[trade_criteria_1 & trade_criteria_2] += order['QUANTITY'][trade_criteria_1 & trade_criteria_2]
    
    #identify shortsell orders and calculate margin
    margin_call = -(position_curr[position_curr < 0] * price[position_curr < 0]).sum()*margin_perc()

    adj_commission = (position_curr-position) * commission()
    adj_slippage = ((position_curr-position) * slippage)
    order_value = ((position_curr-position) * price).sum()
    total_commission=adj_commission.sum()
    total_slippage = adj_slippage.sum()

    #check if you can execute buy orders
    if ((order_value - (margin-margin_call)) + total_commission + total_slippage) >= budget:
        logger.info(order['SIGNAL']*order['QUANTITY'])
        logger.info('Buy order exceeds available funds! Buy order cancelled.')
        position_curr[ trade_criteria_1 & position_curr > 0] = position[ trade_criteria_1 & position_curr > 0]
        adj_commission = (position_curr-position) * commission()
        adj_slippage = ((position_curr-position) * slippage)
        order_value = ((position_curr-position) * price).sum()
        total_commission=adj_commission.sum()
        total_slippage = adj_slippage.sum()

    #check if you can execute order to buyback short sells
    if ((order_value - (margin-margin_call)) + total_commission + total_slippage) >= budget:
        logger.info('Not enough funds to Buy! Complete Buy Order cancelled')
        return position, budget, margin, 0*position
    else:
        cost_to_buy = adj_commission + adj_slippage
        return position_curr, budget - (order_value - (margin-margin_call)) - total_commission - total_slippage, margin_call, cost_to_buy

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

def writecsv(back_data,budget):

    results = pd.DataFrame(0, index=back_data['DAILY_PNL'].index, columns=['Daily Returns'])
    results['Daily Returns'] = back_data['DAILY_PNL'].sum(axis=1)*100/budget
    results['Total Returns'] = back_data['TOTAL_PNL'].sum(axis=1)*100/budget
    results['Funds'] = back_data['FUNDS']
    results['Portfolio Value'] = back_data['VALUE']
    for stock in back_data['DAILY_PNL'].columns.tolist():
        results['%s Position'%stock]= back_data['POSITION'][stock]
        results['%s Order'%stock]=back_data['ORDER'][stock]
        results['%s Filled Order'%stock]=back_data['FILLED_ORDER'][stock]
        results['%s Trade Price'%stock]=back_data['OPEN'][stock]
        results['%s Cost to Trade'%stock]=back_data['COST TO TRADE'][stock]
        results['%s PnL'%stock]=back_data['DAILY_PNL'][stock]

    results = results.sort_index(axis=0,ascending=False)
    csv_dir = 'runLogs/'
    try:
        csv_file =  open('%srun-%s.csv'%(csv_dir, dt.datetime.now().strftime('%Y-%m-%d %H-%M-%S')), 'wb')
        results.to_csv(csv_file)
    except:
        csv_file =  open('%srun-%s.csv'%(csv_dir, dt.datetime.now().strftime('%Y-%m-%d %H-%M-%S')), 'w')
        results.to_csv(csv_file)
    # writer = csv.writer(csv_file)
    # writer.writerow(['Dates']+back_data['DAILY_PNL'].index.format())
    # writer.writerow(['Daily Pnl']+daily_return.sum(axis=1).values.tolist())
    # writer.writerow(['Total PnL']+total_return.sum(axis=1).values.tolist())
    # writer.writerow(['Funds']+back_data['FUNDS'].values.tolist())
    # writer.writerow(['Portfolio Value']+back_data['VALUE'].values.tolist())
    # for stock in back_data['DAILY_PNL'].columns.tolist():
    #     writer.writerow(['%s Position'%stock]+back_data['POSITION'][stock].values.tolist())
    #     writer.writerow(['%s Order'%stock]+back_data['ORDER'][stock].values.tolist())
    #     writer.writerow(['%s Filled Order'%stock]+back_data['FILLED_ORDER'][stock].values.tolist())
    #     writer.writerow(['%s Slippage'%stock]+back_data['SLIPPAGE'][stock].values.tolist())
    #     writer.writerow(['%s PnL'%stock]+back_data['DAILY_PNL'][stock].values.tolist())
    csv_file.close()

def writejson(back_data,budget):

    daily_return = back_data['DAILY_PNL']*100/budget
    total_return = back_data['TOTAL_PNL']*100/budget

    d = {'dates':back_data['DAILY_PNL'].index.format(),\
         'daily PnL':daily_return.sum(axis=1).values.tolist(),\
         'total PnL':total_return.sum(axis=1).values.tolist(),\
         'stocks':back_data['DAILY_PNL'].columns.tolist(),\
         'stock PnL':daily_return.values.tolist(),\
         'stock Position':back_data['POSITION'].values.tolist()}
    print(json.dumps(d))


