import ccxt  # noqa: E402
from ccxt.base.decimal_to_precision import ROUND_UP  # noqa: E402
import os
import sys
import time
import numpy as np

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

class Wrapper:
    def __init__(self, apiKey: str = None, secret: str = None, symbol: str = "ETH/USD:USD"):
        self.phemex = ccxt.phemex({
            "enableRateLimit": True,
            "apiKey": apiKey,
            "secret": secret
        })
        self.amountConversion = {
            "BTC/USD:USD": 0.001,
            "ETH/USD:USD": 0.005,
            "TRX/USDT:USDT": 1,
            "XRP/USDT:USDT": 1
            }

        self.symbol = symbol

    def buy_coin(self, _leverage: int, amount_to_buy_percent: int = 100) -> str:
        moneyInAccount = self.phemex.fetch_balance({"type": "swap", "code": f"USD{'T' if self.symbol[-1] == 'T' else ''}"})[f"USD{'T' if self.symbol[-1] == 'T' else ''}"]["total"]
        moneyToSpend = moneyInAccount * amount_to_buy_percent / 100
        amountToBuy = (moneyToSpend / self.phemex.fetch_ticker(self.symbol)["bid"]) * _leverage

        amountToPay = amountToBuy / self.amountConversion[self.symbol]

        if amountToPay < 1:
            return "Not Enough Funds"

        if self.symbol[-1] == "T":
            self.phemex.set_position_mode(False, self.symbol)

        leverageResponse = self.phemex.set_leverage(_leverage, self.symbol)

        order = self.phemex.create_market_buy_order(self.symbol, amountToPay)

        return order

    def sell_coin(self, _leverage: int,  amount_to_sell_percent: int = 100) -> str:
        amountToGet = int(self.phemex.fetch_positions([self.symbol])[0]["info"]["size"]) * amount_to_sell_percent / 100

        if amountToGet < 1:
            return "Not Enough Funds"

        if self.symbol[-1] == "T":
            self.phemex.set_position_mode(False, self.symbol)

        self.phemex.set_leverage(_leverage, self.symbol)

        order = self.phemex.create_market_sell_order(self.symbol, amountToGet)

        return order

    def calc_sma(self, price_data: list, calc_len: int) -> float:
        if len(price_data) < calc_len:
            return 0

        sum_price = 0

        for x in price_data[-calc_len:]:
            sum_price += x

        return sum_price / calc_len

    def calc_rma(self, price_data: list, calc_len: int) -> float:
        relPriceData = price_data[-calc_len - 1:][0:calc_len]
        RMAI = sum(relPriceData) / calc_len
        calculationPrice = price_data[-1]

        RMA = (calculationPrice + (RMAI * (calc_len - 1))) / calc_len

        return RMA

    def calc_rsi(self, price_data: list, calc_len: int) -> float:
        posPriceDiff = []
        negPriceDiff = []

        for i, a in enumerate(price_data):
            if i == 0:
                continue
            priceDifference = a - price_data[i - 1]
            if priceDifference > 0:
                negPriceDiff.append(0)
                posPriceDiff.append(priceDifference)
            else:
                posPriceDiff.append(0)
                negPriceDiff.append(abs(priceDifference))


        rmaPos = self.calc_rma(posPriceDiff, calc_len)
        rmaNeg = self.calc_rma(negPriceDiff, calc_len)

        if max(negPriceDiff) == 0:
            return 100

        relativeStrength = rmaPos / rmaNeg
        return (100 - (100 / (1 + relativeStrength))) - 0

    def calc_ema(self, price_data: list, calc_len: int) -> list:
        ema = np.zeros(len(price_data))
        sma = np.mean(price_data[:calc_len])
        ema[calc_len - 1] = sma
        weighting_factor = 2 / (calc_len + 1)

        for i in range(calc_len, len(price_data)):
            ema[i] = (price_data[i] * weighting_factor) + (ema[i - 1] * (1 - weighting_factor))
        return ema.tolist()

    def calc_macd(self, price_data, slow_len: int = 26, fast_len: int = 12, signal_len: int = 9):
        fast_ema = np.array(self.calc_ema(price_data, fast_len))
        slow_ema = np.array(self.calc_ema(price_data, slow_len))

        macd_line = fast_ema - slow_ema
        signal_len = self.calc_ema(macd_line.tolist(), signal_len)

        return macd_line.tolist()[-1], signal_len[-1]
    
    def bot_loop(self, strategy, timeframe: int = "5m"):
        limit = 300
        hold = 30
        timeframe = timeframe

        exchange = ccxt.cryptocom()
        interval = exchange.parse_timeframe(timeframe) * 1000

        pastData = exchange.fetch_ohlcv(self.symbol.split(":")[0], timeframe,
                                        since=exchange.round_timeframe(timeframe, exchange.milliseconds(), ROUND_UP) - (
                                                limit * interval), limit=limit)
        closeData = [pastData[x][4] for x, a in enumerate(pastData)]

        lastTime = pastData[-1][0]

        buyPrice = -1

        while True:
            try:
                print(exchange.milliseconds(), 'Fetching candles')
                since = exchange.round_timeframe(timeframe, exchange.milliseconds(), ROUND_UP) - (limit * interval)
                ohlcv = exchange.fetch_ohlcv('ETH/USD', timeframe, since=since, limit=limit)

                lastCandle = ohlcv[-1]
                last = lastCandle[0]
                if lastTime == lastCandle[0]:
                    print('Last candle', lastCandle, exchange.iso8601(last))
                    time.sleep(hold)
                    continue

                closeData.pop(0)
                closeData.append(lastCandle[4])

                buyPrice = strategy(closeData, buyPrice, lastCandle, exchange)
                
                # Calculate time to next candle and sleep for that many seconds
                sleeptime = (exchange.round_timeframe(timeframe, last, ROUND_UP) - exchange.milliseconds()) / 1000

                if sleeptime >= 0:
                    time.sleep(sleeptime)
                else:
                    sleeptime = (exchange.round_timeframe(timeframe, last, ROUND_UP) - exchange.milliseconds()) / 1000 * -1
                    time.sleep(10)

            except (ccxt.ExchangeError, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout,
                ccxt.NetworkError) as error:
                print('Got an error', type(error).__name__, error.args, ', retrying in', hold, 'seconds...')
                time.sleep(hold)
