import dotenv
import os
import sys
from Wrapper import Wrapper

dotenv.load_dotenv()

# DO NOT TRADE BITCOIN WITH THIS BOT IT IS NOT DESIGNED TO HANDLE BITCOIN
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

wrapper = Wrapper(os.getenv("PHEMEXAPI_ID"), os.getenv("PHEMEXAPI_SECRET"))

fastSMALen = 10
slowSMALen = 75
rsiLen = 14
macdFastLen = 12
macdSlowLen = 26
macdSignalLen = 9
ema100Len = 100

leverage = 5

def strategy(close_data, buy_price, last_candle, exchange):
        lastFastSMA = wrapper.calc_sma(close_data, fastSMALen)
        lastSlowSMA = wrapper.calc_sma(close_data, slowSMALen)
        lastRSI = wrapper.calc_rsi(close_data, rsiLen)
        ema200 = wrapper.calc_ema(close_data, ema100Len)[-1]
        macdLine, signalLine = wrapper.calc_macd(close_data, macdSlowLen, macdFastLen, macdSignalLen)

        buyCondition = macdLine > signalLine and macdLine < 2 and signalLine < 2 and last_candle[2] > ema200 and macdLine - signalLine > 0

        closeCondition1 = (lastFastSMA - lastSlowSMA) / lastSlowSMA <= -.01 and not buyCondition
        closeCondition2 = lastRSI > 80 and not buyCondition
        closeCondition3 = macdLine > signalLine and macdLine > 0 and signalLine > 0 and lastRSI > 65


        # print('Last candle', last_candle, exchange.iso8601(last_candle[0]))
        # print('Last Fast SMA', lastFastSMA)
        # print('Last Slow SMA', lastSlowSMA)
        # print('Last RSI', lastRSI)
        # print('Last Signal', signalLine)
        # print('Last MACD', macdLine)
        # print('Last Long Support', ema200)

        openPosition = buy_price != -1
        print(buy_price)


        if buyCondition and not openPosition:
            wrapper.buy_coin(leverage)

            print("Buy!")
            print('Last candle', last_candle, exchange.iso8601(last_candle[0]))
            print('Last Fast SMA', lastFastSMA)
            print('Last Slow SMA', lastSlowSMA)
            print('Last RSI', lastRSI)
            print('Last Signal', signalLine)
            print('Last MACD', macdLine)
            print('Last Long Support', ema200)

            return last_candle[4]

        elif (closeCondition1 or closeCondition2 or closeCondition3) and openPosition and last_candle[4]*1.0015 > buy_price:
            wrapper.sell_coin(leverage)

            print("Sell!")
            print('Last candle', last_candle, exchange.iso8601(last_candle[0]))
            print('Last Fast SMA', lastFastSMA)
            print('Last Slow SMA', lastSlowSMA)
            print('Last RSI', lastRSI)
            print('Last Signal', signalLine)
            print('Last MACD', macdLine)
            print('Last Long Support', ema200)

            return -1
        
        return buy_price

wrapper.bot_loop(strategy, "5m")