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
from machine import Timer

# -----------------------------------------------------------------------------
# helpers

def get_file_size(file):
    return os.stat(file)[6]

def read_file(file):

    with open(file, 'rb') as f:
        return f.read()

def handle_http_file(conn, body, file, content_type, code):

    headers = {
        'Content-Type': content_type,
        'Content-Length': str(get_file_size(file)),
        'Cache-Control': 'max-age=86400'
    }
    conn.write(httpserver.create_header(headers, code))
    conn.write(read_file(file))
    
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

turn_off_tim = Timer(-1)

async def turn_off_lights():

    global turn_off_tim
    cancel_animation_task()
    rgbled.strip_set(0, 0, 0)

# -----------------------------------------------------------------------------
# tasks

async def blink(led, period_s):

    while True:
        led.on()
        await asyncio.sleep(period_s)
        led.off()
        await asyncio.sleep(period_s)

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
    pass


# -----------------------------------------------------------------------------
# http handlers

def handle_main_page(conn, body):

    handle_http_file(conn, body, 'page.html', 'text/html', 200)

def handle_favicon(conn, body):

    handle_http_file(conn, body, 'favicon.ico', 'image/x-icon', 200)

def handle_javascript(conn, body):

    handle_http_file(conn, body, 'script.js', 'text/javascript', 200)

def handle_css_styles(conn, body):

    handle_http_file(conn, body, 'styles.css', 'text/css', 200)

def handle_not_found(conn, body):
    
    handle_http_file(conn, body, '404.html', 'text/html', 404)

def handle_get_rgb(conn, body):

    rgb = rgbled.strip_get()
    json_str = json.dumps({'r':rgb[0],'g':rgb[1],'b':rgb[2]})

    headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(json_str))
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(json_str)

def handle_post_rgb(conn, body):

    cancel_animation_task()
    json_rgb = json.loads(body)
    rgbled.strip_set_smooth(json_rgb['r'], json_rgb['g'], json_rgb['b'])

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

def handle_post_timer(conn, body):

    json_timer = json.loads(body)
    timer_value_seconds = json_timer['seconds'];

    global turn_off_tim

    if (timer_value_seconds > 0):
        turn_off_tim.init(period = timer_value_seconds * 1000, mode=Timer.ONE_SHOT, callback = lambda t: asyncio.create_task(turn_off_lights()))
    else:
        turn_off_tim.deinit()

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

def handle_get_timer(conn, body):
    pass

def handle_rainbow(conn, body):

    run_animation_task(rainbow_animation)

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

def handle_fire(conn, body):

    run_animation_task(fire_animation)

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

def handle_breathe(conn, body):
        
    run_animation_task(breathe_animation)

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

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

    httpserver.add_handler('GET', '/', handle_main_page)
    httpserver.add_handler('GET', '/favicon.ico', handle_favicon)
    httpserver.add_handler('GET', '/script.js', handle_javascript)
    httpserver.add_handler('GET', '/styles.css', handle_css_styles)
    httpserver.add_handler('POST', '/rainbow', handle_rainbow)
    httpserver.add_handler('POST', '/fire', handle_fire)
    httpserver.add_handler('POST', '/breathe', handle_breathe)
    httpserver.add_handler('GET', '/rgb', handle_get_rgb)
    httpserver.add_handler('POST', '/rgb', handle_post_rgb)
    httpserver.add_handler('POST', '/timer', handle_post_timer)
    httpserver.add_handler('GET', '/timer', handle_get_timer)

    httpserver.add_not_found_handler(handle_not_found)
    httpserver.add_unauthorized_handler(handle_unauthorized)

    blink_task = asyncio.create_task(blink(status_led, 0.5))

    http_srv_task = await httpserver.start()

    # server started
    blink_task.cancel()
    status_led.on()

    while True:
        await asyncio.sleep(1)

# Start the whole thing
asyncio.run(main())
