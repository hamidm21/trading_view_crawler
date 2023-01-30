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

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print("Error--------------> {}".format(error))

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection\n")

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://data.tradingview.com/socket.io/websocket",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()

class TV_Crawler:
    def __init__(self, ws, symbol, since):
        self.headers = json.dumps({'Origin': 'https://data.tradingview.com'})
        websocket.enableTrace(True)
        self.ws = ws

        session = self.generateSession()
        chart_session = self.generateChartSession()
        self.sendMessage(self.ws, "set_auth_token", ["unauthorized_user_token"])
        self.sendMessage(self.ws, "chart_create_session", [chart_session, ""])
        self.sendMessage(self.ws, "quote_create_session", [session])
        self.sendMessage(self.ws, "quote_set_fields",
                         [session, "ch", "chp", "current_session", "description", "local_description", "language",
                          "exchange",
                          "fractional", "is_tradable", "lp", "lp_time", "minmov", "minmove2", "original_name",
                          "pricescale",
                          "pro_name", "short_name", "type", "update_mode", "volume", "currency_code", "rchp", "rtc"])
        self.sendMessage(self.ws, "quote_add_symbols", [session, symbol, {"flags": ['force_permission']}])
        self.sendMessage(self.ws, "quote_fast_symbols", [session, symbol])

        message = json.dumps({"symbol": symbol, "adjustment": "splits", "session": "extended"})
        self.sendMessage(self.ws, "resolve_symbol",
                         [chart_session, "symbol_1",
                          "=" + message])
        self.sendMessage(self.ws, "create_series", [chart_session, "s1", "s1", "symbol_1", "1", since])
                
    def do(self):
        while True:
            try:
                result = self.ws.recv()
                if result:
                    return result
            except Exception as e:
                print(e)
                break

    def generateSession(self):
        string_length = 12
        letters = string.ascii_lowercase
        random_string = ''.join(random.choice(letters) for i in range(string_length))
        return "qs_" + random_string

    def generateChartSession(self):
        string_length = 12
        letters = string.ascii_lowercase
        random_string = ''.join(random.choice(letters) for i in range(string_length))
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

    def translate(self, content, symbol):
        a = ""
        a = a + content + "\n"
        str = re.search('"s":\[(.+?)\}\]', a)
        if str is not None:
            out = str.group(1)
            x = out.split(',{\"')
            for xi in x:
                xi = re.split('\[|:|,|\]', xi)
                # ts = datetime.datetime.fromtimestamp(float(xi[4]), tz=pytz.UTC).strftime("%Y/%m/%d, %H:%M:%S")
                result = {
                    'currency': symbol,
                    'time': xi[4],
                    'open': xi[5],
                    'high': xi[6],
                    'low': xi[7],
                    'close': xi[8],
                    'volume': xi[9]
                }
            return result


# if __name__ == "__main__":
#     crawler = TV_Crawler('binance:BTCUSDT', 2)
#     crawler.do()


    # ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    # rel.signal(2, rel.abort)  # Keyboard Interrupt
    # rel.dispatch()
