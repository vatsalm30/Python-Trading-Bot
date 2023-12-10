import ccxt  # noqa: E402
import os
import dotenv
import numpy as np

dotenv.load_dotenv()

phemex = ccxt.phemex({
    "enableRateLimit": True,
    "apiKey": os.getenv("PHEMEXAPI_ID"),
    "secret": os.getenv("PHEMEXAPI_SECRET")
})

symbol = 'ETH/USD:USD'

amountConversion = {
    "BTC/USD:USD": 0.001,
    "ETH/USD:USD": 0.005,
    "TRX/USDT:USDT": 1,
    "XRP/USDT:USDT": 1
}

leverage = 5

# print(phemex.fetch_balance({"type": "swap", "code": "USD"})["USD"]["free"])
# print(phemex.fetch_balance({"type": "swap", "code": "USD"})["USD"]["free"]/phemex.fetch_ticker(symbol)["bid"])

# amount = phemex.fetch_balance({"type": "swap", "code": "USD"})["USD"]["free"]/phemex.fetch_ticker(symbol)["bid"] * leverage
# amountToPay = amount/amountConversion[symbol]
# print(amountToPay < 1)

# if symbol[-1] == "T":
#     phemex.set_position_mode(False, symbol)


def calc_ema(price_data: list, calc_len: int) -> list:
    ema = np.zeros(len(price_data))
    sma = np.mean(price_data[:calc_len])
    ema[calc_len - 1] = sma
    weighting_factor = 2 / (calc_len + 1)

    for i in range(calc_len, len(price_data)):
        ema[i] = (price_data[i] * weighting_factor) + (ema[i - 1] * (1 - weighting_factor))
    return ema.tolist()

print(calc_ema([100, 105, 110, 115, 120, 125, 130, 135, 140, 145.3], 5))

# leverageResponse = phemex.set_leverage(leverage, symbol)

# order = phemex.create_market_buy_order(symbol, amountToPay)
# print(int(phemex.fetch_positions([symbol])[0]["info"]["size"])*amountConversion[symbol])
