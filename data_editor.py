import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import datetime
import ccxt
import os
import dotenv

dotenv.load_dotenv()

phemex = ccxt.phemex({
    "enableRateLimit": True,
    "apiKey": os.getenv("PHEMEXAPI_ID"),
    "secret": os.getenv("PHEMEXAPI_SECRET")
})

creds = ServiceAccountCredentials.from_json_keyfile_name("gs_credentials.json")
client = gspread.authorize(creds)

sheet = client.open("ETH Bot Tracker").sheet1

print("Starting Server")
hold = 30

while True:
    try:
        balance = phemex.fetch_balance({"type": "swap", "code": "USD"})["USD"]["total"]
        print("Balance: " + str(balance))
        current_date = datetime.datetime.now().strftime("%m/%d/%y")
        dates_list = sheet.col_values(1)
        for row, date in enumerate(dates_list):
            if date == current_date:
                sheet.update_cell(row + 1, 3, balance)
                print("Sheet Updated")
                break

        time.sleep(3600)
    except (ccxt.ExchangeError, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout,
            ccxt.NetworkError) as error:
        print('Got an error', type(error).__name__, error.args, ', retrying in', hold, 'seconds...')
        time.sleep(300)

