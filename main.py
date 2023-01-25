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

def read_file_in_chunks(file, chunk_size = 1024):
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        else:
            yield chunk
    
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

shutdown_timer = Timer(-1)
shutdown_timer_remaining_seconds = 0

def shutdown_timer_callback(timer):

    global shutdown_timer_remaining_seconds
    shutdown_timer_remaining_seconds -= 1
    if (shutdown_timer_remaining_seconds == 0):
        asyncio.create_task(shutdown())

async def shutdown():

    global shutdown_timer
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

    while True:
        rgbled.strip_rainbow()
        await asyncio.sleep(0.01)

async def fire_animation():

    while True:
        rgbled.strip_fire()
        await asyncio.sleep(random.randint(10, 50) / 1000)

async def breathe_animation():
    
    color = rgbled.strip_get()
    rgbled.strip_breathe_setup(color[0], color[1], color[2])
    
    while True:
        rgbled.strip_breathe()
        await asyncio.sleep(0.01)


# -----------------------------------------------------------------------------
# http handlers

async def handle_http_file(conn, file, content_type, code = 200):

    headers = {
        'Content-Type': content_type,
        'Content-Length': str(get_file_size(file)),
        'Cache-Control': 'max-age=86400'
    }
    conn.write(httpserver.create_header(headers, code))

    with open(file, 'rb') as f:
        for chunk in read_file_in_chunks(f):
            conn.write(chunk)
            await conn.drain()

@httpserver.handle('GET', '/')
async def handle_main_page(conn, body):

    await handle_http_file(conn, 'page.html', 'text/html')

@httpserver.handle('GET', '/favicon.ico')
async def handle_favicon(conn, body):

    await handle_http_file(conn, 'favicon.ico', 'image/x-icon')

@httpserver.handle('GET', '/script.js')
async def handle_javascript(conn, body):

    await handle_http_file(conn, 'script.js', 'text/javascript')

@httpserver.handle('GET', '/styles.css')
async def handle_css_styles(conn, body):

    await handle_http_file(conn, 'styles.css', 'text/css')

@httpserver.handle('GET', '/rgb')
async def handle_get_rgb(conn, body):

    rgb = rgbled.strip_get()
    json_str = json.dumps({'r':rgb[0],'g':rgb[1],'b':rgb[2]})

    headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(json_str))
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(json_str)

@httpserver.handle('POST', '/rgb')
async def handle_post_rgb(conn, body):

    cancel_animation_task()
    json_rgb = json.loads(body)
    rgbled.strip_set_smooth(json_rgb['r'], json_rgb['g'], json_rgb['b'])

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

@httpserver.handle('POST', '/timer')
async def handle_post_timer(conn, body):

    global shutdown_timer
    global shutdown_timer_remaining_seconds

    shutdown_timer_remaining_seconds = json.loads(body)['seconds']

    if (shutdown_timer_remaining_seconds > 0):
        shutdown_timer.init(period = 1000, mode=Timer.PERIODIC, callback = shutdown_timer_callback)
    else:
        shutdown_timer.deinit()

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

@httpserver.handle('GET', '/timer')
async def handle_get_timer(conn, body):

    global shutdown_timer_remaining_seconds
    json_str = json.dumps({'seconds':shutdown_timer_remaining_seconds})

    headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(json_str))
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(json_str)

@httpserver.handle('POST', '/rainbow')
async def handle_rainbow(conn, body):

    run_animation_task(rainbow_animation)

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

@httpserver.handle('POST', '/fire')
async def handle_fire(conn, body):

    run_animation_task(fire_animation)

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

@httpserver.handle('POST', '/breathe')
async def handle_breathe(conn, body):
        
    run_animation_task(breathe_animation)

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

@httpserver.not_found()
async def handle_not_found(conn, body):
    
    await handle_http_file(conn, '404.html', 'text/html', 404)
    
# -----------------------------------------------------------------------------
# 'main'

async def main():
    print('--- main.py ---')

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

    blink_task = asyncio.create_task(blink(status_led, 0.5))

    http_srv_task = await httpserver.start()

    # server started
    blink_task.cancel()
    status_led.on()

    while True:
        await asyncio.sleep(1)

# Start the whole thing
asyncio.run(main())
