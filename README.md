# Camgrabber

Saves images from an url in a specific interval and renders a daily time lapse video from the images. Weather data will be included into each image (and of course the video).

## Requirements

- Python >= 3.6
- ffmepg
- Graphviz

## Installation (Debian/Ubuntu Linux)

- Install some packages
  `sudo apt-get update && sudo apt-get install -y ffmpeg graphviz python3 python3-venv`
- Clone this repository
  `git clone https://github.com/elpatron68/camgrabber.git`
- Create Python Virtual Environment
  `cd camgrabber && python3 -m venv venv`
- Activate the Virtual Environment
  `source venv/bin/activate`
- Install Python requirements
  `pip install wheel`
  `pip install -r requirements.txt`
- Download the needed font from http://www.911fonts.com/font/download_MicrosoftSansSerifRegular_6457.htm and save it as `MicrosoftSansSerifRegular.ttf` in the same directory as `main.py`

## Start

To obtain weather data, you need to have a (free) API key from https://openweathermap.org/api. Create an account, log in and generate a key: https://home.openweathermap.org/api_keys.

Before the first start: Edit `main.py` and change values in the settings section to your needs.

_Example settings_

```
"""
Change setting below!
"""
URL = 'https://www.yacht-club-norden.de/MOBOTIX/nu.jpg'
INTERVAL = 15
# Use %i for an incrementing number
FILENAME = 'ycn-%i.jpg'
# Search your place on https://openweathermap.org and use the number in the URL (eg. https://openweathermap.org/city/2862041 -> 2862041)
OPENWEATEHR_ID = '2862041'
OPENWEATHER_APIKEY = '<insert your openweathermap api key here>'
# You can get your location from https://maps.google.com. See URL after selecting a location or right click and select "What´s here?"
LAT = '53.624721 N'
LON = '7.153373 E'
```

### Manual start

`source venv/bin/activate`
`python main.py`

### Run permanently with Supervisor

- Install _Supervisor_: `sudo apt-get install -y supervisor`
- Edit the configuration file:
    `sudo nano /etc/supervisor/conf.d/camgrabber.conf`
    ```
    [program:camgrabber]
    directory=/home/ubuntu/camgrabber
    command=/home/ubuntu/camgrabber/venv/bin/python main.py
    autostart=true
    autorestart=true
    startretries=10
    startsecs=10
    stopwaitsecs=5
    user=ubuntu
    stdout_logfile=/home/ubuntu/camgrabber/log/camgrabber.stdout.log
    stdout_logfile_maxbytes=100000
    stderr_logfile=/home/ubuntu/camgrabber/log/camgrabber.stderr.log
    stderr_logfile_maxbytes=100000
    ```
    (Change `directory`, `command` and `user`)
- Reread and update the configuration: `sudo supervisorctl reread && sudo supervisorctl update`
- Check status: `sudo supervisorctl status`

If any problems occur, http://www.onurguzel.com/supervisord-restarting-and-reloading/ might help.

## License & Copyright

This Script is licensed under the *MIT License*

(c) 2019 Markus Busche, elpatron@mailbox.org

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.