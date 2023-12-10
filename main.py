import os
import sys
import time
import dotenv

dotenv.load_dotenv()

# DO NOT TRADE BITCOIN WITH THIS BOT IT IS NOT DESIGNED TO HANDLE BITCOIN
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

import ccxt  # noqa: E402
from ccxt.base.decimal_to_precision import ROUND_UP  # noqa: E402

msec = 1000
minute = 60 * msec
hold = 30

exchange = ccxt.cryptocom()

phemex = ccxt.phemex({
    "enableRateLimit": True,
    "apiKey": os.getenv("PHEMEXAPI_ID"),
    "secret": os.getenv("PHEMEXAPI_SECRET")
})

amountConversion = {
    "BTC/USD:USD": 0.001,
    "ETH/USD:USD": 0.005,
    "TRX/USDT:USDT": 1,
    "XRP/USDT:USDT": 1
}

symbol = 'ETH/USD:USD'
leverage = 5
# amount = .005 * leverage

limit = 75
timeframe = "5m"
interval = exchange.parse_timeframe(timeframe) * 1000

fastSMALen = 10
slowSMALen = 75
rsiLen = 14

pastData = exchange.fetch_ohlcv('ETH/USD', timeframe,
                                since=exchange.round_timeframe(timeframe, exchange.milliseconds(), ROUND_UP) - (
                                        limit * interval), limit=limit)
closeData = [pastData[x][4] for x, a in enumerate(pastData)]


def buy_coin(amount_to_buy, _leverage):
    amountToPay = amount_to_buy / amountConversion[symbol]

    if symbol[-1] == "T":
        phemex.set_position_mode(False, symbol)

    leverageResponse = phemex.set_leverage(_leverage, symbol)

    order = phemex.create_market_buy_order(symbol, amountToPay)

    print(order)

def sell_coin(amount_to_sell, _leverage):
    amountToGet = amount_to_sell / amountConversion[symbol]

    if amountToGet < 1:
        print("Not Enough Funds")
        return 1

    if symbol[-1] == "T":
        phemex.set_position_mode(False, symbol)

    phemex.set_leverage(_leverage, symbol)

    order = phemex.create_market_sell_order(symbol, amountToGet)

    print(order)

def calc_sma(price_data: list, calc_len: int) -> float:
    if len(price_data) < calc_len:
        return 0

    sum_price = 0

    for x in price_data[-calc_len:]:
        sum_price += x

    return sum_price / calc_len


def calc_rma(price_data: list, calc_len: int) -> float:
    relPriceData = price_data[-calc_len - 1:][0:calc_len]
    RMAI = sum(relPriceData) / calc_len
    calculationPrice = price_data[-1]

    RMA = (calculationPrice + (RMAI * (calc_len - 1))) / calc_len

    return RMA


def calc_rsi(price_data: list, calc_len: int) -> float:
    # priceDifferences = []

    posPriceDiff = []
    negPriceDiff = []
    averageGain = 0
    averageLoss = 0

    a = 1 / calc_len

    for i, a in enumerate(price_data):
        if i == 0:
            continue
        priceDifference = a - price_data[i - 1]
        # priceDifferences.append(priceDifference)
        if priceDifference > 0:
            negPriceDiff.append(0)
            posPriceDiff.append(priceDifference)
        else:
            posPriceDiff.append(0)
            negPriceDiff.append(abs(priceDifference))

    # priceDifferences = priceDifferences[::-1]

    rmaPos = calc_rma(posPriceDiff, calc_len)
    rmaNeg = calc_rma(negPriceDiff, calc_len)

    if max(negPriceDiff) == 0:
        return 100

    relativeStrength = rmaPos / rmaNeg
    return (100 - (100 / (1 + relativeStrength))) - 0


openPosition = False
buyPrice = 0

print("Starting Server")

amountBought = 0
lastTime = pastData[-1][0]

while True:
    try:
        print(exchange.milliseconds(), 'Fetching candles')
        since = exchange.round_timeframe(timeframe, exchange.milliseconds(), ROUND_UP) - (limit * interval)
        ohlcv = exchange.fetch_ohlcv('ETH/USD', timeframe, since=since, limit=limit)

        lastCandle = ohlcv[-1]
        last = lastCandle[0]
        if lastTime == lastCandle[0]:
            print('Last candle', lastCandle, exchange.iso8601(last))
            time.sleep(10)
            continue

        closeData.pop(0)
        closeData.append(lastCandle[4])
        lastFastSMA = calc_sma(closeData, fastSMALen)
        lastSlowSMA = calc_sma(closeData, slowSMALen)
        lastRSI = calc_rsi(closeData, rsiLen)

        buyCondition = lastFastSMA > lastSlowSMA
        buyCondition2 = lastRSI <= 30
        buyConditionFilter = lastRSI <= 58

        closeCondition1 = (lastFastSMA - lastSlowSMA) / lastSlowSMA <= -.01
        closeCondition2 = lastRSI > 73

        # print('Last candle', lastCandle, exchange.iso8601(last))
        # print('Last Fast SMA', lastFastSMA)
        # print('Last Slow SMA', lastSlowSMA)
        # print('Last RSI', lastRSI)

        if (buyCondition or buyCondition2) and buyConditionFilter and not openPosition:
            amount = (phemex.fetch_balance({"type": "swap", "code": "USD"})["USD"]["free"]/phemex.fetch_ticker(symbol)["bid"]) * leverage
            amountBought = amount
            buy_coin(amount, leverage)

            print("Buy!")
            print('Last candle', lastCandle, exchange.iso8601(last))
            print('Last Fast SMA', lastFastSMA)
            print('Last Slow SMA', lastSlowSMA)
            print('Last RSI', lastRSI)
            buyPrice = lastCandle[4]
            openPosition = True

        elif (closeCondition1 or closeCondition2) and openPosition and lastCandle[4] > buyPrice:
            sell_coin(amountBought, leverage)
            amountBought = 0

            print("Sell!")
            print('Last candle', lastCandle, exchange.iso8601(last))
            print('Last Fast SMA', lastFastSMA)
            print('Last Slow SMA', lastSlowSMA)
            print('Last RSI', lastRSI)
            print("Sale Profit: " + str((lastCandle[4] / buyPrice - 1) * 100) + "%")
            buyPrice = 0
            openPosition = False

        # Calculate time to next candle and sleep for that many seconds
        sleeptime = (exchange.round_timeframe(timeframe, last, ROUND_UP) - exchange.milliseconds()) / 1000

        if sleeptime >= 0:
            # print('sleeping for: ', sleeptime, 's', sleeptime // 60, 'min')
            time.sleep(sleeptime)
        else:
            sleeptime = (exchange.round_timeframe(timeframe, last, ROUND_UP) - exchange.milliseconds()) / 1000 * -1
            # print(sleeptime)
            # print('sleeping for: ', sleeptime, 's', sleeptime // 60, 'min')
            time.sleep(10)

    except (ccxt.ExchangeError, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout,
            ccxt.NetworkError) as error:
        print('Got an error', type(error).__name__, error.args, ', retrying in', hold, 'seconds...')
        time.sleep(hold)
