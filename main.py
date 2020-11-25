# -----------------------------------------------------------------------------
# imports

import os
import re
import httpserver
import credentials
import rgbled

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
    

def handle_rgb(conn, body):

    rgb_data = httpserver.url_unquote(body)
    regex = re.compile('(\w*rgb_color=rgb)\((\d+),(\d+),(\d+)\)')
    regex = regex.match(rgb_data)

    r = int(regex.group(2))
    g = int(regex.group(3))
    b = int(regex.group(4))
    # rgbled.set(r,g,b)
    rgbled.strip_set(r, g, b)

    headers = {
        'Connection': 'close',
        'ETag': '\"' + str(rgb_data) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

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

rgbled.strip_init(5, 60)
rgbled.strip_rainbow()

httpserver.init(credentials.ssid, credentials.pwd, True)

httpserver.register_callback('GET', '/', handle_main_page)
httpserver.register_callback('GET', '/favicon.ico', handle_favicon)
httpserver.register_callback('POST', '/rgb', handle_rgb)
httpserver.register_not_found_callback(handle_not_found)

httpserver.listen()
