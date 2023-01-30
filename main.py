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

def cancel_animation_task():

    global animation_name, animation_task
    if animation_task is not None:
        animation_task.cancel()
        animation_name = ''

def run_animation_task(name):

    global animation_name, animation_task, animation_map

    cancel_animation_task()
    animation_name = name
    animation_task = asyncio.create_task(animation_map[name]())

shutdown_timer = Timer(-1)
shutdown_timer_remaining_seconds = 0

def shutdown_timer_callback(timer):

    global shutdown_timer_remaining_seconds
    shutdown_timer_remaining_seconds -= 1
    if (shutdown_timer_remaining_seconds == 0):
        asyncio.create_task(shutdown())

color_change_evt = asyncio.Event()

# -----------------------------------------------------------------------------
# tasks

async def shutdown():

    global shutdown_timer
    cancel_animation_task()
    rgbled.strip_set(0, 0, 0)
    shutdown_timer.deinit()

async def blink(led, period_s):

    while True:
        led.on()
        await asyncio.sleep(period_s)
        led.off()
        await asyncio.sleep(period_s)

async def color_animation():

    global color_change_evt

    while True:
        color = rgbled.get_next_color()
        rgbled.strip_set_smooth(color[0], color[1], color[2])
        await color_change_evt.wait()
        color_change_evt.clear()

async def rainbow_animation():

    while True:
        rgbled.strip_rainbow()
        await asyncio.sleep(0.01)

async def fire_animation():

    while True:
        rgbled.strip_fire()
        await asyncio.sleep(random.randint(10, 50) / 1000)

async def breathe_animation():

    global color_change_evt

    color = rgbled.get_color()
    rgbled.strip_breathe_setup(color[0], color[1], color[2])

    while True:
        if (color_change_evt.is_set()):
            color_change_evt.clear()
            color = rgbled.get_next_color()
            rgbled.strip_breathe_setup(color[0], color[1], color[2])

        rgbled.strip_breathe()
        await asyncio.sleep(0.001)

animation_name = 'color'
animation_task = None
animation_map = {
    'color': color_animation,
    'breathe': breathe_animation,
    'fire': fire_animation,
    'rainbow': rainbow_animation
}

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

@httpserver.handle('GET', '/state')
async def handle_get_state(conn, body):

    global shutdown_timer_remaining_seconds, animation

    color = rgbled.get_color()
    timer = shutdown_timer_remaining_seconds
    effect = animation_name
    json_str = json.dumps({'color':{'r':color[0],'g':color[1],'b':color[2]}, 'timer':timer, 'effect':effect})

    headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(json_str))
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(json_str)

@httpserver.handle('POST', '/color')
async def handle_post_color(conn, body):

    global color_change_evt

    json_rgb = json.loads(body)
    rgbled.set_next_color(json_rgb['r'], json_rgb['g'], json_rgb['b'])
    color_change_evt.set()

    headers = {
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

@httpserver.handle('POST', '/effect')
async def handle_post_effect(conn, body):

    effect = json.loads(body)['effect']

    if (effect != animation_name):
        run_animation_task(effect)

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
    run_animation_task('color')

    while True:
        await asyncio.sleep(1)

# Start the whole thing
asyncio.run(main())
