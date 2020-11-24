
print('-----------main.py started------------')

# -----------------------------------------------------------------------------
# imports

import os
import httpserver
import credentials
from machine import Pin, PWM

# -----------------------------------------------------------------------------
# PWM

# Gamma brightness lookup table <https://victornpb.github.io/gamma-table-generator>
# gamma = 2.00 steps = 256 range = 0-1023
gamma_lut = (
     0,   0,   0,   0,   0,   0,   1,   1,   1,   1,   2,   2,   2,   3,   3,   4,
     4,   5,   5,   6,   6,   7,   8,   8,   9,  10,  11,  11,  12,  13,  14,  15,
    16,  17,  18,  19,  20,  22,  23,  24,  25,  26,  28,  29,  30,  32,  33,  35,
    36,  38,  39,  41,  43,  44,  46,  48,  49,  51,  53,  55,  57,  59,  60,  62,
    64,  66,  69,  71,  73,  75,  77,  79,  82,  84,  86,  88,  91,  93,  96,  98,
   101, 103, 106, 108, 111, 114, 116, 119, 122, 125, 127, 130, 133, 136, 139, 142,
   145, 148, 151, 154, 157, 160, 164, 167, 170, 173, 177, 180, 184, 187, 190, 194,
   197, 201, 204, 208, 212, 215, 219, 223, 227, 230, 234, 238, 242, 246, 250, 254,
   258, 262, 266, 270, 274, 278, 282, 287, 291, 295, 300, 304, 308, 313, 317, 322,
   326, 331, 335, 340, 345, 349, 354, 359, 363, 368, 373, 378, 383, 388, 393, 398,
   403, 408, 413, 418, 423, 428, 434, 439, 444, 449, 455, 460, 465, 471, 476, 482,
   487, 493, 498, 504, 510, 515, 521, 527, 533, 538, 544, 550, 556, 562, 568, 574,
   580, 586, 592, 598, 604, 611, 617, 623, 629, 636, 642, 648, 655, 661, 668, 674,
   681, 687, 694, 700, 707, 714, 720, 727, 734, 741, 748, 755, 761, 768, 775, 782,
   789, 796, 804, 811, 818, 825, 832, 839, 847, 854, 861, 869, 876, 884, 891, 899,
   906, 914, 921, 929, 937, 944, 952, 960, 968, 975, 983, 991, 999,1007,1015,1023
)

r_gpio = 12
g_gpio = 13
b_gpio = 14
pwm12 = PWM(Pin(r_gpio), freq=500, duty=0)
pwm13 = PWM(Pin(g_gpio), freq=500, duty=0)
pwm14 = PWM(Pin(b_gpio), freq=500, duty=0)

# -----------------------------------------------------------------------------
# helpers

def set_led(r, g, b):

    global gamma_lut
    pwm12.duty(gamma_lut[r])
    pwm13.duty(gamma_lut[g])
    pwm14.duty(gamma_lut[b])
    print('RGB: ',r,g,b)

def read_file(file):

    data = None
    with open(file, 'rb') as f:
        data = f.read()

    return data

# -----------------------------------------------------------------------------
# http handlers

def handle_main_page(conn, body):

    global httpserver

    html_file = 'index.html'

    headers = {
        'Content-Type': 'text/html',
        'Content-Length': str(os.stat(html_file)[6]),
        'Connection': 'close'
    }
    conn.write(httpserver.create_header(headers, 200))
    conn.write(read_file(html_file))
    

def handle_rgb(conn, body):

    import re
    global httpserver

    rgb_data = httpserver.url_unquote(body)
    regex = re.compile('(\w*rgb_color=rgb)\((\d+),(\d+),(\d+)\)')
    regex = regex.match(rgb_data)

    r = int(regex.group(2))
    g = int(regex.group(3))
    b = int(regex.group(4))
    set_led(r,g,b)

    headers = {
        'Connection': 'close',
        'ETag': '\"' + str(rgb_data) + '\"'
    }
    conn.write(httpserver.create_header(headers, 204))

def handle_favicon(conn, body):

    global httpserver

    headers = { 'Connection': 'close' }
    conn.write(httpserver.create_header(headers, 404))

def handle_not_found(conn, body):

    global httpserver

    html_file = '404.html'

    headers = {
        'Content-Type': 'text/html',
        'Content-Length': str(os.stat(html_file)[6]),
        'Connection': 'close'
    }
    conn.write(httpserver.create_header(headers, 404))
    conn.write(read_file(html_file))

# -----------------------------------------------------------------------------
# http server

httpserver.init(credentials.ssid, credentials.pwd, True)

httpserver.register_callback('GET', '/', handle_main_page)
httpserver.register_callback('GET', '/favicon.ico', handle_favicon)
httpserver.register_callback('POST', '/rgb', handle_rgb)
httpserver.register_not_found_callback(handle_not_found)

httpserver.listen()
