# import logging
import threading
import time
from loguru import logger as logging
from math import ceil
import concurrent.futures
import numpy as np


from TradingView import TradingView

symbols = [
    "BTCUSDT",
    "ETHUSDT",
    "BCHUSDT",
    "XRPUSDT",
    "EOSUSDT",
    "LTCUSDT",
    "TRXUSDT",
    "ETCUSDT",
    "LINKUSDT",
    "XLMUSDT",
    "ADAUSDT",
    "XMRUSDT",
    "DASHUSDT",
    "ZECUSDT",
    "XTZUSDT",
    "BNBUSDT",
    "ATOMUSDT",
    "ONTUSDT",
    "IOTAUSDT",
    "BATUSDT",
    "VETUSDT",
    "NEOUSDT",
    "QTUMUSDT",
    "IOSTUSDT",
    "THETAUSDT",
    "ALGOUSDT",
    "ZILUSDT",
    "KNCUSDT",
    "ZRXUSDT",
    "COMPUSDT",
    "OMGUSDT",
    "DOGEUSDT",
    "SXPUSDT",
    "KAVAUSDT",
    "BANDUSDT",
    "WAVESUSDT",
    "MKRUSDT",
    "DOTUSDT",
    "YFIUSDT",
]

def _create_crawler(coins: list[str], worker: int):
    logging.info("Crawler for Worker {}: Starting".format(worker))
    TradingView(coins, worker)

if __name__ == "__main__":
    threads = list()
    workers = 4
    splits = np.array_split(symbols, workers)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        logging.info("Main: CREATING THREADS")
        for idx, split in enumerate(splits):
            logging.info("Craete crawler for worker {}".format(idx))
            executor.submit(_create_crawler, split, idx)