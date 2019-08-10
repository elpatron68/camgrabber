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

## Run permanently as supervisor service
