import math
import random
import pwm_lightness
from machine import Pin, PWM
from neopixel import NeoPixel

# -----------------------------------------------------------------------------
# CIE 1931 LUTs

_cie_lut_10b = None
_cie_lut_8b = None

# -----------------------------------------------------------------------------
# color transformations

def _hsv2rgb(h, s, v):
    # This version below is ~3x slower but ~3x shorter ;)
    # k = lambda n: math.fmod((n + h / 60.0), 6)
    # f = lambda n: v - v * s * max(0, min(min(k(n), 4 - k(n)), 1))
    # return round(f(5) * 255), round(f(3) * 255), round(f(1) * 255)

    c = v * s
    hp = h / 60.0
    x = c * (1 - math.fabs(math.fmod(hp, 2) - 1))
    m = v - c
    x = round(255 * (x + m))
    c = round(255 * (c + m))
    m = round(255 * m)
    hp = int(hp) % 6
    if hp == 0:
        return c, x, m
    elif hp == 1:
        return x, c, m
    elif hp == 2:
        return m, c, x
    elif hp == 3:
        return m, x, c
    elif hp == 4:
        return x, m, c
    elif hp == 5:
        return c, m, x

def _rgb2hsv(r, g, b):

    r /= 255
    g /= 255
    b /= 255

    maxc = max(r, g, b)
    minc = min(r, g, b)
    v = maxc

    if minc == maxc:
        return 0.0, 0.0, v

    s = (maxc-minc) / maxc
    rc = (maxc-r) / (maxc-minc)
    gc = (maxc-g) / (maxc-minc)
    bc = (maxc-b) / (maxc-minc)
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0

    return h * 360.0, s, v

_rgb_next_color = bytearray(3)
_rgb_curr_color = bytearray(3)

def get_color():

    return _rgb_curr_color

def get_next_color():

    return _rgb_next_color

def set_next_color(r, g, b):

    global _rgb_next_color
    _rgb_next_color = bytearray((r, g, b))

# -----------------------------------------------------------------------------
# RGB PWM LED

_rpwm = None
_gpwm = None
_bpwm = None

def init(rpin, gpin, bpin):

    global _rpwm, _gpwm, _bpwm, _cie_lut_10b

    _cie_lut_10b = pwm_lightness.get_pwm_table(1023, 255)

    _rpwm = PWM(Pin(rpin), freq=500, duty=0)
    _gpwm = PWM(Pin(gpin), freq=500, duty=0)
    _bpwm = PWM(Pin(bpin), freq=500, duty=0)

def set(r, g, b):

    global _rgb_curr_color

    cie = _cie_lut_10b
    _rpwm.duty(cie[r])
    _gpwm.duty(cie[g])
    _bpwm.duty(cie[b])
    _rgb_curr_color = bytearray((r, g, b))

# -----------------------------------------------------------------------------
# RGB LED strip

_led_strip_drv = None

def strip_init(pin, leds):

    global _led_strip_drv, _cie_lut_8b

    _cie_lut_8b = pwm_lightness.get_pwm_table(255, 255)

    _led_strip_drv = NeoPixel(Pin(pin, Pin.OUT), leds)
    _led_strip_drv.fill((0, 0, 0))
    _led_strip_drv.write()

def strip_set(r, g, b):

    drv = _led_strip_drv
    cie = _cie_lut_8b

    global _rgb_curr_color

    drv.fill((cie[r], cie[g], cie[b]))
    drv.write()
    _rgb_curr_color = bytearray((r, g, b))

def strip_set_smooth(r, g, b):

    drv = _led_strip_drv
    cie = _cie_lut_8b

    global _rgb_curr_color
    prev_color = _rgb_curr_color
    new_color = bytearray((r, g, b))

    if new_color == prev_color:
        strip_set(r, g, b)
        return

    diff = (new_color[0] - prev_color[0], new_color[1] - prev_color[1], new_color[2] - prev_color[2])
    length = math.sqrt(diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2)

    cosb_sina = diff[0] / length
    cosb_cosa = diff[1] / length
    sinb = diff[2] / length

    steps = range(1, int(round(length)) + 1)
    for step in steps:
        new_color[0] = int(prev_color[0] + round(step * cosb_sina))
        new_color[1] = int(prev_color[1] + round(step * cosb_cosa))
        new_color[2] = int(prev_color[2] + round(step * sinb))
        drv.fill((cie[new_color[0]], cie[new_color[1]], cie[new_color[2]]))
        drv.write()
    _rgb_curr_color = new_color

# -----------------------------------------------------------------------------
# RGB LED strip effects

_raibow_hue = 0

def strip_rainbow():

    global _raibow_hue
    drv = _led_strip_drv
    cie = _cie_lut_8b
    leds = range(drv.n)

    hue_step = 360 / drv.n

    for led in leds:
        led_hue = (_raibow_hue + hue_step * led) % 360
        drv[led] = tuple(cie[x] for x in _hsv2rgb(led_hue, 1.0, 1.0))
    drv.write()

    _raibow_hue += 1

def strip_fire():

    drv = _led_strip_drv
    cie = _cie_lut_8b
    leds = range(drv.n)

    # color of fire
    rgb = (217, 109, 0)

    for led in leds:
        flicker = random.randint(0, 50)
        drv[led] = tuple([cie[x - flicker] if x-flicker >= 0 else 0 for x in rgb])
    drv.write()

_breathe_max_value = None
_breathe_min_value = None
_breathe_step = None
_breathe_hsv = None

def strip_breathe_setup(r, g, b, intensity = 0.8):

    global _rgb_curr_color
    global _breathe_max_value, _breathe_min_value, _breathe_step, _breathe_hsv, _breathe_value

    _rgb_curr_color = bytearray((r, g, b))
    _breathe_hsv = _rgb2hsv(r, g, b)
    _breathe_max_value = _breathe_hsv[2]
    _breathe_min_value = (1 - intensity) * _breathe_max_value
    _breathe_value = _breathe_min_value
    _breathe_step = 0.005 * _breathe_max_value

def strip_breathe():

    global _breathe_step
    global _breathe_hsv
    global _breathe_value

    drv = _led_strip_drv

    if (_breathe_value <= _breathe_min_value):
        _breathe_step  = 0.005 * _breathe_max_value
    elif (_breathe_value >= _breathe_max_value - _breathe_step):
        _breathe_step = -0.02 * _breathe_min_value

    _breathe_value += _breathe_step

    # no CIE LUT to minimize flicker at low light intensity
    drv.fill(_hsv2rgb(_breathe_hsv[0], _breathe_hsv[1], _breathe_value))
    drv.write()