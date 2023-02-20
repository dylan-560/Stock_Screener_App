import schedule
import time
import datetime
from end_of_day import run_EOD
from run_screeners import run_screeners
import logging


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s func:%(funcName)s line:%(lineno)d %(levelname)s:%(message)s')

schedule.every().day.at("08:45").do(run_screeners)
schedule.every().day.at("10:40").do(run_screeners)
schedule.every().day.at("12:30").do(run_screeners)
schedule.every().day.at("14:00").do(run_screeners)
schedule.every().day.at("15:03").do(run_screeners)

#schedule.every().day.at("16:30").do(run_EOD)

run_time = 0
print(datetime.datetime.now(),'starting...')
while True:
    time.sleep(60)
    run_time+=60
    if run_time >= 900:
        print(datetime.datetime.now(),' still running...')
        run_time = 0

    schedule.run_pending()
