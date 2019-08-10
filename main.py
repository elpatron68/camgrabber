import os
import time
import urllib.request
import requests
from datetime import date
from astral import Astral
import ffmpeg

URL = 'https://www.yacht-club-norden.de/MOBOTIX/nu.jpg'
INTERVAL = 15
FILENAME = 'ycn-%i.jpg'
OPENWEATEHR_ID = '2862135'
CITY_NAME = 'Norden'
OPENWEATHER_APIKEY = '6ea7a73741212ae93cb6231852f9f7d0'


def getimages(day, path):
    try:
        os.mkdir(path)
    except OSError:
        print(f'Creation of the directory {path} failed')
    else:
        print(f'Successfully created the directory {path}')
    counter = 0
    while day == date.today():
        f = FILENAME.replace('%i', str(counter).zfill(5))
        fullname = f'{path}/{f}'
        print(f'Saving file: {fullname}')
        print('Loading weather information')
        weatherdata = getweather(OPENWEATEHR_ID)
        print('Inserting weather into image')
        insertdata(fullname, weatherdata)
        urllib.request.urlretrieve(URL, fullname)
        counter += 1
        print(f'Sleeping {INTERVAL} seconds...')
        time.sleep(INTERVAL)


def createtimelapse(day, path):
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


def getweather(location_id):
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


def insertdata(img, data):
    pass


def cleanup(path):
    images = os.listdir(path)

    for item in images:
        if item.endswith('.jpg'):
            try:
                os.remove(os.path.join(path, item))
            except:
                pass
        

def getsun():
    a = Astral()
    a.solar_depression = 'civil'
    city = a[CITY_NAME]
    sun = city.sun(date=date.today, local=True)
    dawn = sun['dawn']
    sunset = sun['sunset']
    return dawn, sunset

if __name__ == '__main__':
    while 1:
        today = date.today()
        path = today.strftime('%Y%m%d')
        getimages(today, path)
        createtimelapse(today, path)
        cleanup(path)