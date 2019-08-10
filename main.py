import os
import time
import urllib.request
from datetime import date
import ffmpeg

URL = 'https://www.yacht-club-norden.de/MOBOTIX/nu.jpg'
INTERVAL = 15
FILENAME = "ycn-%i.png"


def getimages(t):
    path = t.strftime('%Y%m%d')
    try:
        os.mkdir(path)
    except OSError:
        print(f"Creation of the directory {path} failed")
    else:
        print(f"Successfully created the directory {path}")
    counter = 0
    while t == date.today():
        f = FILENAME.replace('%i', str(counter).zfill(5))
        fullname = f'{path}/{f}'
        print(f'Saving file: {fullname}')
        urllib.request.urlretrieve(URL, fullname)
        counter += 1
        print(f'Sleeping {INTERVAL} seconds...')
        time.sleep(INTERVAL)


def createtimelapse():
    output_options = {
        'crf': 20,
        'preset': 'slower',
        'movflags': 'faststart',
        'pix_fmt': 'yuv420p'
    }
    (
        ffmpeg
        .input('/path/to/jpegs/*.jpg', pattern_type='glob', framerate=25)
        .filter_('deflicker', mode='pm', size=10)
        .filter_('scale', size='hd1080', force_original_aspect_ratio='increase')
        .output(
            'movie.mp4', 
            **output_options
        )
        .view(filename='filter_graph')
        .run()
    )

if __name__ == '__main__':
    while 1:
        today = date.today()
        getimages(today)
        # createtimelapse()