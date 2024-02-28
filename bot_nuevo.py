import websocket, json, pprint, yagmail
import pandas as pd
import talib
from binance.client import Client
from binance.enums import *
import numpy as np



TRADE_QUANTITY = 20.0 #En moneda base
NUM_VELAS=10
bought=False
close=0
precio_compra=0.0
quantity_token=0.0 #Cantidad en primer token
token_real=0.0 #quantity_token rounded a 6 decimales
SYMBOL="BTCBUSD"
SOCKET="wss://stream.binance.com:9443/ws/btcbusd@kline_1m"
client = Client("<key>","<secret_key>", tld='com')


def order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    try:
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
        correo=yagmail.SMTP("<email>","<password>")
        correo.send(to="<client_email>",subject=side,contents=order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message): 
    global bought,close,precio_compra,quantity_token,token_real

    # Almacenar datos cada vez que llegue un mensaje
    json_message = json.loads(message)
  
    candle = json_message['k']
    is_candle_closed = candle['x']
    time = candle['t']
    close = float(candle['c'])

    # Obtener últimos 500 datos
    candelas= client.get_klines(symbol='BTCBUSD', interval= Client.KLINE_INTERVAL_1MINUTE)
    pf=pd.DataFrame(candelas)
    pf=pf.tail(NUM_VELAS)
    column = pf.iloc[:,4]

    # Calcular indicador
    upperband, middleband, lowerband = talib.BBANDS(column, timeperiod=10, nbdevup=2, nbdevdn=2)
    lower=float(lowerband[499])
    uper=float(upperband[499])

    # Condicion para vender
    if uper<=close:
        if close>precio_compra*1.003:
            if bought==True:
                order_succeeded = order(SIDE_SELL,token_real,SYMBOL)
                if order_succeeded:
                    bought = False
    # Condicion para comprar
    if lower>=close:
        if bought==False:
            precio_compra=close
            quantity_token=TRADE_QUANTITY/close
            token_real=round(quantity_token,6)
            order_succeeded = order(SIDE_BUY,token_real,SYMBOL)
            if order_succeeded:
                bought = True
                    
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)

ws.run_forever()
