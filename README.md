# Camgrabber

Saves images from an url (eg. static webcam JPG images) in a specific interval and renders a daily time lapse video from the images. Weather data will be included into each image (and of course the video).

Demo video from the webcam of https://yacht-club-norden.de/ 

[![Demo video from the webcam of https://yacht-club-norden.de/](https://img.youtube.com/vi/SDnwLYIla0E/0.jpg)](https://www.youtube.com/watch?v=SDnwLYIla0E)

Click on the image to see the video on YouTube

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
  `pip install wheel && pip install -r requirements.txt`
- Download the needed font from http://www.911fonts.com/font/download_MicrosoftSansSerifRegular_6457.htm and save it as `MicrosoftSansSerifRegular.ttf` in the same directory as `main.py`

## Start recording

### Preparation

- To obtain weather data, you need to have a (free) API key from https://openweathermap.org/api. Create an account, log in and generate a key: https://home.openweathermap.org/api_keys.
- Find the ID of the place for which you want to retreive weather data: Open https://openweathermap.org, search and click on your place. Use the right part of the URL as you ID. Eg. https://openweathermap.org/city/2862041 -> `openweather_id = 2862041`.
- Find the geographic coordinates of the place of the webcam (from Google maps or place information on openweathermap.org), They are needed to calculate sun dawn and -down.

### Before the first start:

- Make a copy of `camgrabber.default.ini`:
  `cp camgrabber.default.ini camgrabber.ini`
- Edit `camgrabber.ini` and change values to your needs (eg `nano camgrabber.ini`)
- Create a log directory (`mkdir -p log`) - only needed if you run the script with Supervisor

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
    stderr_logfile=/home/ubuntu/camgrabber/log/camgrabber.stderr.log
    stderr_logfile_maxbytes=100000
    ```
    (Change `directory`, `command`, `stderr_logfile` and `user`)
- Reread and update the configuration: `sudo supervisorctl reread && sudo supervisorctl update`
- Check the status: `sudo supervisorctl status`

If any problems occur, http://www.onurguzel.com/supervisord-restarting-and-reloading/ might help.

## Thanks

Thanks to Alessio Atzeni for his free weather icons from https://www.iconfinder.com/iconsets/meteocons

## License & Copyright

This Script is licensed under the *MIT License*

(c) 2019 Markus Busche, elpatron@mailbox.org

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.