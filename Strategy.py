from binance import ThreadedWebsocketManager
from binance.client import Client
from binance.enums import *
import time
from typing import List, Any
from datetime import datetime
from AccountManager import AccountInfomation
from DataManager import CryptoData
from Base import StrategyBase

# binance restful api help page https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md

class MomentumSignal(StrategyBase):
    _current_signal = 0

    # input 10 close price for moving average
    def __init__(self, rs: Client, 
                       ws: ThreadedWebsocketManager, 
                       acc_obj: AccountInfomation, 
                       data_obj: CryptoData,
                       symbol: str, 
                       malen: int, 
                       size: float, 
                       strategy_id: str) -> None:
        self.rest_client = rs
        self.ws_client = ws
        self.account = acc_obj
        self.crypto_data = data_obj
        self.malen = malen
        self.symbol = symbol
        self.default_size = size
        self.strategy_id = strategy_id
        StrategyBase.__init__(self)
        

    def start(self):
        # before starting detect, cancel all open orders
        self.rest_client.futures_cancel_all_open_orders(symbol=self.symbol)
    
    def close(self):
        print("Cancel all open orders!")
        self.rest_client.futures_cancel_all_open_orders(symbol=self.symbol)
        
        print(f"Save position to {self.strategy_id}...")
        self._save_data(position=self.account.current_position[self.strategy_id]['position'])

    def detect(self):
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -> {self.strategy_id} start detect")
        # if self.strategy_id == 'Momentum':
            # print("in",self.crypto_data.ma_data)
            # print(self.crypto_data.real_time_data)
        # print(self.crypto_data.ma_data['kline'])
        # print(f"NOW position {self.account.current_position[self.strategy_id]}")
        if (self.account.current_position == None) or (self.account.current_order[self.strategy_id]['order'] == None):
            raise ValueError("Position or order has not been loaded")
        
        ma = sum(self.crypto_data.ma_data['kline']) / len(self.crypto_data.ma_data['kline'])
        if (self.crypto_data.ma_data['kline'][-1] > ma):
            self._current_signal = 1
        
        elif (self.crypto_data.ma_data['kline'][-1] < ma):
            self._current_signal = -1
        
        # check the order has been reordered or order is empty
        if (self._check_order()):
            print("Stop by check order")
            return

        # the same direction order
        if (self._check_position()):
            print("Stop by check position")
            return
    
        # To avoid websocket delay
        if (self.account.current_order[self.strategy_id]['flag']):
            print("Websocket delay.")
            self.write_transaction_log("Websocket delay.")
            return
        
        order_size = self.default_size if (float(self.account.current_position[self.strategy_id]['position']) == 0)\
                                       else (abs(self.account.current_position[self.strategy_id]['position'] - self.default_size*self._current_signal))
        
        self._create_order(order_size)
        self._previous_signal = self._current_signal


    def _check_position(self):
        if abs(self.account.current_position[self.strategy_id]['position']) > self.default_size:
            self.write_transaction_log("Position mismatch !!")
            raise ValueError("Position mismatch !!")

        if self.account.current_position[self.strategy_id]['position'] == (self._current_signal * self.default_size):
            # print(f"The same direction position exist. \
            #     position:{self.account.current_position[self.strategy_id]['position']} \
            #     signal:{self._current_signal*self.default_size}")
            return True

        return False

    def _check_order(self):
        # open order is exists
        if (self.account.current_order[self.strategy_id]['order'] != []):
            if (self.account.current_order[self.strategy_id]['order'][0]['order_type'] == 'NEW') or (
                self.account.current_order[self.strategy_id]['order'][0]['order_type'] == 'PARTIALLY_FILLED'):
                print("Meet entry criteria, but established order")
                self._reorder()
                return True

            else:
                raise TypeError('unpredict condition for order type!')
        
        # open order is empty
        elif self.account.current_order[self.strategy_id]['order'] == []:
            return False

    def _create_cid(self) -> str:
        timestamp = str(int(time.time()))
        client_id = self.strategy_id + timestamp
        return client_id

    def _create_order(self, size):
        # To avoid websocket delay
        self.account.current_order[self.strategy_id]['flag'] = True
        
        if self._current_signal == 1:
            # crete order, to avoid bug, when caculate price, use (round({caculate_result}, 3))
            self.rest_client.futures_create_order(
                symbol=self.symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=size,
                price=str(self.crypto_data.real_time_data['best_bid']),
                newClientOrderId=self._create_cid()
            )

            # write log to localhost
            self.write_transaction_log("\n")
            order_record = f"raise crossup signal and open long position, quantity : {size}"
            self.write_transaction_log(order_record)

        elif self._current_signal == -1:
            
            # create order
            self.rest_client.futures_create_order(
                symbol=self.symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=size,
                price=str(self.crypto_data.real_time_data['best_ask']),
                newClientOrderId=self._create_cid()
            )

            # write log to localhost
            self.write_transaction_log("\n")
            order_record = f"raise crossdown signal and open short position, quantity : {size}"
            self.write_transaction_log(order_record)

    
    def _reorder(self):
        remaining_size = self.account.current_order[self.strategy_id]['order'][0]['remaining_size']
        side = self.account.current_order[self.strategy_id]['order'][0]['side']
    
        # when the order is filled, it's no need to place new order.
        try:
            self.rest_client.futures_cancel_order(symbol=self.symbol, origClientOrderId=self.account.current_order[self.strategy_id]['order'][0]['order_cid'])

        except:
            return

        # avoid order event delay
        time.sleep(0.2)

        # crete order, to avoid bug, when caculate price, use (round({caculate_result}, 3))
        # self._create_order(remaining_size)
        
        # To avoid websocket delay
        self.account.current_order[self.strategy_id]['flag'] = True
        
        if side == 'BUY':
            
            # crete order, to avoid bug, when caculate price, use (round({caculate_result}, 3))
            # reorder for remaining size
            self.rest_client.futures_create_order(
                symbol=self.symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=(remaining_size),
                price=str(self.crypto_data.real_time_data['best_bid']),
                newClientOrderId=self._create_cid()
            )

            # write log to localhost
            order_record = f"reorder long position, quantity : {remaining_size}."
            self.write_transaction_log(order_record)

        elif side == 'SELL':
            
            # reorder for remaining size
            self.rest_client.futures_create_order(
                symbol=self.symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=(remaining_size),
                price=str(self.crypto_data.real_time_data['best_ask']),
                newClientOrderId=self._create_cid()
            )

            # write log to localhost
            order_record = f"reorder short position, quantity : {remaining_size}."
            self.write_transaction_log(order_record)
    