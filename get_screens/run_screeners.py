import helper_functions
import os
import json
import random
from data_sources import Screeners
import db_connect
import logging
from constants import *

logging.basicConfig(level=logging.INFO,
                    format='func:%(funcName)s line:%(lineno)d %(levelname)s:%(message)s') #filename='logfile.log')

try:
    import environment_vars
except:
    pass

def shuffle_APIs(API_dict):
    ret_dict = {}
    for name,sources_list in API_dict.items():
        source_indexes = list(range(0, len(sources_list)))
        random.shuffle(source_indexes)

        shuffled = [sources_list[idx] for idx in source_indexes]
        ret_dict[name] = shuffled

    return ret_dict

def run_screeners():
    screeners = Screeners()

    all_screeners = {
        'tradingview':[screeners.tradingview_screener_key_1, screeners.tradingview_screener_key_2],
        'yahoofinance':[screeners.yahoo_finance_screener_key_1,screeners.yahoo_finance_screener_key_2],
        'schwab':[screeners.schwab_screener_key_1,screeners.schwab_screener_key_2],
        'finviz':[screeners.finviz_screener]
    }

    all_screeners = shuffle_APIs(API_dict=all_screeners)

    save_list = []

    for screen_list in all_screeners.values():

        for screen in screen_list:
            screen_results = screen()
            if screen_results:
                save_list += screen_results
                break

    try:
        db_connection = db_connect.establish_DB_conection()
        db_connect.insert_daily_raw_screen_results(db_conn=db_connection, screens_list=save_list)

    except Exception as e:
        error_msg = f'ERROR: {e}: problem saving screen data'
        logging.error(error_msg)
        helper_functions.save_to_txt(screen_list=save_list, label='daily_screen')

    finally:
        if db_connection.is_connected():
            db_connection.close()

if __name__ == '__main__':
    if helper_functions.is_trading_day(curr_date=TODAY):
        try:
            run_screeners()
        except Exception as e:
            error_msg = f'ERROR: {e} screener failed'
            logging.error(error_msg)
            helper_functions.send_SMS(msg=error_msg)

    else:
        logging.info('IS NOT A TRADING DAY')