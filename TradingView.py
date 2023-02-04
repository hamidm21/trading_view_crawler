import threading
import datetime
import json
import random
import re
import string
import sys
import time

# import logging
from loguru import logger 
import pytz
import websocket

# from .logger import logger
# from test import symbols

# format = "%(asctime)s: %(message)s\n_______"
# logging.basicConfig(format=format, level=logging.INFO,
#                     datefmt="%H:%M:%S")


class TradingView:
    def __init__(self, symbols, worker_id):
        self.symbols = symbols
        self.worker_id = worker_id
        self.logger = logger
        self._closed_candles = []
        self._subscribed_coins = []
        self.headers = json.dumps({'Origin': 'https://data.tradingview.com'})
        self.ws = websocket.WebSocketApp("wss://data.tradingview.com/socket.io/websocket",
                                         on_open=self._on_open,
                                         on_message=self._on_message,
                                         on_error=self._on_error,
                                         on_close=self._on_close,
                                         header=self.headers)
        self.logger.debug("Initializing Crawler {}".format(worker_id))
        self.ws.run_forever()
    @property
    def closed_candles(self):
        return self._closed_candles

    @closed_candles.setter
    def closed_candles(self, candle):
        self._closed_candles.append(candle)
        self._closed_candles = self._closed_candles[-2:]
        print("closed candle {}".format(self._closed_candles))
        return self._closed_candles

    # WEBSOCKET FUNCTIONS
    def _on_message(self, ws, message):
        pattern = re.compile("~m~\d+~m~~h~\d+$")
        if pattern.match(message):
            ws.send(message)
            self.logger.info("stay alive message -> {}".format(message))
        # a=a+message+"\n"

        # self.logger.info("new message")
        a = ""
        a = a + message + "\n"
        unique_id_of_the_coin = re.search(r'(?<="p":\[")(\w+)', a)
        short_name = re.search(r'(?<=n":")(\w+)', a)
        if unique_id_of_the_coin and short_name:
            if short_name[0] in self.symbols:
                new_coin = {
                    "id": unique_id_of_the_coin[0],
                    "name": short_name[0]
                }
                if new_coin not in self._subscribed_coins:
                    old = []
                    [old.append(idx) if coin["name"] == new_coin["name"] else None for idx ,coin in enumerate(self._subscribed_coins)]
                    if old:
                        self._subscribed_coins[old[0]] = new_coin
                    else:
                        self._subscribed_coins.append(new_coin)
                    self.logger.debug("{}, len:{}, worker-id: {}".format(new_coin ,len(self._subscribed_coins), self.worker_id))
        
        # self._subscribed_coins.append(new_coin)
        # if
        # str = re.search('"s":\[(.+?)\}\]', a)
        # if str is not None:
        #     # coin = re.search(r'(?<=\bname":")(\w+)', a)
        #     out = str.group(1)
        #     x = out.split(',{\"')
        #     for xi in x:
        #         xi = re.split('\[|:|,|\]', xi)
        #         # ts = datetime.datetime.fromtimestamp(float(xi[4]), tz=pytz.UTC).strftime("%Y/%m/%d, %H:%M:%S")
        #         results = {
        #             'currency': self.coin,
        #             'time': xi[4],
        #             'open': xi[5],
        #             'high': xi[6],
        #             'low': xi[7],
        #             'close': xi[8],
        #             'volume': xi[9]
        #         }
        #     logging.info()

    def _on_error(self, ws, error):
        print("Error--------------> {}".format(error))

    def _on_close(self, ws, close_status_code, close_msg):
        print(close_msg, close_status_code)
        print("### closed")

    def _on_open(self, ws):
        print("Opened connection\n")
        # while True:
        for coin in self.symbols[:39]:
            self._send(coin, 1)
            # time.sleep(10)
            # thread.Thread()

    def _send(self, symbol, since: int):
        session = self.generateSession()
        chart_session = self.generateChartSession()
        self.sendMessage(self.ws, "set_auth_token", [
                         "unauthorized_user_token"])
        self.sendMessage(self.ws, "chart_create_session", [chart_session, ""])
        self.sendMessage(self.ws, "quote_create_session", [session])
        self.sendMessage(self.ws, "quote_set_fields",
                         [session, "ch", "chp", "current_session", "description", "local_description", "language",
                          "exchange",
                          "fractional", "is_tradable", "lp", "lp_time", "minmov", "minmove2", "original_name",
                          "pricescale",
                          "pro_name", "short_name", "type", "update_mode", "volume", "currency_code", "rchp", "rtc"])
        self.sendMessage(self.ws, "quote_add_symbols", [
                         session, symbol, {"flags": ['force_permission']}])
        self.sendMessage(self.ws, "quote_fast_symbols", [session, symbol])

        message = json.dumps(
            {"symbol": symbol, "adjustment": "splits", "session": "extended"})
        self.sendMessage(self.ws, "resolve_symbol",
                         [chart_session, "symbol_1",
                          "=" + message])
        self.sendMessage(self.ws, "create_series", [
                         chart_session, "s1", "s1", "symbol_1", "1", since])

    def generateSession(self):
        string_length = 12
        letters = string.ascii_lowercase
        random_string = ''.join(random.choice(letters)
                                for i in range(string_length))
        return "qs_" + random_string

    def generateChartSession(self):
        string_length = 12
        letters = string.ascii_lowercase
        random_string = ''.join(random.choice(letters)
                                for i in range(string_length))
        return "cs_" + random_string

    def prependHeader(self, st):
        return "~m~" + str(len(st)) + "~m~" + st

    def constructMessage(self, func, paramList):
        return json.dumps({
            "m": func,
            "p": paramList
        }, separators=(',', ':'))

    def createMessage(self, func, paramList):
        return self.prependHeader(self.constructMessage(func, paramList))

    def sendRawMessage(self, ws, message):
        ws.send(self.prependHeader(message))

    def sendMessage(self, ws, func, args):
        ws.send(self.createMessage(func, args))
