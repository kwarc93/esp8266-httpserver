import math
import time
import pwm_lightness
from machine import Pin, PWM
from neopixel import NeoPixel

# -----------------------------------------------------------------------------
# CIE 1931 LUTs

cie_lut_10b = pwm_lightness.get_pwm_table(1023, 255)
cie_lut_8b = pwm_lightness.get_pwm_table(255, 255)

# -----------------------------------------------------------------------------
# RGB PWM LED

_rpwm = None
_gpwm = None
_bpwm = None

def init(rpin, gpin, bpin):

    global _rpwm, _gpwm, _bpwm
    
    _rpwm = PWM(Pin(rpin), freq=500, duty=0)
    _gpwm = PWM(Pin(gpin), freq=500, duty=0)
    _bpwm = PWM(Pin(bpin), freq=500, duty=0)

def set(r, g, b):

    cie = cie_lut_10b
    _rpwm.duty(cie[r])
    _gpwm.duty(cie[g])
    _bpwm.duty(cie[b])

# -----------------------------------------------------------------------------
# RGB LED strip

_led_strip_drv = None
_led_strip_color = bytearray(3)

def strip_init(pin, leds):

    global _led_strip_drv

    _led_strip_drv = NeoPixel(Pin(pin, Pin.OUT), leds)

def strip_set(r, g, b):

    drv = _led_strip_drv
    cie = cie_lut_8b
    leds = range(drv.n)

    for led in leds:
        drv[led] = (cie[r], cie[g], cie[b])
    drv.write()

def _hsv2rgb(h, s, v):

    if h > 360.0 or h < 0.0 or s > 1.0 or s < 0.0 or v > 1.0 or v < 0.0:
        return None
    
    k = lambda n: math.fmod((n + h / 60.0), 6)
    f = lambda n: v - v * s * max(0, min(min(k(n), 4 - k(n)), 1))

    return (int(f(5) * 255), int(f(3) * 255), int(f(1) * 255))

def strip_rainbow():

    drv = _led_strip_drv
    cie = cie_lut_8b
    leds = range(drv.n)
    
    hue_step = 360 / drv.n
    
    for led in leds:
        avg_hue = hue_step * (2 * led + 1) / 2
        (r, g, b) = _hsv2rgb(avg_hue, 1.0, 1.0)
        drv[led] = (cie[r], cie[g], cie[b])
    drv.write()

def strip_set_smooth(r, g, b):

    drv = _led_strip_drv
    cie = cie_lut_8b
    leds = range(drv.n)

    global _led_strip_color
    prev_color = _led_strip_color
    new_color = bytearray((g, r, b))

    if new_color == prev_color:
        return

    diff = (new_color[0] - prev_color[0], new_color[1] - prev_color[1], new_color[2] - prev_color[2])
    length = math.sqrt(diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2)
    
    cosb_sina = diff[0] / length
    cosb_cosa = diff[1] / length
    sinb = diff[2] / length

    color = bytearray(3)
    steps = range(0, int(round(length)) + 1)
    for step in steps:
        new_color[0] = int(prev_color[0] + round(step * cosb_sina))
        new_color[1] = int(prev_color[1] + round(step * cosb_cosa))
        new_color[2] = int(prev_color[2] + round(step * sinb))
        color[0] = cie[new_color[0]]
        color[1] = cie[new_color[1]]
        color[2] = cie[new_color[2]]
        for led in leds:
            led *= 3
            drv.buf[led : led + 3] = color
        drv.write()
    _led_strip_color = new_color