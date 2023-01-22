# -----------------------------------------------------------------------------
# imports

import os
import json
import random
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

# -----------------------------------------------------------------------------
# tasks

async def blink(led, period_s):

    while True:
        led.on()
        await asyncio.sleep(period_s)
        led.off()
        await asyncio.sleep(period_s)

animation_task = None

def cancel_animation_task():
    
    global animation_task
    if animation_task is not None:
        animation_task.cancel()

def run_animation_task(task):

    global animation_task
    if animation_task is not None:
        animation_task.cancel()
    animation_task = asyncio.create_task(task())

async def rainbow_animation():

    hue_offset = 0

    while True:
        rgbled.strip_rainbow(hue_offset)
        hue_offset += 2
        await asyncio.sleep(0.01)

async def fire_animation():

    while True:
        rgbled.strip_fire()
        await asyncio.sleep(random.randint(10, 50) / 1000)

async def breathe_animation():
    # TODO
    return


# -----------------------------------------------------------------------------
# http handlers

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

    cancel_animation_task()
    json_rgb = json.loads(body)
    rgbled.strip_set_smooth(json_rgb['r'], json_rgb['g'], json_rgb['b'])

    headers = {
        'Connection': 'close',
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))


def handle_rainbow(conn, body):

    run_animation_task(rainbow_animation)

    headers = {
        'Connection': 'close',
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

def handle_fire(conn, body):

    run_animation_task(fire_animation)

    headers = {
        'Connection': 'close',
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

def handle_breathe(conn, body):
        
    run_animation_task(breathe_animation)

    headers = {
        'Connection': 'close',
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

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
    httpserver.register_callback('POST', '/rainbow', handle_rainbow)
    httpserver.register_callback('POST', '/fire', handle_fire)
    httpserver.register_callback('POST', '/breathe', handle_breathe)
    httpserver.register_callback('GET', '/rgb', handle_get_rgb)
    httpserver.register_callback('POST', '/rgb', handle_post_rgb)

    httpserver.register_not_found_callback(handle_not_found)
    httpserver.register_unauthorized_callback(handle_unauthorized)

    blink_task = asyncio.create_task(blink(status_led, 0.5))

    http_srv_task = await httpserver.start()

    # server started
    blink_task.cancel()
    status_led.on()

    while True:
        await asyncio.sleep(1)

# Start the whole thing
asyncio.run(main())
