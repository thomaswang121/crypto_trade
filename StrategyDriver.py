from concurrent.futures import thread
import Strategy
import os
import time
from DataManager import CryptoData
from AccountManager import AccountInfomation
from ConnectionKeeper import Connection
import threading

def run(**kwargs):
    rs = kwargs['rs']
    ws = kwargs['ws']

    # strategy 1
    symbol = 'BTCBUSD'
    flen = 5
    slen = 5
    timeframe = 'hour'
    interval = 1
    strategy_id = 'Momentumi'
    fund = 10
    lever = 3
    
    # strategy 2
    symbol_2 = 'BTCBUSD'
    flen_2 = 4
    slen_2 = 72
    timeframe_2 = 'hour'
    interval_2 = 1
    strategy_id_2 = 'Momentumii'
    fund_2 = 20
    lever_2 = 3

    # strategy 3
    symbol_3 = 'BTCBUSD'
    flen_3 = 8
    slen_3 = 180
    timeframe_3 = 'hour'
    interval_3 = 1
    strategy_id_3 = 'Momentumiii'
    fund_3 = 20
    lever_3 = 3

    # strategy 4
    symbol_4 = 'BTCBUSD'
    flen_4 = 160
    slen_4 = 176
    timeframe_4 = 'hour'
    interval_4 = 1
    strategy_id_4 = 'Momentumiv'
    fund_4 = 20
    lever_4 = 3

    # strategy 5
    symbol_5 = 'BTCBUSD'
    flen_5 = 215
    slen_5 = 247
    timeframe_5 = 'hour'
    interval_5 = 1
    strategy_id_5 = 'Momentumv'
    fund_5 = 20
    lever_5 = 3

    # initialize data object
    crypto_data = CryptoData(rs, ws, 'BTCBUSD')
    # crypto_data.regist_double_sma_strategy(strategy_id, timeframe, interval, slen, crypto_data.handle_1h_kline)
    crypto_data.regist_double_sma_strategy(strategy_id_2, timeframe_2, interval_2, slen_2, crypto_data.handle_1h_kline)
    crypto_data.regist_double_sma_strategy(strategy_id_3, timeframe_3, interval_3, slen_3, crypto_data.handle_1h_kline)
    crypto_data.regist_double_sma_strategy(strategy_id_4, timeframe_4, interval_4, slen_4, crypto_data.handle_1h_kline)
    crypto_data.regist_double_sma_strategy(strategy_id_5, timeframe_5, interval_5, slen_5, crypto_data.handle_1h_kline)

    # update account infomation in real time
    account_info = AccountInfomation(rs, ws)

    # Must register strategy !!!
    # account_info(strategy_id, account_info.handle_ma_order)
    account_info(strategy_id_2, account_info.handle_ma_order)
    account_info(strategy_id_3, account_info.handle_ma_order)
    account_info(strategy_id_4, account_info.handle_ma_order)
    account_info(strategy_id_5, account_info.handle_ma_order)
    account_info.get_current_account_info(symbol)
    account_info.start_detecting_account_event()

    time.sleep(0.5)

    # initialize strategy object
    # momentum = Strategy.DoubleSma(rs, ws, account_info, crypto_data, symbol, flen, slen, fund, lever, strategy_id)
    momentum_2 = Strategy.DoubleSma(rs, ws, account_info, crypto_data, symbol_2, flen_2, slen_2, fund_2, lever_2, strategy_id_2)
    momentum_3 = Strategy.DoubleSma(rs, ws, account_info, crypto_data, symbol_3, flen_3, slen_3, fund_3, lever_3, strategy_id_3)
    momentum_4 = Strategy.DoubleSma(rs, ws, account_info, crypto_data, symbol_4, flen_4, slen_4, fund_4, lever_4, strategy_id_4)
    momentum_5 = Strategy.DoubleSma(rs, ws, account_info, crypto_data, symbol_5, flen_5, slen_5, fund_5, lever_5, strategy_id_5)
    
    # t1 = threading.Thread(target=momentum.launch_strategy, name="Strategy1", daemon=True)
    t2 = threading.Thread(target=momentum_2.launch_strategy, name="Strategy2", daemon=True)
    t3 = threading.Thread(target=momentum_3.launch_strategy, name="Strategy3", daemon=True)
    t4 = threading.Thread(target=momentum_4.launch_strategy, name="Strategy4", daemon=True)
    t5 = threading.Thread(target=momentum_5.launch_strategy, name="Strategy5", daemon=True)

    # t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()

    # t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()

    return

if __name__ == "__main__":
    run()