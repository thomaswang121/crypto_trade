# crypto_trade

## Introduce
The purpose of this system is to find out the entry and exit signals through data analysis, and automatically create orders, it must monitor the stability of the entire system and the error handling when errors occur, so as to avoid losses that are not caused by the strategy.<br><br>
This system consists of three component:
 * Data - get real time data from binance server (kline, bookticker)
 * Account - get the account event and order event
 * Strategy - detect long or short signal and create order

## System architecture
![crypto_architechture](https://user-images.githubusercontent.com/86098705/185808426-25402e80-20a6-46ca-8a32-fd4bd97cc4fa.PNG)
## Data
Binance provides two ways to get data
1. From RESTApi
2. From Websocket
<br>
I use RESTApi to recover historical kline data, and establish a websocket connection to update.

## Account
Establish websocket connection to receiving account events or order events triggered by Binance.

## Strategy
Strategy object is mainly responsible for detecting signal, create order, reorder, each strategy has different entry criteria, and different strategies have different approach to checking old order status, and in order to ensuer that the position is correct, the position status must be monitored in real-time.

## How to run this program
First step : Setup the environment<br>
run `pip install -r requirements.txt`

Second step : run this program<br>
`python main.py`
