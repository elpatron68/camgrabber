import sys
import os
import time
import urllib.request
import requests
import ntpath
import logging
import shutil
import configparser
import subprocess
from datetime import date
from datetime import timedelta
from datetime import datetime
from shutil import copyfile
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import ffmpeg
from skyfield import api
from skyfield import almanac

# Initiate logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logging.info('Starting Camgrabber')

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
START_BEFORE_SUNDAWN = int(CONFIG['recording']['start_before_dawn'])
END_AFTER_SUNDOWN = int(CONFIG['recording']['end_after_sundown'])


def get_images(day, path):
    logging.debug(f'Creating directories {path}')
    try:
        os.mkdir(path)
        os.mkdir('longterm')
    except OSError:
        logging.debug(f'Creation of the directory {path} failed')
    counter = 0
    longterm_counter = 0
    indexfile = f'{path}/lastindex.txt'
    
    if os.path.isfile(indexfile):
        logging.info(f'Reading last image index from {indexfile}')
        f = open(indexfile)
        counter = int(f.read())
        logging.info(f'Last image index: {counter}')
        counter += 1
        f.close()

    weathercount = 0
    sun = get_sun()
    sun_dawn = datetime.strptime(sun[0], '%Y-%m-%dT%H:%M:%SZ')
    logging.debug(f'Sun dawn: {sun_dawn}')
    sun_down = datetime.strptime(sun[1], '%Y-%m-%dT%H:%M:%SZ')
    logging.debug(f'Sun down: {sun_down}')
    start = sun_dawn - timedelta(minutes=START_BEFORE_SUNDAWN)
    logging.debug(f'Start: {start}')
    end = sun_down + timedelta(minutes=END_AFTER_SUNDOWN)
    timediff_secs = (end - start).seconds
    logging.debug(f'End: {end}')
    load_interval = int(CONFIG['recording']['interval'])
    weather_interval = int(CONFIG['weather']['interval'])
    while day == date.today():
        now = datetime.utcnow()
        if now > start and now < end:
            logging.info(f'Start recording until {end}')
            logging.info('Loading image')
            f = CONFIG['general']['filename'].replace('%i', str(counter).zfill(5))
            fullname = f'{path}/{f}'
            logging.debug(f'Image file name: {fullname}')
            if weathercount == 0:
                logging.info('Loading new weather information')
                weatherdata = get_weather()
            weathercount += 1
            urllib.request.urlretrieve(CONFIG['recording']['url'], fullname)
            # Keep 50 images after noon for long term time lapse (without weather information)
            if CONFIG['recording']['long_term'].lower() == 'true':
                if counter > (timediff_secs / load_interval / 2) and longterm_counter < 50:
                    f1 = CONFIG['general']['filename'].replace('%i', str(longterm_counter).zfill(2))
                    d1 = date.today().strftime('%Y%m%d')
                    logging.info(f'Saving image #{longterm_counter} for long term time lapse: {d1}-lt-{f1}')
                    dst = f'longterm/{d1}-lt-{f1}'
                    copyfile(fullname, dst)
                    longterm_counter += 1
                    pass
            insert_weather_data(fullname, weatherdata)
            if counter > 0:        
                save_lastindex(path, counter)
            counter += 1
            time.sleep(load_interval)
            if weathercount > (60 / load_interval * weather_interval):
                logging.debug('Resetting weather counter to zero')
                weathercount = 0
        else:
            logging.info(f'Stop recording. {str(counter)} images saved.')
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
        logging.debug(f'Creation of the directory {dest_path} failed')

    logging.info(f'Rendering images from {source_path} to mp4 video file: {fullname}')
    (
        ffmpeg
        .input(f'{source_path}/*{file_extension}', pattern_type='glob', framerate=25)
        .output(f'{fullname}')
        .run()
    )
    return fullname
        

def get_weather():
    base_url = 'http://api.openweathermap.org/data/2.5/weather?'
    apikey = CONFIG['weather']['openweather_apikey']
    location_id = CONFIG['weather']['openweather_id']
    units = CONFIG['weather']['units']
    complete_url = f'{base_url}appid={apikey}&id={location_id}&units={units}'
    logging.info(f'Getting weather information from {complete_url}')
    response = requests.get(complete_url)
    x = response.json()
    try:
        if x['cod'] != '404': 
            main = x['main'] 
            current_temperature = main['temp']
            current_pressure = main['pressure'] 
            wind = x['wind']
            windspeed = wind['speed']
            winddirection = wind['deg']
            logging.debug(f'Temp: {current_temperature}, Pressure: {current_pressure}, Wind speed: {windspeed}, Wind direction: {winddirection}')
            return current_temperature, current_pressure, windspeed, winddirection
    except:
        logging.warn(f'Failed to retreive weather data. Response was\n {x}')


def insert_weather_data(imagefile, data):
    img_xpos = int(CONFIG['rendering']['img_xpos'])
    img_ypos = int(CONFIG['rendering']['img_ypos'])
    txt_xpos = int(CONFIG['rendering']['txt_xpos'])
    txt_ypos = int(CONFIG['rendering']['txt_ypos'])
    ypos_step = int(CONFIG['rendering']['ypos_step'])
    fontsize = int(CONFIG['rendering']['fontsize'])
    if CONFIG['weather']['units'] == 'metric':
        temp_unit = "C"
        wind_unit = "m/s"
    else:
        temp_unit = "F"
        wind_unit = "miles/hour"
    logging.info(f'Inserting weather information into image {imagefile}')
    background = Image.open(imagefile)
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(r'MicrosoftSansSerifRegular.ttf', fontsize)
    # img_w, img_h = background.size
    img_wind = Image.open('wind_32.png', 'r')
    background.paste(img_wind, (img_xpos, img_ypos), img_wind)
    img_compass = Image.open('compass_32.png', 'r')
    background.paste(img_compass, (img_xpos, img_ypos + ypos_step), img_compass)
    img_temp = Image.open('temperature_32.png', 'r')
    background.paste(img_temp, (img_xpos, img_ypos + ypos_step * 2), img_temp)
    img_pressure = Image.open('pressure_32.png', 'r')
    background.paste(img_pressure, (img_xpos, img_ypos + ypos_step * 3), img_pressure)
    draw.text((txt_xpos, txt_ypos + ypos_step * 0),f'{data[2]} {wind_unit}', font=font, fill=(0,0,0,255))
    draw.text((txt_xpos, txt_ypos + ypos_step * 1),f'{data[3]}°', font=font, fill=(0,0,0,255))
    draw.text((txt_xpos, txt_ypos + ypos_step * 2),f'{data[0]}° {temp_unit}', font=font, fill=(0,0,0,255))
    draw.text((txt_xpos, txt_ypos + ypos_step * 3),f'{data[1]} hPa', font=font, fill=(0,0,0,255))
    background.save(imagefile)
    pass
    

def cleanup(path):
    if CONFIG['recording']['delete_images'].lower() == 'true':
        logging.info(f'Cleanup: Remove directory {path}')
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except:
                logging.warn('Cleanup failed')
                pass
    else:
        logging.debug('Deleting of image files disabled')
        

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

def upload_youtube(filename):
    title = CONFIG['youtube']['title']
    playlist = CONFIG['youtube']['playlist']
    embeddable = CONFIG['youtube']['embeddable']
    privacy = CONFIG['youtube']['privacy']
    logging.info(f'Uploading {filename} to YouTube. Playlist: {playlist}, title: {title}, privacy: {privacy}')
    subprocess.call(['youtube-upload', f'--title={title}', f'--playlist={playlist}', f'--embeddable={embeddable}', f'--privacy={privacy}', filename])
    pass

if __name__ == '__main__':
    dark = False
    while 1:
        today = date.today()
        sun = get_sun()
        path = today.strftime('%Y%m%d')
        now = datetime.utcnow()
        sun_dawn_utc = datetime.strptime(sun[0], '%Y-%m-%dT%H:%M:%SZ')
        sun_down_utc = datetime.strptime(sun[1], '%Y-%m-%dT%H:%M:%SZ')
        start = sun_dawn_utc - timedelta(minutes=START_BEFORE_SUNDAWN)
        end = sun_down_utc + timedelta(minutes=END_AFTER_SUNDOWN)
        if now > start and now < end:
            logging.info('The sun has risen, start recording')
            dark = False
            get_images(today, path)
            videofile = create_timelapse(today, path, CONFIG['general']['destination_path'])
            logging.info(f'Video rendered: {videofile}')
            cleanup(path)
            if CONFIG['youtube']['enabled'].lower() == 'true':
                upload_youtube(videofile)
        else:
            if dark == False:
                logging.info(f'It is too dark outside, recording paused until {start} UTC')
                dark = True
            time.sleep(60)