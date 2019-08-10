# Camgrabber

Saves images from url in a specific intervall and renders a daily time lapse video.

## Requirements

- Python >= 3.6
- ffmepg
- Graphviz

## Installation (Debian/Ubuntu Linux)

`sudo apt-get update && sudo apt-get install -y ffmpeg graphviz python3 python3-venv`
`python3 -m venv venv`
`source venv/bin/activate`
`pip install wheel`
`pip install -r requirements.txt`

## Start

Edit `main.py` and change `URL`, `INTERVAL` and `FILENAME` to your needs.

### Manual start

`source venv/bin/activate`
`python main.py`

### Run permanently as Supervisor service

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
    ```
    (Change `directory`, `command` and `user`)
- Reread and update the configuration: `sudo supervisorctl reread && sudo supervisorctl update`
- Check status: `sudo supervisorctl status`

If any problems occur, http://www.onurguzel.com/supervisord-restarting-and-reloading/ might help.

## License & Copyright

*MIT License*

(c) 2019 Markus Busche, elpatron@mailbox.org

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.