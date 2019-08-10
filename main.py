import os
import time
import urllib.request
from datetime import date
import ffmpeg

URL = 'https://www.yacht-club-norden.de/MOBOTIX/nu.jpg'
INTERVAL = 15
FILENAME = "ycn-%i.jpg"


def getimages(day, path):
    try:
        os.mkdir(path)
    except OSError:
        print(f"Creation of the directory {path} failed")
    else:
        print(f"Successfully created the directory {path}")
    counter = 0
    while day == date.today():
        f = FILENAME.replace('%i', str(counter).zfill(5))
        fullname = f'{path}/{f}'
        print(f'Saving file: {fullname}')
        urllib.request.urlretrieve(URL, fullname)
        counter += 1
        print(f'Sleeping {INTERVAL} seconds...')
        time.sleep(INTERVAL)


def createtimelapse(day, path):
    f = FILENAME.replace("%i", day.strftime("%Y%m%d"))
    fn, file_extension = os.path.splitext(f)

    fullname = f'{path}/{fn}'
    print(f'Rendering to {fullname}')
    (
        ffmpeg
        .input(f'{path}/*.jpg', pattern_type='glob', framerate=25)
        .output(f'{fullname}.mp4')
        .run()
    )


def cleanup(path):
    images = os.listdir(path)

    for item in images:
        if item.endswith(".jpg"):
            try:
                os.remove(os.path.join(path, item))
            except:
                pass
        

if __name__ == '__main__':
    while 1:
        today = date.today()
        path = today.strftime('%Y%m%d')
        getimages(today, path)
        createtimelapse(today, path)
        cleanup(path)