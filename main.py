import os
import time
import urllib.request
import requests
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
OPENWEATEHR_ID = '2862041'
OPENWEATHER_APIKEY = '6ea7a73741212ae93cb6231852f9f7d0'
LAT = '53.624721 N'
LON = '7.153373 E'


def get_images(day, path):
    try:
        os.mkdir(path)
    except OSError:
        print(f'Creation of the directory {path} failed')
    else:
        print(f'Successfully created the directory {path}')
    counter = 0
    weathercount = 0
    sun = get_sun()
    while day == date.today():
        if datetime.utcnow() > datetime.strptime(sun[0], '%Y-%m-%dT%H:%M:%SZ') and datetime.utcnow() < datetime.strptime(sun[1], '%Y-%m-%dT%H:%M:%SZ'):
            f = FILENAME.replace('%i', str(counter).zfill(5))
            fullname = f'{path}/{f}'
            if weathercount == 0:
                print('Loading new weather information')
                weathercount += 1
                weatherdata = get_weather(OPENWEATEHR_ID)
            print(f'Saving file: {fullname}')
            urllib.request.urlretrieve(URL, fullname)
            print('Inserting weather into image')
            insert_weather_data(fullname, weatherdata)
            counter += 1
            print(f'Sleeping {INTERVAL} seconds...')
            time.sleep(INTERVAL)
            if weathercount > 39:
                weathercount=0
        else:
            pass


def create_timelapse(day, path):
    f = FILENAME.replace('%i', day.strftime('%Y%m%d'))
    fn, file_extension = os.path.splitext(f)

    fullname = f'{path}/{fn}'
    print(f'Rendering to {fullname}')
    (
        ffmpeg
        .input(f'{path}/*.jpg', pattern_type='glob', framerate=25)
        .output(f'{fullname}.mp4')
        .run()
    )


def get_weather(location_id):
    base_url = 'http://api.openweathermap.org/data/2.5/weather?'
    # api.openweathermap.org/data/2.5/weather?id=2172797
    complete_url = f'{base_url}appid={OPENWEATHER_APIKEY}&id={location_id}&units=metric'
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
    draw.text((20, 40),f'Wind Speed: {data[2]} m/s', font=font, fill=(255,0,0,255))
    draw.text((20, 60),f'Wind Direction: {data[3]}°', font=font, fill=(255,0,0,255))
    draw.text((20, 80),f'Air Pressure: {data[1]} mbar', font=font, fill=(255,0,0,255))
    draw.text((20, 100),f'Air Temperature: {data[0]}° C', font=font, fill=(255,0,0,255))
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

if __name__ == '__main__':
    while 1:
        today = date.today()
        sun = get_sun()
        path = today.strftime('%Y%m%d')
        if datetime.utcnow() > datetime.strptime(sun[0], '%Y-%m-%dT%H:%M:%SZ') and datetime.utcnow() < datetime.strptime(sun[1], '%Y-%m-%dT%H:%M:%SZ'):
            get_images(today, path)
            create_timelapse(today, path)
            cleanup(path)
        else:
            time.sleep(60)