import sys
import os
import time
import urllib.request
import requests
import ntpath
import logging
import shutil
import configparser
from datetime import date
from datetime import timedelta
from datetime import datetime
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import ffmpeg
from skyfield import api
from skyfield import almanac

# Read configuration file
CONFIG = configparser.ConfigParser()
if os.path.isfile('camgrabber.ini'):
    logging.info('Using camgrabber.ini')
    CONFIG.read('camgrabber.ini')
elif os.path.isfile('camgrabber.default.ini'):
    CONFIG.read('camgrabber.default.ini')
    logging.info('Using default.ini')
else:
    sys.exit()

# Constants
START_BEFORE_SUNDAWN = CONFIG['recording']['start_before_dawn']
END_AFTER_SUNDOWN = CONFIG['recording']['end_after_sundown']


def get_images(day, path):
    logging.debug(f'Creating directory {path}')
    try:
        os.mkdir(path)
    except OSError:
        logging.warn(f'Creation of the directory {path} failed')
    counter = 0
    indexfile = f'{path}/lastindex.txt'
    
    if os.path.isfile(indexfile):
        logging.info(f'Reading last image index from {indexfile}')
        f = open(indexfile)
        counter = int(f.read())
        logging.info(f'Las image index: {counter}')
        counter += 1
        f.close()
        try:
            logging.debug('Delete index file')
            os.remove(indexfile)
        except OSError:
            pass

    weathercount = 0
    sun = get_sun()
    sun_dawn = datetime.strptime(sun[0], '%Y-%m-%dT%H:%M:%SZ')
    logging.debug(f'Sun dawn: {sun_dawn}')
    sun_down = datetime.strptime(sun[1], '%Y-%m-%dT%H:%M:%SZ')
    logging.debug(f'Sun down: {sun_down}')
    start = sun_dawn - timedelta(hours=START_BEFORE_SUNDAWN)
    logging.debug(f'Start: {start}')
    end = sun_down + timedelta(hours=END_AFTER_SUNDOWN)
    logging.debug(f'End: {end}')

    while day == date.today():
        now = datetime.utcnow()
        if now > start and now < end:
            logging.info('Loading image')
            f = CONFIG['general']['filename'].replace('%i', str(counter).zfill(5))
            fullname = f'{path}/{f}'
            logging.debug(f'Image file name: {fullname}')
            if weathercount == 0:
                logging.info('Loading new weather information')
                weatherdata = get_weather()
            weathercount += 1
            urllib.request.urlretrieve(CONFIG['recording']['url'], fullname)
            logging.info('Inserting weather into image')
            insert_weather_data(fullname, weatherdata)
            save_lastindex(path, counter)
            counter += 1
            time.sleep(CONFIG['recording']['interval'])
            if weathercount > 39:
                logging.debug('Resetting weather counter to zero')
                weathercount = 0
        else:
            logging.info('Time before start or after end, breaking loop')
            break


def create_timelapse(day, source_path, dest_path):
    date = day.strftime('%Y%m%d')
    f = CONFIG['general']['filename'].replace('%i', date)
    fn, file_extension = os.path.splitext(f)
    fn = path_leaf(fn)
    fullname = f'{dest_path}/{fn}.mp4'
    logging.info(f'Creating time lapse: {fullname}')

    try:
        os.mkdir(dest_path)
    except OSError:
        logging.warn(f'Creation of the directory {dest_path} failed')

    logging.info(f'Rendering images from {source_path} to mp4 video file: {fullname}')
    (
        ffmpeg
        .input(f'{source_path}/*{file_extension}', pattern_type='glob', framerate=25)
        .output(f'{fullname}')
        .run()
    )
        

def get_weather():
    base_url = 'http://api.openweathermap.org/data/2.5/weather?'
    apikey = CONFIG['weather']['openweather_apikey']
    location_id = CONFIG['weather']['openweather_id']
    units = CONFIG['weather']['units']
    complete_url = f'{base_url}appid={apikey}&id={location_id}&units={units}'
    logging.info(f'Getting weather information from {complete_url}')
    response = requests.get(complete_url)
    x = response.json()
    if x['cod'] != '404': 
        main = x['main'] 
        current_temperature = main['temp']
        current_pressure = main['pressure'] 
        wind = x['wind']
        windspeed = wind['speed']
        winddirection = wind['deg']
        logging.debug(f'Temp: {current_temperature}, Pressure: {current_pressure}, Wind speed: {windspeed}, Wind direction: {winddirection}')
        return current_temperature, current_pressure, windspeed, winddirection


def insert_weather_data(imagefile, data):
    logging.info(f'Inserting weather information into image {imagefile}')
    img = Image.open(imagefile)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(r'MicrosoftSansSerifRegular.ttf', 16)
    draw.text((20, 40),f'Wind speed: {data[2]} m/s', font=font, fill=(255,0,0,255))
    draw.text((20, 60),f'Wind direction: {data[3]}°', font=font, fill=(255,0,0,255))
    draw.text((20, 80),f'Air pressure: {data[1]} mbar', font=font, fill=(255,0,0,255))
    draw.text((20, 100),f'Air temperature: {data[0]}° C', font=font, fill=(255,0,0,255))
    img.save(imagefile)
    pass
    

def cleanup(path):
    logging.info(f'Cleanup: Remove directory {path}')
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except:
            logging.warn('Cleanup failed')
            pass
        

def get_sun():
    lat = CONFIG['sun']['lat']
    lon = CONFIG['sun']['lon']
    logging.debug(f'Calculating sun dawn end down for LAT {lat}, LON {lon}')
    location = api.Topos(lat, lon)
    ts = api.load.timescale()
    e = api.load('de421.bsp')
    today = date.today()
    t0 = ts.utc(today.year, today.month, today.day, 0)
    t1 = ts.utc(today.year, today.month, today.day, 23)
    t, y = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(e, location))
    sun = t.utc_iso()
    return sun


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def save_lastindex(path, index):
    indexfile = f'{path}/lastindex.txt'
    logging.debug(f'Saving last image index ({index}) to {indexfile}')
    f = open(indexfile, 'w')
    f.write(str(index))
    f.close
    pass

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
    while 1:
        today = date.today()
        sun = get_sun()
        path = today.strftime('%Y%m%d')
        now = datetime.utcnow()
        sun_dawn_utc = datetime.strptime(sun[0], '%Y-%m-%dT%H:%M:%SZ')
        sun_down_utc = datetime.strptime(sun[1], '%Y-%m-%dT%H:%M:%SZ')
        start = sun_dawn_utc - timedelta(hours=START_BEFORE_SUNDAWN)
        end = sun_down_utc + timedelta(hours=END_AFTER_SUNDOWN)
        if now > start and now < end:
            get_images(today, path)
            for fname in os.listdir(path):
                if fname.endswith('.jpg'):
                    create_timelapse(today, path, CONFIG['general']['destination_path'])
                    cleanup(path)
        else:
            print('It´s still dark outside...')
            time.sleep(60)