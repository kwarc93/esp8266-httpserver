# -----------------------------------------------------------------------------
# imports

import os
import json
import httpserver
import credentials
import rgbled
import uasyncio as asyncio

from machine import Pin

# -----------------------------------------------------------------------------
# helpers

def read_file(file):

    data = None
    with open(file, 'rb') as f:
        data = f.read()

    return data

async def blink(led, period_ms):

    while True:
        led.on()
        await asyncio.sleep_ms(period_ms)
        led.off()
        await asyncio.sleep_ms(period_ms)

async def rainbow_task():

    hue_offset = 0;

    while True:
        rgbled.strip_rainbow(hue_offset)
        hue_offset += 3
        await asyncio.sleep_ms(1)

# -----------------------------------------------------------------------------
# http handlers

http_handler_task = None

def handle_main_page(conn, body):

    html_file = 'index.html'

    headers = {
        'Content-Type': 'text/html',
        'Content-Length': str(os.stat(html_file)[6]),
        'Connection': 'close'
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(read_file(html_file))
    
def handle_get_rgb(conn, body):

    rgb = rgbled.strip_get()
    json_str = json.dumps({'r':rgb[0],'g':rgb[1],'b':rgb[2]})

    headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(json_str)),
        'Connection': 'close'
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(json_str)

def handle_post_rgb(conn, body):

    global http_handler_task
    if http_handler_task != None:
        http_handler_task.cancel()

    headers = {
        'Connection': 'close',
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

    json_rgb = json.loads(body)
    rgbled.strip_set_smooth(json_rgb['r'], json_rgb['g'], json_rgb['b'])

def handle_rainbow(conn, body):

    global http_handler_task
    if http_handler_task != None:
        http_handler_task.cancel()

    html_file = 'rainbow.html'

    headers = {
        'Content-Type': 'text/html',
        'Content-Length': str(os.stat(html_file)[6]),
        'Connection': 'close'
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(read_file(html_file))

    http_handler_task = asyncio.create_task(rainbow_task())

def handle_favicon(conn, body):

    ico_file = 'favicon.ico'

    headers = {
        'Content-Type': 'image/x-icon',
        'Content-Length': str(os.stat(ico_file)[6]),
        'Connection': 'close'
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(read_file(ico_file))

def handle_not_found(conn, body):

    html_file = '404.html'

    headers = {
        'Content-Type': 'text/html',
        'Content-Length': str(os.stat(html_file)[6]),
        'Connection': 'close'
    }
    conn.write(httpserver.create_header(headers, 404))
    conn.write(read_file(html_file))

def handle_unauthorized(conn, body):

    headers = {
        'WWW-Authenticate': 'Basic realm="general", charset="UTF-8"'
    }
    conn.write(httpserver.create_header(headers, 401))

# -----------------------------------------------------------------------------
# 'main'

async def main():
    print("--- main.py ---")

    # init status LED
    status_led = Pin(4, Pin.OUT)
    status_led.off()

    # set unused IO
    io12 = Pin(12, Pin.OUT)
    io13 = Pin(13, Pin.OUT)
    io12.on()
    io13.on()

    # LED strip with 60 LEDs on pin 14
    rgbled.strip_init(14, 60)

    httpserver.init(credentials.wifi_ssid, credentials.wifi_pwd)
    httpserver.enable_basic_auth(credentials.usr_name, credentials.usr_pwd)

    httpserver.register_callback('GET', '/', handle_main_page)
    httpserver.register_callback('GET', '/favicon.ico', handle_favicon)
    httpserver.register_callback('GET', '/rainbow', handle_rainbow)
    httpserver.register_callback('GET', '/rgb', handle_get_rgb)
    httpserver.register_callback('POST', '/rgb', handle_post_rgb)

    httpserver.register_not_found_callback(handle_not_found)
    httpserver.register_unauthorized_callback(handle_unauthorized)

    blink_task = asyncio.create_task(blink(status_led, 500))

    await httpserver.start()

    # server started
    blink_task.cancel()
    status_led.on()

    while True:
        await asyncio.sleep(1)

# Start the whole thing
asyncio.run(main())
