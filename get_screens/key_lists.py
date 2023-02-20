"""
yfinance:               https://pypi.org/project/yfinance/
finnhub                 https://finnhub.io/docs/api                                 60/min
alphavantage            https://www.alphavantage.co/                                500/day
polygon                 https://polygon.io/docs/stocks/getting-started
alpaca                  https://alpaca.markets/docs/api-references/trading-api/

stock prices            https://rapidapi.com/alphawave/api/stock-prices2            500/month
API stocks:             https://rapidapi.com/api4stocks/api/apistocks
twelve data:            https://rapidapi.com/twelvedata/api/twelve-data1
seeking alpha:          https://rapidapi.com/apidojo/api/seeking-alpha              500/month
fidelity                https://rapidapi.com/apidojo/api/fidelity-investments
alphavantage RAPI       https://rapidapi.com/alphavantage/api/alpha-vantage         500/day
cnbc                    https://rapidapi.com/apidojo/api/cnbc
yahoo_finance_1_RAPI    https://rapidapi.com/sparior/api/yahoo-finance15
morningstar             https://rapidapi.com/apidojo/api/ms-finance                 500/month
mboum                   https://rapidapi.com/sparior/api/mboum-finance              500/month

"""

import os
import copy
try:
    import environment_vars
except:
    pass

key_ext = {
    'key_errors': 0,            # number of consecutive errors encountered when using key
    'key_exclude': False,       # killswitch that determines if the key is even used
    'last_used': None,          # datetime the key was last used
    'rate':40                   # number of calls allowed in a 60 second time window, default to 40
}

rapid_api_keys = [
    {'key': os.environ['RAPID_API_KEY_1'], 'key_num': 1, **key_ext},
    {'key': os.environ['RAPID_API_KEY_2'], 'key_num': 2, **key_ext}
]

#############################################################################################

stock_prices_API_keys = copy.deepcopy(rapid_api_keys)
rate = 9.5 # is 10
stock_prices_API_keys[0]['rates'] = rate
stock_prices_API_keys[1]['rates'] = rate
#############################################################################################
API_stocks_keys = copy.deepcopy(rapid_api_keys)
rate = 59 # is 60
API_stocks_keys[0]['rate'] = rate
API_stocks_keys[1]['rate'] = rate
#############################################################################################
twelve_data_keys = copy.deepcopy(rapid_api_keys)
rate = 7.8 # is 8
twelve_data_keys[0]['rate'] = rate
twelve_data_keys[1]['rate'] = rate
#############################################################################################
seeking_alpha_keys = copy.deepcopy(rapid_api_keys)
rate = 290 # is 300
seeking_alpha_keys[0]['rate'] = rate
seeking_alpha_keys[1]['rate'] = rate
#############################################################################################
alphavantage_RAPI_keys = copy.deepcopy(rapid_api_keys)
rate = 4.95 # is 5
alphavantage_RAPI_keys[0]['rate'] = rate
alphavantage_RAPI_keys[1]['rate'] = rate
#############################################################################################
cnbc_keys = copy.deepcopy(rapid_api_keys)
rate = 290 # is 300
cnbc_keys[0]['rate'] = rate
cnbc_keys[1]['rate'] = rate
#############################################################################################
YF_RAPI_keys = copy.deepcopy(rapid_api_keys)
rate = 59 # is 60 to 300 depending on source
YF_RAPI_keys[0]['rate'] = rate
YF_RAPI_keys[1]['rate'] = rate
#############################################################################################
morningstar_keys = copy.deepcopy(rapid_api_keys)
rate = 290 # is 300
morningstar_keys[0]['rate'] = rate
morningstar_keys[1]['rate'] = rate
#############################################################################################
mboum_keys = copy.deepcopy(rapid_api_keys)
rate = 9.5 # is 10
mboum_keys[0]['rate'] = rate
mboum_keys[1]['rate'] = rate
#############################################################################################
fidelity_keys = copy.deepcopy(rapid_api_keys)
rate = 290 # is 300
fidelity_keys[0]['rate'] = rate
fidelity_keys[1]['rate'] = rate
#############################################################################################
alphavantage_keys = [{'key': os.environ['ALPHAVANTAGE_KEY_1'], 'key_num': 1, **key_ext}]
alphavantage_keys[0]['rate'] = 4.95        # is 5
#############################################################################################
polygon_keys = [{'key': os.environ['POLYGON_API_KEY_1'], 'key_num': 1, **key_ext},
                {'key': os.environ['POLYGON_API_KEY_2'], 'key_num': 2, **key_ext}]
rate = 4.95 # is 5
polygon_keys[0]['rates'] = rate
polygon_keys[1]['rates'] = rate
#############################################################################################
finnhub_keys = [{'key': os.environ['FINNHUB_1'], 'key_num': 1, **key_ext},
                {'key': os.environ['FINNHUB_2'], 'key_num': 2, **key_ext}]
rate = 300 # is 1800
finnhub_keys[0]['rate'] = rate
finnhub_keys[1]['rate'] = rate
#############################################################################################
# alpaca                                # 200/min
