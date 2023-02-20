import datetime
import json
import logging
import os
import mysql.connector
import pandas as pd
import numpy
import helper_functions
from constants import DB_NAME, FINAL_SCREEN_RESULTS_TABLE_NAME

try:
    import environment_vars
except:
    pass

def establish_DB_conection():

    conn = mysql.connector.connect(host='localhost',
                                   user='root',
                                   passwd=os.environ['DB_PASSWORD'],
                                   database=DB_NAME,
                                   auth_plugin='mysql_native_password')

    return conn

def end_DB_connection(cursor):
    if conn.is_connected():
        cursor.close()
        conn.close()

####################################################################################
def insert_daily_raw_screen_results(db_conn, screens_list):
    cursor = db_conn.cursor()
    for symbol_dict in screens_list:
        symbol_dict = json.dumps(symbol_dict)
        query = f"INSERT INTO {DB_NAME}.daily_screen_results (screen_result) VALUES ('" + symbol_dict + "');"
        cursor.execute(query, (symbol_dict))
        db_conn.commit()

    cursor.close()
    logging.info('\t ...updating raw screens')

def pull_daily_raw_screen_results(db_conn):

    cursor = db_conn.cursor()
    cursor.execute(f"SELECT * FROM {DB_NAME}.daily_screen_results")
    screen_results = cursor.fetchall()

    ret_list = []
    for result in screen_results:
        result = json.loads(result[0])
        ret_list.append(result)

    cursor.close()
    logging.info('\t ...pulling screen data')
    return ret_list

def delete_daily_screen_results(db_conn):
    cursor = db_conn.cursor()
    cursor.execute(f"DELETE FROM {DB_NAME}.daily_screen_results")
    db_conn.commit()
    cursor.close()
    logging.info('\t ...deleting raw screens')

####################################################################################

def insert_final_results(db_conn, screens_list):
    cursor = db_conn.cursor()

    # saves screen and ohlcv data
    for screen in screens_list:
        insert_keys = []
        insert_values = []
        place_holders = []

        for k,v in screen.items():
            insert_keys.append(k)
            insert_values.append(v)
            place_holders.append('%s')

        query = f"INSERT INTO {DB_NAME}.{FINAL_SCREEN_RESULTS_TABLE_NAME} ("+", ".join(insert_keys)+") VALUES ("+", ".join(place_holders)+")"
        cursor.execute(query, insert_values)

    db_conn.commit()
    cursor.close()
    logging.info('\t ...updated final screen results')

def pull_final_results(db_conn):
    cursor = db_conn.cursor()
    cursor.execute(f"SELECT * FROM {DB_NAME}.{FINAL_SCREEN_RESULTS_TABLE_NAME}")
    screen_results = list(cursor.fetchall())

    ret_list = []
    for result in screen_results:
        ret_list.append(list(result))

    cursor.close()
    logging.info('\t ...pulling screen data')

    return ret_list
####################################################################################
#!!! not used
def insert_OHLCV_data(db_conn, screens_list):

    cursor = db_conn.cursor()

    for symbol_dict in screens_list:
        ticker = symbol_dict['symbol']
        df = symbol_dict['ohlc df']

        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')

        query = f"INSERT INTO {DB_NAME}.ohlcv (ticker, datetime, open, high, low, close, volume) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        for row in df.itertuples():
            cursor.execute(query,(ticker, row.Date, row.Open, row.High, row.Low, row.Close, row.Volume))

    db_conn.commit()
    cursor.close()

#!!! not used
def pull_OHLCV_data(db_conn, ticker, date_time):

    ticker = ticker.upper()
    curr_date_str = str(date_time).split()[0]
    start = curr_date_str + " 00:00:00"
    end = curr_date_str + " 23:59:59"

    cursor = db_conn.cursor()
    query = "SELECT * FROM ohlcv WHERE ticker = (%s) AND datetime BETWEEN (%s) and (%s)"
    df = pd.read_sql(query, con=db_conn,params=[ticker,start,end])

    return df



