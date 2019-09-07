# Database functions
import os
import sys
from datetime import date, datetime
import sqlite3
from sqlite3 import Error

def update_db(db_file, table_name, data):
    conn = None
    try:
        conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    except Error as e:
        pass
    try:
        temp = float(data['temperature'])
        pressure = float(data['pressure'])
        wind = float(data['windspeed'])
        winddirection = int(data['winddirection'])
    except Error as e:
        print(f'Conversion failed: {e}')
    now = datetime.now()
    try:
        c = conn.cursor()
        c.execute(f'''INSERT INTO {table_name} (ts, windspeed, winddirection, pressure, temperature) VALUES (?, ?, ?, ?, ?);''', (now, wind, winddirection, pressure, temp))
        conn.commit()
        conn.close()
    except Error as e:
        print(e)
    pass

def get_today_avg(db_file, table_name):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        pass
    pass


def create_db_table(db_file, table_name):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        pass

    create_table_sql = f"""CREATE TABLE IF NOT EXISTS {table_name} (
                            id integer PRIMARY KEY,
                            ts timestamp,
                            windspeed real,
                            winddirection integer,
                            pressure real,
                            temperature real
                        );"""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        conn.close()
    except Error as e:
        print(e)

if __name__ == '__main__':
    create_db_table('camgrabber.sqlite3', 'ycn')
