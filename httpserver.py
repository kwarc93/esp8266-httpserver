# -----------------------------------------------------------------------------
# imports

import gc
import os
import network
import binascii
import uasyncio as asyncio

# -----------------------------------------------------------------------------
# logging

_log_enabled = False

def _log(*args, **kwargs):

    if not _log_enabled:
        return
    header = '[httpserver]'
    print(header, *args, **kwargs, end='\r\n')

# -----------------------------------------------------------------------------
# initialization

_wifi_ssid = None
_wifi_pwd = None

def init(wifi_ssid, wifi_pwd):

    global _wifi_ssid
    global _wifi_pwd

    _wifi_ssid = wifi_ssid
    _wifi_pwd = wifi_pwd

# -----------------------------------------------------------------------------
# authentication

_basic_auth_enabled = False
_usr_name = None
_usr_pwd = None

def enable_basic_auth(usr_name, usr_pwd):

    global _basic_auth_enabled
    global _usr_name, _usr_pwd

    _basic_auth_enabled = True
    _usr_name = usr_name
    _usr_pwd = usr_pwd

def _authenticate(authorization_header):

    header = authorization_header.split(' ')
    if len(header) != 3:
        return False

    (type, credentials) = header[1:3]

    if type != 'Basic':
        return False

    (username, password) = binascii.a2b_base64(credentials).decode().split(':')
    _log('username: ', username)
    _log('password: ', password)

    return username == _usr_name and password == _usr_pwd

# -----------------------------------------------------------------------------
# callbacks

_handlers = {}

def add_handler(method, url, callback):

    global _handlers

    if method not in _handlers:
        _handlers[method] = {}
    _handlers[method][url] = callback

def add_not_found_handler(callback):
    add_handler('404', '404', callback)

def add_unauthorized_handler(callback):
    add_handler('401', '401', callback)

# -----------------------------------------------------------------------------
# utils

def _gc_cleanup():

    gc.collect()
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
    _log('free heap: ', gc.mem_free())

def create_header(headers, status):
 
    header = 'HTTP/1.1 {} OK\r\n Server: {}, Micropython {}\r\n'.format(str(status), getattr(os.uname(), 'machine'), getattr(os.uname(), 'version'))

    for name in headers:
        header += '{}: {}\r\n'.format(name, headers[name])

    # Server does not support persistent connections
    header += 'Connectrion: close\r\n\r\n'

    return header
    
# -----------------------------------------------------------------------------
# listening

async def _conn_close(writer):

    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def _conn_handler(reader, writer):
 
    _gc_cleanup()

    try:
        addr = writer.get_extra_info('peername')
        _log('client connected, address:', addr)

        # if basic authentication is enabled dont accept clients without credentials 
        authorized = not _basic_auth_enabled

        # get start line
        start = await reader.readline()

        # get headers
        body_length = 0
        while True:
            header = await reader.readline()
            if header == b'\r\n' or header == b'' or header == None:
                break
            if b'Content-Length' in header:
                body_length = int(''.join(list(filter(str.isdigit, header.decode()))))
            if b'Authorization' in header:
                authorized = _authenticate(header.decode())

        _gc_cleanup()

        # get body (if available)
        body = await reader.readexactly(body_length)

        start = start.decode().split(' ')
        if len(start) != 3:
            await _conn_close(writer)
            return

        (method, url, version) = start

        _log('method: ', method)
        _log('url: ', url)
        _log('version: ', version)
        _log('body: ', body, body_length)

        if not authorized:
            if '401' in _handlers and '401' in _handlers['401']:
                _handlers['401']['401'](writer, body.decode('utf-8'))
            _log('unauthorized')
            await _conn_close(writer)
            return

        _gc_cleanup()

        if method in _handlers and url in _handlers[method]:
            _handlers[method][url](writer, body.decode('utf-8'))
        elif '404' in _handlers and '404' in _handlers['404']:
            _handlers['404']['404'](writer, body.decode('utf-8'))
        else:
            _log('no handler for request')

    except OSError as e:
        _log('OSError:', e)
    finally:
        _log('closing connection')
        await _conn_close(writer)
        _gc_cleanup()

async def start():

    ap = network.WLAN(network.AP_IF)
    ap.active(False)

    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.config(dhcp_hostname = 'wifirgb')
    _log(sta.config('dhcp_hostname'))

    if not sta.isconnected():
        _log('connecting to network...')
        sta.connect(_wifi_ssid, _wifi_pwd)
        while not sta.isconnected():
            await asyncio.sleep(0.1)

    port = 80;
    addr = sta.ifconfig()[0]
    _log('connected, listening on:', addr + ':' + str(port))

    return asyncio.create_task(asyncio.start_server(_conn_handler, addr, port, backlog = 3))
        
