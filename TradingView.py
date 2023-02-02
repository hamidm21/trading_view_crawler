import websocket
import _thread
import time
import rel
import json
import random
import string
import re
import datetime
import pytz


class TradingView:
    def __init__(self, coin):
        self.coin = coin
        self._closed_candles = []
        self.headers = json.dumps({'Origin': 'https://data.tradingview.com'})
        self.ws = websocket.WebSocketApp("wss://data.tradingview.com/socket.io/websocket",
                                         on_open=self._on_open,
                                         on_message=self._on_message,
                                         on_error=self._on_error,
                                         on_close=self._on_close,
                                         header=self.headers)
        # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
        self.ws.run_forever(dispatcher=rel, reconnect=5)
        self.do(symbol="binance:{}".format(coin), since=1)
        rel.signal(2, rel.abort)  # Keyboard Interrupt
        rel.dispatch()

    @property
    def closed_candles(self):
        return self._closed_candles
    
    @closed_candles.setter
    def closed_candles(self, candle):
        self._closed_candles.append(candle)
        self._closed_candles = self._closed_candles[-2:]
        print(self._closed_candles)
        return self._closed_candles

    # WEBSOCKET FUNCTIONS
    def _on_message(self, ws, message):
        a = ""
        a = a + message + "\n"
        initial_message = re.search(r'^(~m~92~m~)', a)
        if initial_message:
            bar_close_time = re.search(r'(?<=bar_close_time":)(\w+)', a)
            print(bar_close_time)

        str = re.search('"s":\[(.+?)\}\]', a)
        if str is not None:
            # coin = re.search(r'(?<=\bname":")(\w+)', a)
            out = str.group(1)
            x = out.split(',{\"')
            for xi in x:
                xi = re.split('\[|:|,|\]', xi)
                # ts = datetime.datetime.fromtimestamp(float(xi[4]), tz=pytz.UTC).strftime("%Y/%m/%d, %H:%M:%S")
                results = {
                    'currency': self.coin,
                    'time': xi[4],
                    'open': xi[5],
                    'high': xi[6],
                    'low': xi[7],
                    'close': xi[8],
                    'volume': xi[9]
                }
            print(
                "\n ++++++++ message ++++++++ \n {} \n ++++++++ message ++++++++ \n".format(results))

    def _on_error(self, ws, error):
        print("Error--------------> {}".format(error))

    def _on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def _on_open(self, ws):
        print("Opened connection\n")

    def do(self, symbol, since: int):
        print('just doing things')
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
