# Camgrabber

Saves images from url in a specific intervall and renders a daily time lapse video.

## Requirements

- Python3
- ffmepg
- Graphviz

## Installation

`sudo apt-get update && sudo apt-get install -y ffmpeg graphviz python3 python3-venv`
`python3 -m venv venv`
`source venv/bin/activate`
`pip install wheel`
`pip install -r requirements.txt`

## Start

Edit `main.py` and change `URL`, `INTERVAL` and `FILENAME` to your needs.

## Manual start

`source venv/bin/activate`
`python main.py`

## Run permanently as Supervisor service

- Install _Supervisor_: `sudo apt-get install -y supervisor`
- Edit the configuration file `sudo nano /etc/supervisor/conf.d/camgrabber.conf`:
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
