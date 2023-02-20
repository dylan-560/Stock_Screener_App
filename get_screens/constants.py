import datetime

DB_NAME = 'screener_data'
FINAL_SCREEN_RESULTS_TABLE_NAME = 'final_screen_results'
#FINAL_SCREEN_RESULTS_TABLE_NAME = 'final_screen_results_dummy'

SAVEPATH_IF_ERROR = r'..\get_screens\save_errors'

MAX_CONSEC_TRIES = 4                    # maximum number of times to recieve an error from an API before it stops being called
REV_SPLIT_CUTOFF = {'PCO':5,'OH':7}     # prev close to current open and current open to current high
BUYOUT_CUTOFF = 5                       # percentage of curr day high to low to recognize and exlcude a buyout
DO_AVERAGE = ['market_cap', 'shares_float', 'short_perc_float', 'shares_short', 'shares_outstanding']
TIME_SENSITIVE_QUOTES = ['high','low','close','volume']

SEND_SMS = False
RATE_LIMITING = True

TODAY = datetime.datetime.today() #2023-02-15 00:03:58.779407
# TODAY = datetime.datetime.today() - datetime.timedelta(days=2)




