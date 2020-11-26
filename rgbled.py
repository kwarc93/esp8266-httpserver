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
    hue_step = 360 / drv.n
    leds = range(drv.n)
    
    for led in leds:
        avg_hue = hue_step * (2 * led + 1) / 2
        (r, g, b) = _hsv2rgb(avg_hue, 1.0, 1.0)
        drv[led] = (cie[r], cie[g], cie[b])
    drv.write()

def strip_breathe():

    drv = _led_strip_drv
    cie = cie_lut_8b
    steps = range(0, 256)
    leds = range(0, drv.n * 3, 3)
    color = bytearray(3)

    for step in steps:
        for led in leds:
            color[1] = cie[step]
            color[0] = cie[step]
            color[2] = cie[step]
            drv.buf[led : led + 3] = color
        drv.write()

    steps = reversed(steps)
    for step in steps:
        for led in leds:
            color[1] = cie[step]
            color[0] = cie[step]
            color[2] = cie[step]
            drv.buf[led : led + 3] = color
        drv.write()