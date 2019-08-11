import os
import time
import urllib.request
import requests
import ntpath
import logging
from datetime import date, timedelta, datetime
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import ffmpeg
from skyfield import api
from skyfield import almanac

"""
Change setting below!
"""
URL = 'https://www.yacht-club-norden.de/MOBOTIX/nu.jpg'
INTERVAL = 15
FILENAME = 'ycn-%i.jpg'
DESTINATION_PATH = 'videos'
OPENWEATEHR_ID = '2862041'
OPENWEATHER_APIKEY = '6ea7a73741212ae93cb6231852f9f7d0'
LAT = '53.624721 N'
LON = '7.153373 E'
START_BEFORE_SUNDAWN = 1
END_AFTER_SUNDOWN = 1


def get_images(day, path):
    try:
        os.mkdir(path)
    except OSError:
        print(f'Creation of the directory {path} failed')
    else:
        print(f'Successfully created the directory {path}')
    counter = 0
    indexfile = f'{path}/lastindex.txt'
    if os.path.isfile(indexfile):
        f = open(indexfile)
        counter = int(f.read())
        f.close()
        try:
            os.remove(indexfile)
        except OSError:
            pass

    weathercount = 0
    sun = get_sun()
    sundawn = datetime.strptime(sun[0], '%Y-%m-%dT%H:%M:%SZ')
    sundown = datetime.strptime(sun[1], '%Y-%m-%dT%H:%M:%SZ')
    start = sundawn - timedelta(hours=START_BEFORE_SUNDAWN)
    end = sundawn + timedelta(hours=END_AFTER_SUNDOWN)
    while day == date.today():
        now = datetime.utcnow()
        if now > start and now < end:
            f = FILENAME.replace('%i', str(counter).zfill(5))
            fullname = f'{path}/{f}'
            if weathercount == 0:
                print('Loading new weather information')
                weatherdata = get_weather()
            weathercount += 1
            print(f'Saving file: {fullname}')
            urllib.request.urlretrieve(URL, fullname)
            print('Inserting weather into image')
            insert_weather_data(fullname, weatherdata)
            save_lastindex(path, counter)
            counter += 1
            print(f'Sleeping {INTERVAL} seconds...')
            time.sleep(INTERVAL)
            if weathercount > 39:
                weathercount = 0
        else:
            print('Breaking loop')
            break


def create_timelapse(day, source_path, dest_path):
    date = day.strftime('%Y%m%d')
    f = FILENAME.replace('%i', date)
    fn, file_extension = os.path.splitext(f)
    fn = path_leaf(fn)
    fullname = f'{dest_path}/{fn}.mp4'
    try:
        os.mkdir(dest_path)
    except OSError:
        print(f'Creation of the directory {dest_path} failed')
    else:
        print(f'Successfully created the directory {dest_path}')

    print(f'Rendering images from {source_path} to mp4 video file: {fullname}')
    (
        ffmpeg
        .input(f'{source_path}/*{file_extension}', pattern_type='glob', framerate=25)
        .output(f'{fullname}')
        .run()
    )
        

def get_weather():
    base_url = 'http://api.openweathermap.org/data/2.5/weather?'
    # api.openweathermap.org/data/2.5/weather?id=2172797
    complete_url = f'{base_url}appid={OPENWEATHER_APIKEY}&id={OPENWEATEHR_ID}&units=metric'
    response = requests.get(complete_url)
    x = response.json()
    if x['cod'] != '404': 
        main = x['main'] 
        current_temperature = main['temp'] 
        current_pressure = main['pressure'] 
        wind = x['wind']
        windspeed = wind['speed']
        winddirection = wind['deg']
        return current_temperature, current_pressure, windspeed, winddirection


def insert_weather_data(imagefile, data):
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
    images = os.listdir(path)
    for item in images:
        if item.endswith('.jpg'):
            try:
                os.remove(os.path.join(path, item))
            except:
                pass
        

def get_sun():
    location = api.Topos(LAT, LON)
    ts = api.load.timescale()
    e = api.load('de421.bsp')
    today = date.today()
    t0 = ts.utc(today.year, today.month, today.day, 0)
    t1 = ts.utc(today.year, today.month, today.day, 23)
    t, y = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(e, location))
    sun = t.utc_iso()
    sun2 = t
    return sun


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def save_lastindex(path, index):
    f = open(f'{path}/lastindex.txt','w')
    f.write(index)
    f.close
    pass

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s')
    while 1:
        today = date.today()
        sun = get_sun()
        path = today.strftime('%Y%m%d')
        now = datetime.utcnow()
        sundawn = datetime.strptime(sun[0], '%Y-%m-%dT%H:%M:%SZ')
        sundown = datetime.strptime(sun[1], '%Y-%m-%dT%H:%M:%SZ')
        start = sundawn - timedelta(hours=START_BEFORE_SUNDAWN)
        end = sundawn + timedelta(hours=END_AFTER_SUNDOWN)
        if now > start and now < end:
            get_images(today, path)
            for fname in os.listdir(path):
                if fname.endswith('.jpg'):
                    create_timelapse(today, path, DESTINATION_PATH)
                    cleanup(path)
        else:
            print('It´s still dark...')
            time.sleep(60)