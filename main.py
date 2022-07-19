from Strategy import MomentumSignal
from binance import ThreadedWebsocketManager
from binance.client import Client
import certifi, os, sys, time
from DataManager import CryptoData
from AccountManager import AccountInfomation

os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = certifi.where() 
os.environ["SSL_CERT_FILE"] = certifi.where()
api_key = os.environ['api_key']
api_secret = os.environ['api_secret']

# error log
# sys.stderr = open('error.log', 'a')

def ping_server(self):
    pass

def run():

    rs = Client(api_key, api_secret)
    ws = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    ws.start()
    
    # strategy 1
    symbol = 'BTCUSDT'
    malen = 5
    interval = 5
    strategy_id = 'Momentum'
    size = 0.001
    
    # initialize data object
    crypto_data = CryptoData(rs, ws, symbol)
    crypto_data.handle_strategy_data(malen=malen, interval=interval)

    # strategy 2
    symbol_2 = 'BTCUSDT'
    malen_2 = 5
    interval_2 = 15
    strategy_id_2 = 'Momentumii'
    size_2 = 0.001

    # initialize data object
    crypto_data_2 = CryptoData(rs, ws, symbol_2)
    crypto_data_2.handle_strategy_data(malen=malen_2, interval=interval_2)

    # update account infomation in real time
    account_info = AccountInfomation(rs, ws)

    # Must register strategy !!!
    account_info(strategy_id, account_info.handle_ma_order)
    account_info(strategy_id_2, account_info.handle_ma_order)
    account_info.get_current_account_info(symbol)
    account_info.start_detecting_account_event()

    time.sleep(2)

    # initialize strategy object
    momentum = MomentumSignal(rs, ws, account_info, crypto_data, symbol, malen, size, strategy_id)
    momentum_2 = MomentumSignal(rs, ws, account_info, crypto_data_2, symbol_2, malen_2, size_2, strategy_id_2)
    # momentum.start()

    
    while(True):
        try:
            if (all(ele > 0 for ele in crypto_data.real_time_data.values())) and (
                len(crypto_data.ma_data['kline']) == malen
                ):
                momentum.detect()

            if (all(ele > 0 for ele in crypto_data_2.real_time_data.values())) and (
                len(crypto_data_2.ma_data['kline']) == malen_2
                ):
                momentum_2.detect()
            
            else:
                print("Data loading...")

            time.sleep(3)

        except KeyboardInterrupt:
            ws.stop()
            momentum.close()
            momentum_2.close()
            os._exit(0)


if __name__ == "__main__":
    run()