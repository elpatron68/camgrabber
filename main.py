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
import re
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
import database

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
    logging.warn('Falling back to default ini. Possibly, at least the openweather API key is missing! Other things may go wrong, too.')
else:
    sys.exit()

# Set log level from configuration
if CONFIG['general']['loglevel'].lower() == 'debug':
    logging.getLogger().setLevel(logging.DEBUG)
elif CONFIG['general']['loglevel'].lower() == 'info':
    logging.getLogger().setLevel(logging.INFO)
elif CONFIG['general']['loglevel'].lower() == 'warning':
    logging.getLogger().setLevel(logging.WARNING)

# Constants
START_BEFORE_SUNDAWN = int(CONFIG['recording']['start_before_dawn'])
END_AFTER_SUNDOWN = int(CONFIG['recording']['end_after_sundown'])

def get_images(day, path):
    logging.debug(f'Creating directories {path}')
    try:
        os.mkdir(path)
    except OSError:
        logging.debug(f'Creation of the directory {path} failed')
    try:
        os.mkdir('longterm')
    except OSError:
        logging.debug(f'Creation of the directory longterm failed')
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
    number_of_images = int(timediff_secs / load_interval)
    weather_interval = int(CONFIG['weather']['interval'])
    if datetime.utcnow() > start and datetime.utcnow() < end:
        logging.info(f'Start recording a total number of {number_of_images} images until {end}')
        send_telegram(f'Good morning. Camgrabber starts recording a total number of {number_of_images} images until {end} UTC.')

    while day == date.today():
        now = datetime.utcnow()
        if now > start and now < end:
            logging.debug('Loading image')
            f = CONFIG['general']['filename'].replace('%i', str(counter).zfill(5))
            fullname = f'{path}/{f}'
            logging.info(f'Processing image #{counter +1}/{number_of_images} - filename: {fullname}')
            if weathercount == 0:
                logging.debug('Loading new weather information')
                weatherdata = get_weather()
            weathercount += 1
            try:
                urllib.request.urlretrieve(CONFIG['recording']['url'], fullname)
            except urllib.error.URLError as e:
                logging.warn(f'Failed loading image (URLError): {str(e)}')
            except urllib.error.HTTPError as e:
                logging.warn(f'Failed loading image (HTTPError): {str(e)}')
            except:
                logging.warn('Unknown error')
            
            if os.path.isfile(fullname):
                insert_weather_data(fullname, weatherdata)
            else:
                logging.error(f'No image file found.')
            
            # Keep 50 images after noon for long term time lapse (without weather information)
            if CONFIG['recording']['long_term'].lower() == 'true':
                startlongterm = timediff_secs / load_interval / 2
                endlongterm = startlongterm + 50
                if counter > startlongterm and longterm_counter < 50 and counter < endlongterm:
                    f1 = CONFIG['general']['filename'].replace('%i', str(longterm_counter).zfill(2))
                    d1 = date.today().strftime('%Y%m%d')
                    logging.info(f'Saving image #{longterm_counter} for long term time lapse: {d1}-lt-{f1}')
                    dst = f'longterm/{d1}-lt-{f1}'
                    copyfile(fullname, dst)
                    longterm_counter += 1
            
            if counter > 0:        
                save_lastindex(path, counter)
            counter += 1
            time.sleep(load_interval)
            if weathercount > (60 / load_interval * weather_interval):
                logging.debug('Resetting weather counter to zero')
                weathercount = 0
        else:
            logging.info(f'Stop recording. {str(counter)} images saved.')
            send_telegram(f'Good evening. Camgrabber stops recording images now. We have collected {str(counter)} images today. The video will be rendered, now.')
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
    send_telegram(f'Camgrabber has rendered a new daily video: {fullname}.')
    return fullname
        

def get_weather():
    base_url = 'http://api.openweathermap.org/data/2.5/weather?'
    apikey = CONFIG['weather']['openweather_apikey']
    location_id = CONFIG['weather']['openweather_id']
    units = CONFIG['weather']['units']
    complete_url = f'{base_url}appid={apikey}&id={location_id}&units={units}'
    logging.debug(f'Getting weather information from {complete_url}')
    response = requests.get(complete_url)
    x = response.json()
    try:
        if x['cod'] != '404': 
            main = x['main'] 
            current_temperature = main['temp']
            try:
                current_temperature = str(round(float(current_temperature), 1))
            except:
                logging.warn(f'Temperature conversion failed')
            current_pressure = main['pressure'] 
            wind = x['wind']
            windspeed = wind['speed']
            winddirection = wind['deg']
            logging.debug(f'Temp: {current_temperature}, Pressure: {current_pressure}, Wind speed: {windspeed}, Wind direction: {winddirection}')
            
            weatherdata = {}
            weatherdata['tablename'] = CONFIG['general']['tablename']
            weatherdata['timestamp'] = datetime.now
            weatherdata['windspeed'] = windspeed
            weatherdata['winddirection'] = winddirection
            weatherdata['pressure'] = current_pressure
            weatherdata['temperature'] = current_temperature
            save_weather_to_db(weatherdata)

            return current_temperature, current_pressure, windspeed, winddirection
    except:
        logging.warn(f'Failed to retreive weather data. Response was\n{x}')
    pass


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
    logging.debug(f'Inserting weather information into image {imagefile}')
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
    tablename = CONFIG['general']['tablename']
    pass
    

def save_weather_to_db(data):
    logging.info(f'Saving weather information to database')
    database.update_db(CONFIG['general']['database'], data['tablename'], data)
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


def upload_youtube(filename):
    title = CONFIG['youtube']['title'].replace('%date', date.today().strftime('%d.%m.%Y'))
    description = CONFIG['youtube']['description']
    playlist = CONFIG['youtube']['playlist']
    embeddable = CONFIG['youtube']['embeddable']
    privacy = CONFIG['youtube']['privacy']
    logging.info(f'Uploading {filename} to YouTube.')
    logging.debug(f'Playlist: {playlist}, title: {title}, privacy: {privacy}')
    try:
        result = subprocess.call(['youtube-upload', f'--title={title}', f'--description={description}',f'--playlist={playlist}', f'--embeddable={embeddable}', f'--privacy={privacy}', filename])
        try:
            yt_url = re.findall(r'https:\/\/www\.youtube\.com\/watch\?v=.*\b', result)[0]
            logging.debug(f'YT URL: {yt_url}')
            send_telegram(f'Camgrabber has uploaded a new daily video to YouTube: {yt_url}')
        except:
            send_telegram(f'Camgrabber has uploaded a new daily video to YouTube: Retrieving URL failed.')
    except:
        logging.warn(f'Launching youtube-upload subprocess failed!')
    if result:
        logging.debug(f'YT upload result: {result}')
    pass


def send_telegram(message):
    if CONFIG['telegram']['enabled'].lower() == 'true':
        logging.info(f'Sending Telegram message')
        try:
            subprocess.call(['telegram-send', f'{message}'])
        except:
            logging.warn('Sending Telegram message failed.')


if __name__ == '__main__':
    dark = False
    logging.info('Create database file and table if not exist')
    database.create_db_table(CONFIG['general']['database'], CONFIG['general']['tablename'])
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
                send_telegram(f'Recording paused until {start} UTC')
                dark = True
            time.sleep(60)