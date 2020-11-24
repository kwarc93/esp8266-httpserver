# -----------------------------------------------------------------------------
# logging
_log_enabled = False

def _log(*args, **kwargs):

    global _log_enabled
    if not _log_enabled:
        return
    header = '[httpserver]'
    print(header, *args, **kwargs, end='\r\n')

# -----------------------------------------------------------------------------
# initialization
_server = None

def init(ssid, pwd, enable_log = False):

    import network
    import socket

    global _log_enabled
    _log_enabled = enable_log

    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    if not sta.isconnected():
        _log('connecting to network...')
        sta.connect(ssid, pwd)
        while not sta.isconnected():
            pass
    _log('connected')
    _log('network config: ', sta.ifconfig())

    global _server
    _server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _server.bind(socket.getaddrinfo('0.0.0.0', 80)[0][-1])
    _server.listen(1)

# -----------------------------------------------------------------------------
# callbacks
_callbacks = {}

def register_callback(method, url, callback):

    global _callbacks

    if method not in _callbacks:
        _callbacks[method] = {}
    _callbacks[method][url] = callback

def register_not_found_callback(callback):
    register_callback('404', '404', callback)

# -----------------------------------------------------------------------------
# utils

def create_header(headers, status):

    colon = ': '
    lend = '\r\n'
    header = 'HTTP/1.1 ' + str(status) + ' OK\r\nServer: ESP8266, Micropython v1.12\r\n'
    
    for name in headers:
        header += name + colon + headers[name] + lend
    header += lend

    return header
    
_hextobyte_cache = None

def url_unquote(string):

    '''unquote('abc%20def') -> b'abc def'.'''
    global _hextobyte_cache

    # Note: strings are encoded as UTF-8. This is only an issue if it contains
    # unescaped non-ASCII characters, which URIs should not.
    if not string:
        return b''

    if isinstance(string, str):
        string = string.encode('utf-8')

    bits = string.split(b'%')
    if len(bits) == 1:
        return string

    res = [bits[0]]
    append = res.append

    # Build cache for hex to char mapping on-the-fly only for codes
    # that are actually used
    if _hextobyte_cache is None:
        _hextobyte_cache = {}

    for item in bits[1:]:
        try:
            code = item[:2]
            char = _hextobyte_cache.get(code)
            if char is None:
                char = _hextobyte_cache[code] = bytes([int(code, 16)])
            append(char)
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)

    return b''.join(res)


# -----------------------------------------------------------------------------
# listening

def listen():

    global _server, _callbacks

    _log('listening...')

    while True:

        try:
            conn, addr = _server.accept()
            _log('client connected, address:', addr)

            conn.settimeout(10.0)

            # get start line
            start = conn.readline()

            # get headers
            body_length = 0
            while True:
                header = conn.readline()
                if header == b'\r\n' or header == b'' or header == None:
                    break
                if b'Content-Length' in header:
                    body_length = int(''.join(list(filter(str.isdigit, header.decode()))))

            #get body (if available)
            body = conn.read(body_length)

            start = start.decode().split(' ')
            if len(start) != 3:
                continue

            (method, url, version) = start

            _log('method: ', method)
            _log('url: ', url)
            _log('version: ', version)
            _log('body: ', body, body_length)

            if method in _callbacks and url in _callbacks[method]:
                _callbacks[method][url](conn, body)
            elif '404' in _callbacks and '404' in _callbacks['404']:
                _callbacks['404']['404'](conn, body)
            else:
                _log('no handler for request')

        except OSError as e:
            _log('OSError:', e)
        finally:
            import gc
            _log('closing connection')
            _log('free heap: ', gc.mem_free())
            conn.close()
        
