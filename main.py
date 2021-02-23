# -----------------------------------------------------------------------------
# imports

import os
import json
import httpserver
import credentials
import rgbled

from machine import Pin

# -----------------------------------------------------------------------------
# helpers

def read_file(file):

    data = None
    with open(file, 'rb') as f:
        data = f.read()

    return data

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
    json_str = json.dumps({'r':rgb[1],'g':rgb[0],'b':rgb[2]})

    headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(json_str)),
        'Connection': 'close'
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(json_str)

def handle_post_rgb(conn, body):

    headers = {
        'Connection': 'close',
        'ETag': '\"' + str(body) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

    json_rgb = json.loads(body)
    rgbled.strip_set_smooth(json_rgb['r'], json_rgb['g'], json_rgb['b'])

def handle_rainbow(conn, body):

    html_file = 'rainbow.html'

    headers = {
        'Content-Type': 'text/html',
        'Content-Length': str(os.stat(html_file)[6]),
        'Connection': 'close'
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(read_file(html_file))

    rgbled.strip_rainbow()

def handle_favicon(conn, body):

    headers = { 'Connection': 'close' }
    conn.write(httpserver.create_header(headers, 404))

def handle_not_found(conn, body):

    html_file = '404.html'

    headers = {
        'Content-Type': 'text/html',
        'Content-Length': str(os.stat(html_file)[6]),
        'Connection': 'close'
    }
    conn.write(httpserver.create_header(headers, 404))
    conn.write(read_file(html_file))

# -----------------------------------------------------------------------------
# 'main'

print("--- main.py ---")

green_led = Pin(4, Pin.OUT)
green_led.off()

io12 = Pin(12, Pin.OUT)
io13 = Pin(13, Pin.OUT)
io12.on()
io13.on()

rgbled.strip_init(14, 60)

httpserver.init(credentials.ssid, credentials.pwd, True)

httpserver.register_callback('GET', '/', handle_main_page)
httpserver.register_callback('GET', '/favicon.ico', handle_favicon)
httpserver.register_callback('GET', '/rainbow', handle_rainbow)
httpserver.register_callback('GET', '/rgb', handle_get_rgb)
httpserver.register_callback('POST', '/rgb', handle_post_rgb)
httpserver.register_not_found_callback(handle_not_found)

green_led.on()

httpserver.listen()
