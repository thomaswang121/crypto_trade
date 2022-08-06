from distutils.log import error
from binance import ThreadedWebsocketManager
from binance.client import Client
from typing import List, Any
from collections import defaultdict
from typing import Callable
from datetime import datetime
import pathlib

class CryptoData(object):
    _sub_list = []
    real_time_data = {
        'best_bid':0.0,
        'best_ask':0.0
    }
    data_kline = {}
    update_hour_flag = {}
    update_min_flag = {}

    def __init__(self, rs: Client, ws: ThreadedWebsocketManager, symbol: str) -> None:
        self.symbol = symbol
        self.rest_client = rs
        self.ws_client = ws
        self._folder = pathlib.Path().cwd() / "DataError"
        if not self._folder.exists():                            
            self._folder.mkdir(parents=True, exist_ok=True) 
        self.rest_client.API_URL = 'https://api.binance.com/api'
        
        exchange_info = self.rest_client.futures_exchange_info()
        symbol_info = [s for s in exchange_info['symbols'] if 'BTCBUSD' in s.values()][0]
        self.qprecision = symbol_info['quantityPrecision']
        
        self.ws_client.start_symbol_ticker_futures_socket(callback=self.handle_bookticker_info, symbol=self.symbol)


    def regist_double_sma_strategy(self, strategy_id: str, timeframe: str ,interval: str, slen: int,func: Callable):
        self.data_kline[strategy_id] = []

        if timeframe == 'hour':
            time_params = [f"{interval * (slen+2)} hours ago UTC", f"{interval}h"]
            self.update_hour_flag[strategy_id] = False
        
        elif timeframe == 'min':
            time_params = [f"{interval * (slen+2)} mins ago UTC", f"{interval}m"]
            self.update_min_flag[strategy_id] = False

        # get history kline data
        self.data_kline[strategy_id] = self.get_from_rest(slen+1, time_params)
        
        # Avoid duplicate subscriptions
        if time_params[1] not in self._sub_list:
            self.ws_client.start_kline_futures_socket(callback=func, 
                                    symbol=self.symbol, 
                                    interval=time_params[1]
                                    )
            self._sub_list.append(time_params[1])
        
    def get_from_rest(self, length, time_params) -> List:
        
        info = self.rest_client.futures_historical_klines(self.symbol, 
                                                time_params[1],
                                                time_params[0],  
                                                limit=length)
        # last record is not finished
        return [float(info[ele][4]) for ele in range(len(info)-1)]
    
    def handle_1h_kline(self, msg):
        
        # each 15 mins update data? 
        # print(f"start: {msg['k']['t']}  end: {msg['k']['T']}  close: {msg['k']['c']}\n")
        if ('e' in msg.keys() and msg['e'] == 'error'):
            self.ws_client.stop_socket(self.ws_client.start_kline_futures_socket)
            self.ws_client.start_kline_futures_socket(callback=self.handle_1h_kline, 
                                    symbol=self.symbol, 
                                    interval='1h'
                                    )

        # This record is not finished
        if (not (msg['k']['x'])):
            return
        
        self.update_hour_flag = dict.fromkeys(self.update_hour_flag, True)

        # loop over every strategy data by key
        for record in self.data_kline.values():
            record.append(float(msg['k']['c']))
            record.pop(0)

    def handle_15m_kline(self, msg):
        # each 15 mins update data? 
        # print(f"start: {msg['k']['t']}  end: {msg['k']['T']}  close: {msg['k']['c']}\n")
        if ('e' in msg.keys() and msg['e'] == 'error'):
            self.ws_client.stop_socket(self.ws_client.start_kline_futures_socket)
            self.ws_client.start_kline_futures_socket(callback=self.handle_15m_kline, 
                                    symbol=self.symbol, 
                                    interval='15m'
                                    )

        # This record is not finished
        if (not (msg['k']['x'])):
            return
        
        self.update_min_flag = dict.fromkeys(self.update_min_flag, True)

        # loop over every strategy data by key
        for record in self.data_kline.values():
            record.append(float(msg['k']['c']))
            record.pop(0)
        

    def handle_bookticker_info(self, msg):
        """
        from binance error message:
        {'e':'error', 'm':'Queue Overflow, message not filled.'}
        it must restart websocket task.
        """
        if ('e' not in msg.keys()):
            self.real_time_data['best_bid'] = float(msg['data']['b'])
            self.real_time_data['best_ask'] = float(msg['data']['a'])
        
        elif ('e' in msg.keys() and msg['e'] == 'error'):
            self.ws_client.stop_socket(self.ws_client.start_symbol_ticker_futures_socket)
            self.write_error_log("bookticker restart!")
            self.ws_client.start_symbol_ticker_futures_socket(callback=self.handle_bookticker_info, symbol=self.symbol)
            
    def write_error_log(self, error_log):
        file_path = self._folder / "error.log"
        f = open(file_path, 'a')
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {error_log}\n")
        f.close()

