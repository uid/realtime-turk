import os
from datetime import datetime, timedelta
import time
from decimal import Decimal

def parseISO(input):
    input_no_z = input[:-1]
    split_dt = input_no_z.split('.')
    no_millis = datetime.strptime( split_dt[0], "%Y-%m-%dT%H:%M:%S" )
    
    millis = 0
    if len(split_dt) == 2:
        millis = int(split_dt[1])  # remove the 'Z' at the end
    
    final_date = no_millis + timedelta(milliseconds = millis)
    
    return unixtime(final_date)

def unixtime(dt):
    millis = dt.microsecond/1000000.
    return Decimal(str(time.mktime(dt.timetuple()) + millis))

def total_seconds(td):
    return td.days * 3600 * 24 + td.seconds + td.microseconds / 1000000.0
    
os.environ['TZ'] = 'America/NewYork'
time.tzset()