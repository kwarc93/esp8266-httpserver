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

    if h > 360.0 or h < 0.0 or s > 1.0 or s < 0.0 or v > 1.0 or v < 0.0:
        return None
    
    k = lambda n: math.fmod((n + h / 60.0), 6)
    f = lambda n: v - v * s * max(0, min(min(k(n), 4 - k(n)), 1))

    return int(f(5) * 255), int(f(3) * 255), int(f(1) * 255)

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

    cie = _cie_lut_10b
    _rpwm.duty(cie[r])
    _gpwm.duty(cie[g])
    _bpwm.duty(cie[b])

# -----------------------------------------------------------------------------
# RGB LED strip

_led_strip_drv = None
_led_strip_color = bytearray(3)

def strip_init(pin, leds):

    global _led_strip_drv, _cie_lut_8b

    _cie_lut_8b = pwm_lightness.get_pwm_table(255, 255)

    _led_strip_drv = NeoPixel(Pin(pin, Pin.OUT), leds)
    _led_strip_drv.fill((0, 0, 0))
    _led_strip_drv.write()

def strip_set(r, g, b):

    drv = _led_strip_drv
    cie = _cie_lut_8b

    global _led_strip_color
    _led_strip_color = bytearray((r, g, b))

    drv.fill((cie[r], cie[g], cie[b]))
    drv.write()

def strip_get():
    return _led_strip_color

def strip_set_smooth(r, g, b):

    drv = _led_strip_drv
    cie = _cie_lut_8b

    global _led_strip_color
    prev_color = _led_strip_color
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
    _led_strip_color = new_color

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
        # avg_hue = (hue_offset + hue_step * (2 * led + 1) / 2) % 360
        avg_hue = (_raibow_hue + hue_step * led) % 360
        (r, g, b) = _hsv2rgb(avg_hue, 1.0, 1.0)
        drv[led] = (cie[r], cie[g], cie[b])
    drv.write()

    _raibow_hue += 2
    
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

def strip_breathe_setup(r, g, b, intensity = 0.5):

    global _breathe_max_value
    global _breathe_min_value
    global _breathe_step
    global _breathe_hsv
    global _breathe_value

    _breathe_hsv = _rgb2hsv(r, g, b)
    _breathe_max_value = int(_breathe_hsv[2] * 500)
    _breathe_min_value = int((1 - intensity) * _breathe_max_value)
    _breathe_value = _breathe_max_value
    _breathe_step = -1

def strip_breathe():

    global _breathe_step
    global _breathe_hsv
    global _breathe_value

    drv = _led_strip_drv
    cie = _cie_lut_8b

    _breathe_value += _breathe_step

    if (_breathe_value <= _breathe_min_value):
        _breathe_step  = 2
    elif (_breathe_value >= _breathe_max_value):
        _breathe_step = -1

    (r, g, b) = _hsv2rgb(_breathe_hsv[0], _breathe_hsv[1], _breathe_value / 500)

    drv.fill((cie[r], cie[g], cie[b]))
    drv.write()