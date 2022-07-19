from binance import ThreadedWebsocketManager
from binance.client import Client
from typing import List, Any
from collections import defaultdict
import sys

class CryptoData(object):

    real_time_data = {
        'best_bid':0.0,
        'best_ask':0.0
    }
    def __init__(self, rs: Client, ws: ThreadedWebsocketManager, symbol: str) -> None:
        self.symbol = symbol
        self.rest_client = rs
        self.ws_client = ws

    def get_from_rest(self, length, time_params) -> List:
        
        self.rest_client.API_URL = 'https://api.binance.com/api'
        
        info = self.rest_client.futures_historical_klines(self.symbol, 
                                                time_params[1],
                                                time_params[0],  
                                                limit=length)
        # last record is not finished
        return [float(info[ele][4]) for ele in range(len(info)-1)]

    def get_from_websocket_stream(self, **kwargs):
        
        if kwargs['type'] == 'kline':
            self.ws_client.start_kline_futures_socket(callback=self.handle_ma_socket_message, 
                                    symbol=self.symbol, 
                                    interval=kwargs['interval']
                                    )

        elif kwargs['type'] == 'bookticker':
            self.ws_client.start_symbol_ticker_futures_socket(callback=self.handle_bookticker_info, symbol=self.symbol)
            
    
    def handle_ma_socket_message(self, msg):
        try:
            if msg['ps'] != self.symbol:
                raise ValueError('The symbol is not correct')

        except:
            sys.exit()
        
        # each 15 mins update data? 
        # print(f"start: {msg['k']['t']}  end: {msg['k']['T']}  close: {msg['k']['c']}\n")
        
        # This record is not finished
        if (not (msg['k']['x'])):
            return
        
        self.ma_data['kline'].append(float(msg['k']['c']))
        self.ma_data['kline'].pop(0)
        

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
            self.ws_client.start_symbol_ticker_futures_socket(callback=self.handle_bookticker_info, symbol=self.symbol)
            

    def handle_strategy_data(self, malen=5, interval=15):
        self.ma_data = {}
        time_params = [f"{interval * (malen+1)} mins ago UTC", f"{interval}m"]
        # get the last 5 close price (hours) maybe SubKlineFuturesEndPoint
        self.ma_data['kline'] = self.get_from_rest(malen, time_params)

        # Could there be a problem with the last data?
        self.get_from_websocket_stream(type='kline', interval=f"{interval}m")
        self.get_from_websocket_stream(type='bookticker')
        
    def _ping_server(self):
        pass
