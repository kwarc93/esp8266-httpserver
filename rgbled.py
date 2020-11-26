import math
import time
from machine import Pin, PWM
from neopixel import NeoPixel

# -----------------------------------------------------------------------------
# gamma LUTs

# Gamma brightness lookup table <https://victornpb.github.io/gamma-table-generator>
# gamma = 2.00 steps = 256 range = 0-1023
gamma_lut_10b = (
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

# Gamma brightness lookup table <https://victornpb.github.io/gamma-table-generator>
# gamma = 2.00 steps = 256 range = 0-255
gamma_lut_8b = (
     0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,
     1,   1,   1,   1,   2,   2,   2,   2,   2,   2,   3,   3,   3,   3,   4,   4,
     4,   4,   5,   5,   5,   5,   6,   6,   6,   7,   7,   7,   8,   8,   8,   9,
     9,   9,  10,  10,  11,  11,  11,  12,  12,  13,  13,  14,  14,  15,  15,  16,
    16,  17,  17,  18,  18,  19,  19,  20,  20,  21,  21,  22,  23,  23,  24,  24,
    25,  26,  26,  27,  28,  28,  29,  30,  30,  31,  32,  32,  33,  34,  35,  35,
    36,  37,  38,  38,  39,  40,  41,  42,  42,  43,  44,  45,  46,  47,  47,  48,
    49,  50,  51,  52,  53,  54,  55,  56,  56,  57,  58,  59,  60,  61,  62,  63,
    64,  65,  66,  67,  68,  69,  70,  71,  73,  74,  75,  76,  77,  78,  79,  80,
    81,  82,  84,  85,  86,  87,  88,  89,  91,  92,  93,  94,  95,  97,  98,  99,
   100, 102, 103, 104, 105, 107, 108, 109, 111, 112, 113, 115, 116, 117, 119, 120,
   121, 123, 124, 126, 127, 128, 130, 131, 133, 134, 136, 137, 139, 140, 142, 143,
   145, 146, 148, 149, 151, 152, 154, 155, 157, 158, 160, 162, 163, 165, 166, 168,
   170, 171, 173, 175, 176, 178, 180, 181, 183, 185, 186, 188, 190, 192, 193, 195,
   197, 199, 200, 202, 204, 206, 207, 209, 211, 213, 215, 217, 218, 220, 222, 224,
   226, 228, 230, 232, 233, 235, 237, 239, 241, 243, 245, 247, 249, 251, 253, 255,
  )

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

    gamma = gamma_lut_10b
    _rpwm.duty(gamma[r])
    _gpwm.duty(gamma[g])
    _bpwm.duty(gamma[b])

# -----------------------------------------------------------------------------
# RGB LED strip

_led_strip_drv = None

def strip_init(pin, leds):

    global _led_strip_drv

    _led_strip_drv = NeoPixel(Pin(pin, Pin.OUT), leds)

def strip_set(r, g, b):

    drv = _led_strip_drv
    gamma = gamma_lut_8b
    leds = range(drv.n)

    for led in leds:
        drv[led] = (gamma[r], gamma[g], gamma[b])
    drv.write()

def _hsv2rgb(h, s, v):

    if h > 360.0 or h < 0.0 or s > 1.0 or s < 0.0 or v > 1.0 or v < 0.0:
        return None
    
    k = lambda n: math.fmod((n + h / 60.0), 6)
    f = lambda n: v - v * s * max(0, min(min(k(n), 4 - k(n)), 1))

    return (int(f(5) * 255), int(f(3) * 255), int(f(1) * 255))

def strip_rainbow():

    drv = _led_strip_drv
    gamma = gamma_lut_8b
    hue_step = 360 / drv.n
    leds = range(drv.n)
    
    for led in leds:
        avg_hue = hue_step * (2 * led + 1) / 2
        (r, g, b) = _hsv2rgb(avg_hue, 1.0, 1.0)
        drv[led] = (gamma[r], gamma[g], gamma[b])
    drv.write()

def strip_breathe():

    drv = _led_strip_drv
    gamma = gamma_lut_8b
    steps = range(0, 128)
    leds = range(0, drv.n * 3, 3)
    color = bytearray(3)

    for step in steps:
        for led in leds:
            color[1] = gamma[step]
            color[0] = gamma[step]
            color[2] = gamma[step]
            drv.buf[led : led + 3] = color
        drv.write()

    steps = reversed(steps)
    for step in steps:
        for led in leds:
            color[1] = gamma[step]
            color[0] = gamma[step]
            color[2] = gamma[step]
            drv.buf[led : led + 3] = color
        drv.write()