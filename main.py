import StrategyDriver
import os
import certifi
from binance import ThreadedWebsocketManager
from binance.client import Client
import sys
import threading
import time
from ConnectionKeeper import Connection

# error log
# sys.stderr = open('error.log', 'a')

os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = certifi.where() 
os.environ["SSL_CERT_FILE"] = certifi.where()
api_key = os.environ['api_key']
api_secret = os.environ['api_secret']

while (True):
    try:
        if Connection.stop_flag:
            raise ConnectionError("Connected Fail")

        rs = Client(api_key, api_secret)
        ws = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    
    except:
        print("ConnectionError")
        time.sleep(5)
        continue

    strategy_framework = threading.Thread(target=StrategyDriver.run, name='Run', daemon=True, kwargs={'rs':rs, 'ws':ws})
    connection = threading.Thread(target=Connection.ping_server, name='Check_connection', daemon=True, kwargs={'rs':rs})

    ws.start()
    strategy_framework.start()
    connection.start()

    strategy_framework.join()
    
    # avoid infinite loop
    time.sleep(1)
    ws.stop()

    