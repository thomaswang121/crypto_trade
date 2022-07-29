from typing import Callable
from binance import ThreadedWebsocketManager
from binance.client import Client
from datetime import datetime
import time
import re
import pathlib
import json
from binance.enums import *

class AccountInfomation(object):
    current_position = {}
    current_order = {}
    _func_dict = {}
    _log_path = {}
    _instance = None
    
    # Singleton mode
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    # account delegate
    def __call__(self, strategy_id: str, func: Callable):
        self._func_dict[strategy_id] = func

        self.current_order[strategy_id] = {}
        self.current_order[strategy_id]['order'] = []
        self.current_order[strategy_id]['flag'] = False
        
        self._log_path[strategy_id] = {}

        # create strategy log folder
        self._log_path[strategy_id]['folder'] = pathlib.Path().cwd() / strategy_id
        if not self._log_path[strategy_id]['folder'].exists():                            
            self._log_path[strategy_id]['folder'].mkdir(parents=True, exist_ok=True)

        # create strategy log file
        self._log_path[strategy_id]['log'] = self._log_path[strategy_id]['folder'] / f"{datetime.now().strftime('%Y-%m-%d')}_transaction.log"

        # recover strategy last status
        self._log_path[strategy_id]['last_trading_status'] = self._log_path[strategy_id]['folder'] / 'last_trading_status.json'
        
        # reload strategy information
        if not self._log_path[strategy_id]['last_trading_status'].exists():
            self.current_position[strategy_id] = {
                'position'  : 0.0,
            }
            self._save_data(strategy_id=strategy_id, position=self.current_position[strategy_id]['position'])

        else:
            f = open(self._log_path[strategy_id]['last_trading_status'], 'r')
            last_trading_status = json.load(f)
            f.close()
            self.current_position[strategy_id] = last_trading_status
            
    def __init__(self, rs: Client=None, ws: ThreadedWebsocketManager=None):
        if rs is not None:
            self.rest_client = rs

        if ws is not None:
            self.ws_client = ws


    def handle_account_socket_message(self, msg):

        if msg['e'] == 'ACCOUNT_UPDATE':
            if msg['a']['m'] == 'FUNDING_FEE':
                return

            self.current_position['total'] = float(msg['a']['P'][0]['pa'])

        elif msg['e'] == 'ORDER_TRADE_UPDATE':
            strategy_patten = re.search(r"^[A-Za-z]+", msg['o']['c']).group(0)
 
            # create order by hand
            if strategy_patten in ["web", "CorrectPosition"]:
                return
            self._func_dict[strategy_patten](msg, strategy_patten)    
            

    def handle_ma_order(self, msg: dict, strategy: str):
        self.write_transaction_log(strategy, msg)
        # check order status, when order type is NEW, add to current order
        if msg['o']['X'] == 'NEW':

            self.current_order[strategy]['order'].append({
                'symbol'         : msg['o']['s'],
                'side'           : msg['o']['S'],
                'order_cid'      : msg['o']['c'],
                'order_type'     : msg['o']['X'],
                'remaining_size' : float(msg['o']['q'])
                })

            self.current_order[strategy]['flag'] = False
            print(f"Event '{msg['e']}' has been detected")
        
        # check order status, when order type is PARTIALLY_FILLED, update remaining size
        elif msg['o']['X'] == 'PARTIALLY_FILLED':
            if msg['o']['S'] == 'BUY':
                self.current_position[strategy]['position'] += float(msg['o']['l'])
            
            else:
                self.current_position[strategy]['position'] -= float(msg['o']['l'])

            self.current_order[strategy]['order'][0]['remaining_size'] = (float(msg['o']['z']) - float(msg['o']['l']))
            self.current_order[strategy]['order'][0]['order_type'] = 'PARTIALLY_FILLED'
            self._save_data(strategy_id=strategy, position=self.current_position[strategy]['position'])
            
            self.current_order[strategy]['flag'] = False

        # check order status, when order type is FILLED or CANCELED, remove from current order
        elif (msg['o']['X'] == 'FILLED'):
            if (msg['o']['S'] == 'BUY'):
                self.current_position[strategy]['position'] += float(msg['o']['l'])
            
            else:
                self.current_position[strategy]['position'] -= float(msg['o']['l'])
            
            print(f"{strategy}:{self.current_position[strategy]}")
            # remove from current order list
            self.current_order[strategy]['order'] = list(filter(lambda x: x['order_cid'] != msg['o']['c'], self.current_order[strategy]['order']))
            self._save_data(strategy_id=strategy, position=self.current_position[strategy]['position'])
            
            self.current_order[strategy]['flag'] = False

        elif (msg['o']['X'] == 'CANCELED'):
            # remove from current order list
            self.current_order[strategy]['order'] = list(filter(lambda x: x['order_cid'] != msg['o']['c'], self.current_order[strategy]['order']))
            
            self.current_order[strategy]['flag'] = False


    def start_detecting_account_event(self):
        self.ws_client.start_futures_socket(callback=self.handle_account_socket_message)

    def get_current_account_info(self, symbol):
        self.current_position['total'] = float(self.rest_client.futures_position_information(symbol=symbol)[0]['positionAmt'])
        self._check_position(symbol=symbol)

        # get all order from binance
        order_response = self.rest_client.futures_get_open_orders(symbol=symbol)
        
        if order_response != []:
            # loop over all orders
            for order in order_response:
                strategy_patten = re.search(r"^[A-Za-z]+", order['clientOrderId']).group(0)
                if strategy_patten not in self.current_order.keys():
                    raise KeyError('Strategy is not not registered!')
                
                else:
                    self.current_order[strategy_patten]['order'].append(
                        {
                            'symbol'         : order['symbol'],
                            'side'           : order['side'],
                            'order_cid'      : order['clientOrderId'],
                            'order_type'     : order['status'],
                            'remaining_size' : (float(order['origQty']) - float(order['executedQty']))
                        }
                    )            

    def _check_position(self, symbol):
        """
        Confirm whether the Binance position is the same as the local position. 
        If there is a difference, 
        correct the Binance position to the local record position
        """
        
        # from local file
        total_position = 0.0
        for strategy in self.current_position:
            # total position from binance
            if strategy == 'total':
                continue
            total_position += float(self.current_position[strategy]['position'])

        # create short order
        if self.current_position['total'] > total_position:
            self.rest_client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=abs(self.current_position['total']-total_position),
                newClientOrderId=f"CorrectPosition{int(time.time())}"
            )
        
        # create long order
        elif self.current_position['total'] < total_position:
            self.rest_client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=abs(self.current_position['total']-total_position),
                newClientOrderId=f"CorrectPosition{int(time.time())}"
            )
        
            
    def write_transaction_log(self, strategy_id, transaction_record):
        file_path = self._log_path[strategy_id]['log']
        f = open(file_path, 'a')
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {transaction_record}\n")
        f.close()


    def _save_data(self, strategy_id, **kwargs):
        file_path = self._log_path[strategy_id]['last_trading_status']
        f = open(file_path, 'w')
        json.dump(kwargs, f, indent=4)
        f.close()

if __name__ == "__main__":
    import certifi, os
    
    os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = certifi.where() 
    os.environ["SSL_CERT_FILE"] = certifi.where()
    api_key = os.environ['api_key']
    api_secret = os.environ['api_secret']
    rs = Client(api_key, api_secret)
    ws = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    ws.start()
    print(AccountInfomation(rs, ws))
    a = AccountInfomation()
    print(a)
    # acc_obj = AccountInfomation(rs, ws)
    # acc_obj('Momentum', acc_obj.handle_ma_order)
    # acc_obj.get_current_account_info('BTCUSDT')
    # acc_obj.start_detecting_account_event()
    # b = AccountInfomation(api_key, api_secret)
    # test = Test(acc_obj)
    # test.start()
    # print(a)
    # print(b)
