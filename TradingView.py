import threading
import datetime
import json
import random
import re
import string
import sys
import time
import csv
import os

# import logging
from loguru import logger
import pytz
import websocket


class TradingView:
    def __init__(self, symbols, worker_id):
        self.time = None
        self.symbols = symbols
        self.worker_id = worker_id
        self.logger = logger
        self._closed_candles = [{"symbol": symbol, "chart_session": None, "time": None,
                                 "qoute_session": None, "data": [], "tickers":[]} for symbol in symbols]
        self.headers = json.dumps({'Origin': 'https://data.tradingview.com'})
        self.ws = websocket.WebSocketApp("wss://data.tradingview.com/socket.io/websocket",
                                         on_open=self._on_open,
                                         on_message=self._on_message,
                                         on_error=self._on_error,
                                         on_close=self._on_close,
                                         header=self.headers)
        self.logger.debug("Initializing Crawler {}".format(worker_id))
        self.ws.run_forever()

    # WEBSOCKET FUNCTIONS
    def _on_message(self, ws, message):
        self._check_stay_alive(message)
        a = ""
        a = a+message+"\n"
        str = re.search(r'"p":\["(\w+)",\{(.+?)\}\]', a)
        if str is not None:
            symbol = None
            unique_id = re.search(r'(?<="p":\[")(\w+)', str[0])
            if unique_id is not None:
                for idx, candle in enumerate(self._closed_candles):
                    if candle["chart_session"] == unique_id[0]:
                        current_candle = self._closed_candles[idx]
                        symbol = current_candle["symbol"]
                        break
                if symbol is not None:
                    str = re.search(r'"s":\[(.+?)\}\]', str[0])
                    if str is not None:
                        out = str.group(1)
                        x = out.split(',{\"')
                        for xi in x:
                            xi = re.split('\[|:|,|\]', xi)
                            ts = datetime.datetime.fromtimestamp(
                                float(xi[4]), tz=pytz.UTC).strftime("%Y/%m/%d, %H:%M:%S")
                            results = {
                                'currency': symbol,
                                'time': xi[4],
                                'open': xi[5],
                                'high': xi[6],
                                'low': xi[7],
                                'close': xi[8],
                                'volume': xi[9],
                            }
                            if not current_candle["time"]:
                                current_candle["time"] = ts
                            elif current_candle["time"] != ts:
                                if current_candle["tickers"]:
                                    current_candle["data"].append(
                                        current_candle["tickers"][-1])
                                    current_candle["tickers"] = []
                                    current_candle["data"] = current_candle["data"][-100:]
                                    current_candle["time"] = ts
                                    self._write_to_csv(
                                        "./data/{}/1m.csv".format(current_candle["symbol"]), [item[1] for item in current_candle["data"][-1].items()])
                                    self.logger.debug(
                                        current_candle["data"][-1])
                            elif current_candle["time"] == ts:
                                current_candle["tickers"].append(
                                    results)

    def _get_last_tickers(self):
        return [candle["data"][-1] if candle["data"] else None for candle in self._closed_candles]

    @staticmethod
    def __create_directory(path: str):
        dirname = os.path.dirname(path)
        tokens = dirname.split('/')
        dirs = ['/'.join(tokens[:index + 1])
                for index in range(1, len(tokens))]
        for parent_dir in dirs:
            if not os.path.exists(parent_dir):
                os.mkdir(parent_dir)

    def _on_error(self, ws, error):
        print("Error--------------> {}".format(error))

    def _on_close(self, ws, close_status_code, close_msg):
        print(close_msg, close_status_code)
        print("### closed")

    def _write_to_csv(self, addr, content):
        self.__create_directory(addr)
        exists = os.path.isfile(addr)
        with open(addr, 'a', newline='') as file:
            writer = csv.writer(file, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
            print(exists)
            if not exists:
                writer.writerow([
                    'currency',
                    'time',
                    'open',
                    'high',
                    'low',
                    'close',
                    'volume'])
            writer.writerow(content)

    def _on_open(self, ws):
        for coin in self.symbols[:39]:
            self.logger.info("start crawling {}".format(coin))
            self._send(coin, 1)

    def _check_stay_alive(self, message):
        pattern = re.compile("~m~\d+~m~~h~\d+$")
        if pattern.match(message):
            self.ws.send(message)

    def _send(self, symbol: str, since: int):
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

        for idx, symb in enumerate(self._closed_candles):
            if symb["symbol"] == symbol:
                self._closed_candles[idx]["chart_session"] = chart_session
                self._closed_candles[idx]["qoute_session"] = session
                break

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
