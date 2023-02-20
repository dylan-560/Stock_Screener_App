import logging

import pandas as pd
import datetime
import os
from constants import *

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s:%(message)s')#,filename='logfile.log')

try:
    import environment_vars
except:
    pass

def sort_dicts(input_dict):
    input_dict = sorted(list, key=lambda i: i['age'])

def string_num_converter(value, convert_to='num'):
    if value == '-' or value == '' or value == None or value == 'N/A':  # or math.isnan(string) == True:
        return None

    if convert_to == 'num':
        if isinstance(value,(int,float)):
            return value
        # convert string to number
        multipliers = {'K': 1000, 'k': 1000, 'M': 1000000, 'm': 1000000,
                       'B': 1000000000, 'b': 1000000000, 'T': 1000000000000, 't': 1000000000000}

        # # check if getting passed an integer or float
        # test = isinstance(value, (int, float))
        # if test == True:
        #     return value

        # gets rid of unwanted characters
        char_set = [' ', '$', ',']
        for char in char_set:
            if char in value:
                value = value.replace(char, '')

        # check if value is a percentage
        if value[-1] == '%':
            value = value.replace('%', '')
            value = float(value)
            return value

        # check if theres a suffix at the end i.e (5.89M, 600K, ect)
        if value[-1].isalpha():
            mult = multipliers[value[-1]]  # look up suffix to get multiplier
            value = int(float(value[:-1]) * mult)  # convert number to float, multiply by multiplier, then make int
            return value

        # else if theres nothing else that needs to be done return string as number
        else:
            value = float(value)
            if value % 1 == 0:
                return int(value)
            else:
                return value

    if convert_to == 'str':  # convert number to string
        # if the number isn't a percentage
        if value >= 1:
            value = '{:,}'.format(value)
            return value

        if value < 1 and value > -1:
            value = str(round((value * 100), 2)) + '%'
            return value

def convert_to_capitalized(input):
    input = input.split(" ")
    input = [p.capitalize() for p in input]
    input = " ".join(input)

    return input

def normalize_names(input_list,names_conversion_dict):
    ret_list = []

    for symbol_dict in input_list:
        temp_dict = {}
        for k,v in symbol_dict.items():
            if k in names_conversion_dict.keys():
                k = names_conversion_dict[k]
            temp_dict[k] = v

        ret_list.append(temp_dict)

    return ret_list

def calculate_VWAP(df):

    df = df.sort_values(by='Date')
    df.reset_index(inplace=True, drop=True)
    df['cum_vol'] = df['Volume'].cumsum()
    df['cum_vol_price'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum()
    df['vwap'] = df['cum_vol_price'] / df['cum_vol']

    vwap = float(df.iloc[-1]['vwap'])
    return vwap

def candle_resampler(input_df, timeframe=str):
    """
    inputs origonal dataframe and selected timeframe and outputs dataframe of desired output conversion timeframe

    input dataframe input:

    Date, Open, High, Low, Close, Volume

    timeframe : '15min' , 1hr:'60min', 4hr:'240min', 1day:'1440min'

    """

    def fill_in(cols):
        volume = cols[0]
        target = cols[1]
        stock_close = cols[2]

        if volume == 0:
            target = stock_close

        return target

    #########################################

    if input_df['Date'].dtype != 'datetime64[ns]':
        # conver to datetime
        input_df['Date'] = pd.to_datetime(input_df['Date'])  # , unit='ms'))

    input_df = input_df.set_index(pd.DatetimeIndex(input_df['Date']))

    data_ohlc = input_df.resample(timeframe).agg({'Open': 'first',
                                                  'High': 'max',
                                                  'Low': 'min',
                                                  'Close': 'last',
                                                  'Volume': 'sum'})

    data_ohlc = data_ohlc.reset_index()

    data_ohlc['Close'] = data_ohlc['Close'].fillna(method='ffill')
    data_ohlc['Open'] = data_ohlc[['Volume', 'Open', 'Close']].apply(fill_in, axis=1)
    data_ohlc['High'] = data_ohlc[['Volume', 'High', 'Close']].apply(fill_in, axis=1)
    data_ohlc['Low'] = data_ohlc[['Volume', 'Low', 'Close']].apply(fill_in, axis=1)

    return data_ohlc

def get_last_x_trading_days(curr_date=TODAY.date(), days=5):
    import pandas as pd
    import pandas_market_calendars as mcal

    def get_dates_list():
        start = (curr_date - datetime.timedelta(days=lookback))

        dates_df = nyse.schedule(start_date=start.strftime('%Y-%m-%d'),
                                 end_date=curr_date.strftime('%Y-%m-%d'))

        dates_list = list(dates_df.to_dict(orient='index'))
        ret_list = [x.to_pydatetime() for x in dates_list]
        return ret_list

    ######################################################

    nyse = mcal.get_calendar('NYSE')

    lookback = days

    ret_list = get_dates_list()

    while len(ret_list) < days:
        lookback += 1
        ret_list = get_dates_list()

    return ret_list

def get_previous_trading_day(curr_date):
    curr_date = datetime.datetime.combine(curr_date, datetime.time.min)
    dates_list = get_last_x_trading_days(curr_date=curr_date)

    if curr_date == dates_list[-1]:
        return dates_list[-2]
    else:
        return dates_list[-1]

def is_trading_day(curr_date):
    curr_date = curr_date.date()

    dates_list = get_last_x_trading_days(curr_date=curr_date)

    if curr_date == dates_list[-1].date():
        return True
    else:
        return False

def label_dicts_in_list(source_name,input_list):
    ret_list = []
    for symbol_dict in input_list:
        symbol_dict['source'] = source_name
        symbol_dict['timestamp'] = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
        ret_list.append(symbol_dict)
    return ret_list

def send_SMS(msg):
    if SEND_SMS:
        try:
            from twilio.rest import Client

            # Set environment variables for your credentials
            # Read more at http://twil.io/secure
            account_sid = os.environ['TWILIO_ACCT_SID']
            auth_token = os.environ['TWILIO_AUTH_TOKEN']
            client = Client(account_sid, auth_token)

            message = client.messages.create(
                body=msg,
                from_="+19253926048",
                to=os.environ['MY_PHONE_NUMBER'])
        except Exception as e:
            logging.info(f'PROBLEM SENDING SMS, ERRORS: {e}')

def save_to_txt(screen_list,label):
    logging.info(f'saving {label} to local files')

    label = label.replace(' ','_')

    filename = f'{label}_{TODAY.strftime("%Y-%m-%d_%H-%M-%S")}.txt'
    filepath = f'{SAVEPATH_IF_ERROR}\\{filename}'

    file = open(filepath,'w')

    #with open(filepath, 'w') as f:
    with file as f:
        # Write each dictionary to the file on a separate line
        for screen in screen_list:
            f.write(str(screen) + '\n')


    logging.info(f'{label} saved to {filepath}')

def read_from_txt(filename):
    filepath = f'{SAVEPATH_IF_ERROR}\\{filename}'

    ret_list = []

    with open(filepath, 'r') as f:
        for line in f:
            ret_list.append(eval(line))

    return ret_list



