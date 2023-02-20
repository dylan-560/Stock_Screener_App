import json
import random
import helper_functions
import logging
import db_connect
import os
import datetime
import pandas as pd
from constants import *
from key_lists import *
from data_sources import QuotesData, StockStats, IntradayCandles
import constants
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s:%(message)s')#,filename='logfile.log')
try:
    import environment_vars
except:
    pass

def run_EOD():

    class ScreenResult():

        def __init__(self, **kwargs):

            self.symbol = kwargs["symbol"].upper()

            if 'timestamp' in kwargs:
                self.timestamp = datetime.datetime.strptime(kwargs['timestamp'], '%Y-%m-%d %H:%M:%S')
            else:
                self.timestamp = datetime.datetime.now()

            if 'source' in kwargs:
                self.source = kwargs['source']

            # kwargs = {key: kwargs[key] for key in kwargs if key not in ['symbol','timestamp','source']}

            for key, value in kwargs.items():
                if key in DO_AVERAGE:
                    setattr(self, key, {self.source: value})
                elif key in TIME_SENSITIVE_QUOTES:
                    setattr(self, key, value)
                    setattr(self,key+'_timestamp',self.timestamp)

                elif key not in ['symbol','timestamp','source']:
                    setattr(self, key, value)

        def timestamped_after_close(self, attr_names):
            # is the quote timestamp after the market close
            ret_vals = []
            for name in attr_names:
                if hasattr(self, name) and name in TIME_SENSITIVE_QUOTES:
                    if getattr(self, name + '_timestamp').hour >= 15:
                        ret_vals.append(True)
                        continue
                ret_vals.append(False)

            return all(i for i in ret_vals)

        def to_dict(self):
            return {key: value for key, value in self.__dict__.items()}

        def conglomerate(self, other):
            # combines ScreenResults instances

            for key, value in vars(other).items():
                key = key.lower()

                if key == 'pct_change':
                    if hasattr(self, key) and hasattr(other, key):
                        if getattr(self, key) < getattr(other,key):
                            setattr(self, key, value)

                elif key in DO_AVERAGE:
                    if self.source != other.source:
                        if hasattr(self, key):
                            sources = {**getattr(self, key), **value}
                        else:
                            sources = value

                        setattr(self, key, sources)

                elif key in TIME_SENSITIVE_QUOTES:
                    if hasattr(other, key):
                        if self.timestamp < other.timestamp:
                            # if self volume is greater than other volume, keep self but set timestamp to other
                            if key.lower() == 'volume' and hasattr(self, 'volume') and other.volume < self.volume:
                                setattr(self, key + '_timestamp', other.timestamp)
                            else:
                                setattr(self, key, value)
                                setattr(self, key+'_timestamp',other.timestamp)

                elif not hasattr(self, key) and key not in ['source','timestamp','symbol'] \
                        and not key.endswith('_timestamp'):
                    setattr(self, key, value)

            if self.timestamp < other.timestamp:
                self.timestamp = other.timestamp

        def do_averages(self, attr_name):

            def numeric_stats_weighted_avg(value_list):

                if not value_list:
                    return None

                # if the list len <= 2 or all values in the list are the same
                if len(value_list) <= 2 or all(x == value_list[0] for x in value_list):  # just do regular average
                    avg = sum(value_list) / len(value_list)
                    return avg

                # if theres 3 or more unique items stored in the value list
                if len(value_list) >= 3:
                    avg_dict = {}

                    for comp_num in value_list:
                        row = []

                        for next_num in value_list:
                            if value_list.index(comp_num) != value_list.index(next_num) and comp_num != next_num:
                                diff = 100 / (abs(comp_num - next_num))
                                row.append(diff)

                        row_sum = sum(row)
                        avg_dict.update({comp_num: row_sum})  # sums all proximity measures

                    val_sum = sum(avg_dict.values())

                    # sums together the weighted avgs
                    avg = 0
                    for k, v in avg_dict.items():
                        try:
                            avg += (k * (v / val_sum))
                        except ZeroDivisionError:
                            pass

                    return avg

            ##############################################################
            try:
                attr_vals = getattr(self, attr_name)
                attr_vals = list(attr_vals.values())
                attr_vals = [v for v in attr_vals if v]

                for val in attr_vals:
                    val = float(helper_functions.string_num_converter(value=val))

                cluster_avg = numeric_stats_weighted_avg(value_list=attr_vals)

                if attr_name != 'short_perc_float':
                    cluster_avg = int(cluster_avg)

                setattr(self, attr_name, cluster_avg)
            except Exception as e:
                error_msg = f'      {e}, on ticker: {self.symbol}, problem getting averages'
                logging.error(error_msg)
                setattr(self, attr_name, None)

        def infer_stats(self):

            try:
                # get short perc float if float and shares short
                if not hasattr(self,'short_perc_float') or not self.short_perc_float:
                    logging.info(f'\t\t\t no short pct float for {self.symbol}, inferring... ')
                    setattr(self, 'short_perc_float', (self.shares_short / self.shares_float) * 100)
            except:
                logging.info(f'\t\t\t\t cant get')
                pass

            try:
                # get float if shares short and short perc float
                if not hasattr(self,'shares_float') or not self.shares_float:
                    logging.info(f'\t\t\t no float for {self.symbol}, inferring... ')
                    setattr(self, 'shares_float', (self.shares_short / self.short_perc_float) * 100)
            except:
                logging.info(f'\t\t\t\t cant get')
                pass

        def filter_by_volume(self):
            # True = dont exclude

            # if the instance has a volume attribute and its timestamped to after the close
            if self.timestamped_after_close(attr_names=['volume']):
                price = 0.0
                if hasattr(self, 'high') and hasattr(self,'low'):
                    price = (self.high + self.low) / 2

                if price:
                    if price <= 1 and self.volume < 15_000_000:
                        logging.info(f'\t\t {self.symbol} excluded on volume')
                        return False

                    if price > 1 and price <= 5 and self.volume < 6_000_000:
                        logging.info(f'\t\t {self.symbol} excluded on volume')
                        return False

                    if price > 5 and price <= 10 and self.volume < 4_000_000:
                        logging.info(f'\t\t {self.symbol} excluded on volume')
                        return False

                    if price > 10 and self.volume < 3_000_000:
                        logging.info(f'\t\t {self.symbol} excluded on volume')
                        return False

            return True

        def filter_buyouts(self):
            # True = dont exclude
            if self.timestamped_after_close(attr_names=['high', 'low']):
                HL_perc_range = ((self.high - self.low) / self.low) * 100
                if HL_perc_range <= BUYOUT_CUTOFF:
                    logging.info(f'\t\t {self.symbol} excluded because suspected buyout')
                    return False

            return True

        def filter_reverse_splits(self):
            # True = dont exclude
            if hasattr(self, 'prev_close') and self.timestamped_after_close(attr_names=['open', 'high']):
                OH_range = ((self.high - self.open) / self.open) * 100
                PCO_range = ((self.open - self.prev_close) / self.prev_close) * 100

                if PCO_range <= REV_SPLIT_CUTOFF['PCO'] and OH_range < REV_SPLIT_CUTOFF['OH']:
                    logging.info(f'\t\t {self.symbol} excluded because suspected reverse split')
                    return False

            return True

        def filter_ticker(self):
            # True = dont exclude

            ex_list = ['_', '-', '.']
            if [e for e in ex_list if e in self.symbol]:
                logging.info(f'\t\t {self.symbol} excluded because ticker')
                return False
            elif len(self.symbol) == 5 and self.symbol[-1] == 'W':
                logging.info(f'\t\t {self.symbol} excluded because ticker')
                return False
            else:
                return True

        def calc_max_pct_gain(self):
            try:
                CO_CH = (self.high - self.open) / self.open
                PC_CH = (self.high - self.prev_close) / self.prev_close
                self.max_pct_gain = (max(CO_CH, PC_CH)) * 100
            except Exception as e:
                logging.error(f'\t\t {e}, on ticker: {self.symbol}')
                self.max_pct_gain = None

        def ext_market_activity(self):
            try:
                self.ext_market_activity = ((self.open - self.prev_close) / self.prev_close) * 100
            except Exception as e:
                logging.error(f'\t\t {e}, on ticker: {self.symbol}')
                self.ext_market_activity = None

        def close_to_range(self):
            try:
                self.close_to_range = ((self.close - self.low) / (self.high - self.low)) * 100
            except Exception as e:
                logging.error(f'\t\t {e}, on ticker: {self.symbol}')
                self.close_to_range = None

        def sma200_distance(self):
            try:
                self.prev_close_to_200sma = ((self.prev_close - self.sma200) / self.sma200) * 100
            except Exception as e:
                logging.error(f'\t\t {e}, on ticker: {self.symbol}')
                self.prev_close_to_200sma = None

        def calc_dollar_volume(self):

            try:
                candle_dollar_volume = ((self.ohlc_data['Open'] + self.ohlc_data['Close']) / 2) * self.ohlc_data['Volume']
                quote_dollar_volume = ((self.high + self.low) / 2) * self.volume
                self.dollar_volume = int(max(candle_dollar_volume.sum(),quote_dollar_volume))
            except Exception as e:
                logging.error(f'\t\t {e}, on ticker: {self.symbol}')
                self.dollar_volume = None

        def finalize_data(self):

            def make_adjustment(k, v):
                if k == 'ohlc_data':
                    v['Date'] = v['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
                    v = v.to_json(orient='records')
                    return v

                if not v:
                    return None

                if k in common_size:
                    v /= 1_000_000
                if k in round_two:
                    v = round(v, 2)
                if k in round_three:
                    v = round(v, 3)
                if k in round_four:
                    v = round(v, 4)

                return v

            ###########################################################################

            common_size = ['market_cap', 'shares_float', 'shares_short', 'shares_outstanding', 'dollar_volume']
            round_two = ['max_pct_gain', 'short_perc_float', 'ext_market_activity', 'close_to_range','prev_close_to_200sma']
            round_three = ['market_cap', 'shares_float', 'shares_short', 'shares_outstanding', 'dollar_volume']
            round_four = ['prev_close']
            keep_keys = ['symbol', 'datetime', 'short_perc_float', 'shares_short', 'shares_outstanding',
                         'shares_float', 'sector', 'prev_close', 'max_pct_gain', 'market_cap',
                         'industry', 'close_to_range', 'ext_market_activity', 'dollar_volume',
                         'prev_close_to_200sma','ohlc_data']

            if isinstance(self.timestamp,datetime.datetime):
                setattr(self, 'datetime', datetime.datetime.strftime(self.timestamp, '%Y-%m-%d').split()[0])

            delete_vars = []
            for key, value in vars(self).items():
                if key in keep_keys:
                    try:
                        value = make_adjustment(k=key, v=value)
                        setattr(self, key, value)
                    except Exception as e:
                        logging.error(f'\t\t {e}, on ticker: {self.symbol}, trying to finalize key: {key}')
                else:
                    delete_vars.append(key)

            for key in delete_vars:
                delattr(self, key)

    ###########################################################################################################
    def shuffle_source_list(s_list):
        if not s_list:
            return s_list
        source_indexes = list(range(0, len(s_list)))
        random.shuffle(source_indexes)
        return [s_list[idx] for idx in source_indexes]

    def pick_method(method_index, ticker, API_list):

        def set_method_index(num):
            # adds + 1 to method index unless youre at the end of the API_list, then it resets index to 0
            return 0 if num >= (len(API_list) - 1) else num + 1

        ################################################
        # checks if all methods have been marked as excluded
        if all(d['exclude'] for d in API_list):
            error_msg = f'ERROR: all quotes APIs arent returning values'
            logging.error(error_msg)
            helper_functions.send_SMS(msg=error_msg)
            exit()

        if all(d['tried'] for d in API_list):
            print('     TRIED ALL APIs, COULD NOT FIND DATA FOR TICKER:', ticker)
            return API_list, None

        # if api is not marked for exclusion or its already been tried for this ticker
        if not API_list[method_index]['exclude'] or API_list[method_index]['tried']:

            # try to get results from selected method
            status, results = API_list[method_index]['API'](ticker=ticker)
            API_list[method_index]['tried'] = True

            # if couldnt fetch results
            if not status:
                API_list[method_index]['errors'] += 1
                if API_list[method_index]['errors'] >= MAX_CONSEC_TRIES:
                    API_list[method_index]['exclude'] = True

                method_index = set_method_index(num=method_index)
                return pick_method(method_index=method_index, ticker=ticker, API_list=API_list)

            else:
                # otherwise result selected api's errors to 0 and return results
                API_list[method_index]['errors'] = 0
                return API_list, results

        # try another one
        else:
            # get the new method index
            method_index = set_method_index(num=method_index)
            return pick_method(method_index=method_index, ticker=ticker, API_list=API_list)

    ############################################################################################################

    def get_screen_data():
        try:
            logging.info('PULLING DAILY SCREEN DATA')
            logging.info('-----------------------------------------------------------------')
            db_connection = db_connect.establish_DB_conection()
            results = db_connect.pull_daily_raw_screen_results(db_conn=db_connection)
            return results

        except Exception as e:
            error_msg = f'ERROR: {e}: problem getting screen data'
            logging.error(error_msg)
            logging.info('-----------------------------------------------------------------')
            helper_functions.send_SMS(msg=error_msg)
            exit()

        finally:
            if db_connection.is_connected():
                db_connection.close()

    def populate(screen_list):
        ret_list = []

        for i in screen_list:
            screen_date = datetime.datetime.strptime(i['timestamp'],'%Y-%m-%d %H:%M:%S').date()
            if screen_date == TODAY.date():
                screen_obj = ScreenResult(**i)
                ret_list.append(screen_obj)

        if not ret_list:
            logging.info(f'NO SCREENS FOR DATE {TODAY} FOUND, EXITING... ')
            exit()

        return ret_list

    def elminate_screen_list_redundancies(screen_list):
        logging.info('REMOVING SCREEN LIST REDUNDANCIES')
        logging.info('-----------------------------------------------------------------')

        found = {}
        for screen in screen_list:

            if screen.symbol in found:
                found[screen.symbol].conglomerate(screen)
            else:
                found[screen.symbol] = screen

        ret_list = [v for v in found.values()]
        ret_list = sorted(ret_list, key=lambda d: d.pct_change, reverse=True)
        return ret_list

    def prelim_screen_filter(screen_list):
        logging.info('RUNNING PRELIM SCREEN ON SCREENS LIST')
        logging.info('-----------------------------------------------------------------')
        ret_list = []

        for screen in screen_list:
            if screen.filter_ticker() and screen.filter_buyouts() and screen.filter_by_volume() and screen.filter_reverse_splits():
                ret_list.append(screen)

        return ret_list

    def prelim_max_pct_gain(screen_list):
        logging.info('RUNNING PRELIM MAX PCT GAIN')
        logging.info('-----------------------------------------------------------------')
        ret_list = []

        for screen in screen_list:

            ret_list.append(screen)
        return ret_list

    def pull_quotes_data(screen_list):

        ###################################################################
        logging.info(f'GETTING QUOTES FOR {len(screen_list)} TICKERS')
        logging.info('-----------------------------------------------------------------')

        quotes = QuotesData()

        source_ext = {'source_errors': 0, 'source_exclude': False}

        quotes_APIs = [
            {'API': quotes.YF_quotes,'keys':[], **source_ext},
            {'API': quotes.alpaca_quotes, 'keys': [], **source_ext},
            {'API': quotes.alphavantage_quotes, 'keys': alphavantage_keys, **source_ext},
            {'API': quotes.alphavantage_RAPID_API_quotes, 'keys': alphavantage_RAPI_keys, **source_ext},
            {'API': quotes.finnhub_quotes, 'keys': finnhub_keys, **source_ext},
            {'API': quotes.twelve_data_quotes, 'keys': twelve_data_keys, **source_ext},
            {'API': quotes.stock_prices_API_quotes, 'keys': stock_prices_API_keys, **source_ext},
            {'API': quotes.fidelity_quotes, 'keys': fidelity_keys, **source_ext},
        ]

        quotes_APIs = shuffle_source_list(s_list=quotes_APIs)

        for enum, screen in enumerate(screen_list):

            # if screen already has quote data
            if screen.timestamped_after_close(attr_names=['high', 'low', 'close', 'volume']) \
                    and hasattr(screen,'prev_close') and hasattr(screen,'open'):
                logging.info('-----------------------------------------------------------------')
                logging.info('\t\t ' + screen.symbol + ' has complete quote data')
                logging.info('-----------------------------------------------------------------')


            else:

                logging.info('-----------------------------------------------------------------')
                logging.info('\t\t ' + screen.symbol)
                logging.info('-----------------------------------------------------------------')

                quotes_APIs = shuffle_source_list(s_list=quotes_APIs)
                quotes_found = False

                for API in quotes_APIs:

                    if not API['source_exclude']:

                        API['keys'] = shuffle_source_list(s_list=API['keys'])

                        API['keys'], results = API['API'](ticker=screen.symbol,
                                                          keys_list=API['keys'])

                        if results:
                            quotes_instance = ScreenResult(**results)
                            screen.conglomerate(quotes_instance)
                            API['source_errors'] = 0
                            quotes_found = True
                            break

                        else:
                            API['source_errors'] += 1
                            if API['source_errors'] >= MAX_CONSEC_TRIES:
                                API['source_exclude'] = True

                if not quotes_found:
                    msg = f'ALL RESOURCES EXHAUSTED FOR {screen.symbol}, EXITING'
                    logging.error(msg)
                    helper_functions.send_SMS(msg=msg)
                    exit()

        return screen_list

    def filter_ticker_list(screen_list):
        logging.info('FILTERING OUT ILLIQUIDS AND BUYOUTS')
        logging.info('-----------------------------------------------------------------')

        ret_list = []
        for screen in screen_list:
            if screen.filter_buyouts() and screen.filter_by_volume() and screen.filter_reverse_splits():
                ret_list.append(screen)

        return ret_list

    def get_max_pct_gain(screen_list):
        logging.info('CALCULATING MAX PCT GAINS')
        logging.info('-----------------------------------------------------------------')
        ret_list = []
        for screen in screen_list:
            screen.calc_max_pct_gain()
            ret_list.append(screen)
        return ret_list

    def get_top_x(screen_list,top_x):
        logging.info('SORTING AND RETURNING TOP GAINERS')
        logging.info('-----------------------------------------------------------------')

        ret_list = sorted(screen_list, key=lambda d: d.max_pct_gain, reverse=True)
        ret_list = ret_list[:top_x]
        logging.info('\t Returning Tickers:')
        for enum,screen in enumerate(ret_list):
            logging.info(f'\t\t{enum+1}. {screen.symbol} {round(screen.max_pct_gain,2)}%')

        logging.info('-----------------------------------------------------------------')
        logging.info('-----------------------------------------------------------------')
        logging.info('-----------------------------------------------------------------')
        return ret_list

    def pull_stats_data(screen_list):

        def get_stats(screen,stats_APIs):

            for API in stats_APIs:

                if all(d['source_exclude'] for d in stats_APIs):
                    error_msg = f'ERROR: all stats APIs not returning values'
                    logging.error(error_msg)
                    helper_functions.send_SMS(msg=error_msg)
                    exit()

                if not API['source_exclude']:

                    API['keys'] = shuffle_source_list(s_list=API['keys'])

                    API['keys'], results = API['API'](ticker=screen.symbol,keys_list=API['keys'])

                    if results:
                        stats_instance = ScreenResult(**results)
                        screen.conglomerate(stats_instance)

                        API['source_errors'] = 0
                    else:
                        API['source_errors'] += 1
                        if API['source_errors'] >= MAX_CONSEC_TRIES:
                            API['source_exclude'] = True

            return screen, stats_APIs

        def get_stats_contingency(screen, scrapers):

            def stats_complete():
                return [s for s in test_stats if hasattr(screen,s) and getattr(screen,s)]

            ################################################

            test_stats = [
                'market_cap',
                'shares_oustanding',
                'shares_float',
                'short_perc_float',
                'shares_short'
            ]

            if not stats_complete():
                logging.info(f'\t\t\t {screen.symbol}: stats incomplete running contingencies')

                scrapers = shuffle_source_list(s_list=scrapers)

                for site in scrapers:
                    if not site['source_exclude']:
                        _, results = site['source'](ticker=screen.symbol)

                        if any([i in results for i in test_stats]):
                            stats_instance = ScreenResult(**results)
                            screen.conglomerate(stats_instance)
                            site['source_errors'] = 0

                            if stats_complete():
                                logging.info(f'\t\t\t\t {screen.symbol}: stats completed')
                                break

                        else:
                            site['source_errors'] += 1
                            if site['source_errors'] >= MAX_CONSEC_TRIES:
                                site['source_exclude'] = True

            return screen, scrapers

        def get_sma_contingency(screen, sma_APIs):
            if not hasattr(screen,'sma200') or not screen.sma200:

                sma_APIs = shuffle_source_list(s_list=sma_APIs)
                sma_found = False

                for API in sma_APIs:
                    API['keys'] = shuffle_source_list(s_list=API['keys'])

                    API['keys'], results = API['API'](ticker=screen.symbol,
                                                      keys_list=API['keys'])

                    if results:
                        screen.sma200 = results['sma200']
                        API['source_errors'] = 0
                        sma_found = True
                        break

                    else:
                        API['source_errors'] += 1
                        if API['source_errors'] >= MAX_CONSEC_TRIES:
                            API['source_exclude'] = True

                if not sma_found:
                    msg = f'ALL RESOURCES FOR GETTING 200SMA EXHAUSTED FOR {screen.symbol}'
                    logging.error(msg)
                    helper_functions.send_SMS(msg=msg)

            return screen, sma_APIs

        ####################################################################################

        logging.info('GETTING STATS DATA')
        logging.info('-----------------------------------------------------------------')

        stats = StockStats()

        source_ext = {'source_errors': 0, 'source_exclude': False}

        stats_APIs = [
            {'API': stats.alphavantage_stats, 'keys': alphavantage_keys, **source_ext},
            {'API': stats.alphavantage_RAPID_API_stats, 'keys': alphavantage_RAPI_keys, **source_ext},
            {'API': stats.cnbc_stats, 'keys': cnbc_keys, **source_ext},
            {'API': stats.yahoo_finance_1_RAPI_stats, 'keys': YF_RAPI_keys, **source_ext},
            {'API': stats.polygon_stats, 'keys': polygon_keys, **source_ext},
            {'API': stats.morningstar_API_stats, 'keys': morningstar_keys, **source_ext},
            {'API': stats.mboum_API_stats, 'keys': mboum_keys, **source_ext},
            #{'API': stats.seeking_alpha_stats, 'keys': seeking_alpha_keys, **source_ext},

        ]

        sma_APIs = [
            {'API': stats.contingency_polygon_200sma, 'keys': polygon_keys, **source_ext},
            {'API': stats.contingency_twelve_data_200sma, 'keys': twelve_data_keys, **source_ext},
        ]

        scrapers = [
            {'source':stats.congingency_stock_analysis_stats,**source_ext},
            {'source':stats.congingency_stock_analysis_stats,**source_ext}
        ]

        for screen in screen_list:
            logging.info('-----------------------------------------------------------------')
            logging.info('\t\t ' + screen.symbol)
            logging.info('-----------------------------------------------------------------')

            screen, stats_APIs = get_stats(screen=screen,stats_APIs=stats_APIs)
            screen, scrapers = get_stats_contingency(screen=screen, scrapers=scrapers)
            screen, sma_APIs = get_sma_contingency(screen=screen, sma_APIs=sma_APIs)

        return screen_list

    def do_averages(screen_list):
        logging.info('GETTING AVERAGES FOR STATS')
        logging.info('-----------------------------------------------------------------')
        for screen in screen_list:
            for metric in DO_AVERAGE:
                screen.do_averages(metric)
                screen.infer_stats()

        return screen_list

    def infer_external_market_activity(screen_list):
        logging.info('CALCULATING PRE/POST MARKET DATA')
        logging.info('-----------------------------------------------------------------')
        for screen in screen_list:
            screen.ext_market_activity()

        return screen_list

    def get_close_from_HOD(screen_list):
        logging.info('CALCULATING CLOSE FROM HOD')
        logging.info('-----------------------------------------------------------------')
        for screen in screen_list:
            screen.close_to_range()

        return screen_list

    def get_dist_from_200sma(screen_list):

        logging.info('CALCULATING DISTANCE FROM 200 SMA')
        logging.info('-----------------------------------------------------------------')
        for screen in screen_list:
            screen.sma200_distance()

        return screen_list

    def pull_intraday_candles(screen_list):
        logging.info('PULLING INTRADAY CANDLE DATA')
        logging.info('-----------------------------------------------------------------')
        ohlc = IntradayCandles()

        source_ext = {'source_errors': 0, 'source_exclude': False}

        ohlc_APIs = [
            {'API': ohlc.API_stocks_intraday, 'keys': API_stocks_keys, **source_ext},
            {'API': ohlc.YF_intraday, 'keys': [], **source_ext},
            {'API': ohlc.twelve_data_intraday, 'keys': twelve_data_keys, **source_ext},
            {'API': ohlc.seeking_alpha_intraday, 'keys': seeking_alpha_keys, **source_ext},
        ]

        for screen in screen_list:
            logging.info('-----------------------------------------------------------------')
            logging.info('\t\t '+screen.symbol)
            logging.info('-----------------------------------------------------------------')

            ohlc_APIs = shuffle_source_list(s_list=ohlc_APIs)
            df_found = False

            for API in ohlc_APIs:
                API['keys'] = shuffle_source_list(s_list=API['keys'])

                API['keys'], results = API['API'](ticker=screen.symbol,
                                                  keys_list=API['keys'])
                if results:
                    if isinstance(results['ohlc_df'],pd.DataFrame) and not results['ohlc_df'].empty:
                        screen.ohlc_data = results['ohlc_df']
                        API['source_errors'] = 0
                        df_found = True
                        break

                else:
                    API['source_errors'] += 1
                    if API['source_errors'] >= MAX_CONSEC_TRIES:
                        API['source_exclude'] = True

            if not df_found:
                msg = f'ALL RESOURCES EXHAUSTED FOR {screen.symbol}, EXITING'
                logging.error(msg)
                helper_functions.send_SMS(msg=msg)
                exit()

        return screen_list

    def get_dollar_volume(screen_list):
        logging.info('GETTING DOLLAR VOLUME')
        logging.info('-----------------------------------------------------------------')
        for screen in screen_list:
            screen.calc_dollar_volume()
        return screen_list

    def finalize_results(screen_list):

        for screen in screen_list:
            screen.finalize_data()

        return screen_list

    def save_final(screen_list=None):

        logging.info('SAVING SCREEN DATA')

        save_list = []
        for screen in screen_list:
            screen = screen.to_dict()
            save_list.append(screen)

        save_successful = False

        try:
            db_connection = db_connect.establish_DB_conection()
            db_connect.insert_final_results(db_conn=db_connection,
                                            screens_list=save_list)
            save_successful = True

        except Exception as e:
            logging.error(f'{e}, problems with database connections')
            helper_functions.send_SMS(msg=error_msg)
            helper_functions.save_to_txt(screen_list=save_list,label='EOD')

        finally:
            if db_connection.is_connected():
                db_connection.close()

        return save_successful

    def delete_raw_screens():
        logging.info('deleting raw screen data')
        try:
            db_connection = db_connect.establish_DB_conection()
            db_connect.delete_daily_screen_results(db_conn=db_connection)
        except Exception as e:
            logging.error(f'{e}, problem deleting raw daily screen data')
            logging.error(error_msg)
            helper_functions.send_SMS(msg=error_msg)
            exit()

        finally:
            if db_connection.is_connected():
                db_connection.close()

    ###############################################################

    logging.info('-----------------------------------------------------------------')
    logging.info('\t\t ' + str(datetime.datetime.now()))
    logging.info('-----------------------------------------------------------------')

    complete_screener_list = get_screen_data()
    complete_screener_list = populate(screen_list=complete_screener_list)
    complete_screener_list = elminate_screen_list_redundancies(screen_list=complete_screener_list)
    complete_screener_list = prelim_screen_filter(screen_list=complete_screener_list)

    ###########################################################################################################
    # new_list = []
    # for screen in complete_screener_list:
    #     if screen.symbol in ['LUNR','AMAM','NEXI','BOXD','CYH','SERA','SRNE','INZY','HOTH','FRHC']:
    #         new_list.append(screen)
    # complete_screener_list = new_list

    # for screen in complete_screener_list:
    #     print(screen.symbol)

    # complete_screener_list = pull_stats_data(screen_list=[complete_screener_list[0], complete_screener_list[19]])

    ###########################################################################################################

    complete_screener_list = pull_quotes_data(screen_list=complete_screener_list)

    complete_screener_list = filter_ticker_list(screen_list=complete_screener_list)
    complete_screener_list = get_max_pct_gain(screen_list=complete_screener_list)
    complete_screener_list = get_top_x(screen_list=complete_screener_list,top_x=10)

    complete_screener_list = pull_stats_data(screen_list=complete_screener_list)

    complete_screener_list = do_averages(screen_list=complete_screener_list)
    complete_screener_list = infer_external_market_activity(screen_list=complete_screener_list)
    complete_screener_list = get_close_from_HOD(screen_list=complete_screener_list)
    complete_screener_list = get_dist_from_200sma(screen_list=complete_screener_list)

    complete_screener_list = pull_intraday_candles(screen_list=complete_screener_list)

    complete_screener_list = get_dollar_volume(screen_list=complete_screener_list)
    complete_screener_list = finalize_results(screen_list=complete_screener_list)

    if save_final(screen_list=complete_screener_list):
        #delete_raw_screens()
        print()
    logging.info('-----------------------------------------------------------------')

if __name__ == '__main__':
    if helper_functions.is_trading_day(curr_date=TODAY):
        run_EOD()
    else:
        logging.info('IS NOT A TRADING DAY')