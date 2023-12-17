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
leverage = 5

def strategy(close_data, buy_price, last_candle, exchange):
        lastFastSMA = wrapper.calc_sma(close_data, fastSMALen)
        lastSlowSMA = wrapper.calc_sma(close_data, slowSMALen)
        lastRSI = wrapper.calc_rsi(close_data, rsiLen)

        buyCondition = lastFastSMA > lastSlowSMA
        buyCondition2 = lastRSI <= 30
        buyConditionFilter = lastRSI <= 58

        closeCondition1 = (lastFastSMA - lastSlowSMA) / lastSlowSMA <= -.01
        closeCondition2 = lastRSI > 73


        print('Last candle', last_candle, exchange.iso8601(last_candle[0]))
        print('Last Fast SMA', lastFastSMA)
        print('Last Slow SMA', lastSlowSMA)
        print('Last RSI', lastRSI)


        openPosition = buy_price != -1


        if (buyCondition or buyCondition2) and buyConditionFilter and not openPosition:
            # wrapper.buy_coin(leverage)

            print("Buy!")
            print('Last candle', last_candle, exchange.iso8601(last_candle[0]))
            print('Last Fast SMA', lastFastSMA)
            print('Last Slow SMA', lastSlowSMA)
            print('Last RSI', lastRSI)

            return last_candle[4]

        elif (closeCondition1 or closeCondition2) and openPosition and last_candle[4] > buy_price:
            # wrapper.sell_coin(leverage)

            print("Sell!")
            print('Last candle', last_candle, exchange.iso8601(last_candle[0]))
            print('Last Fast SMA', lastFastSMA)
            print('Last Slow SMA', lastSlowSMA)
            print('Last RSI', lastRSI)
            
            return -1
        
        return buy_price

wrapper.bot_loop(strategy, "1m")