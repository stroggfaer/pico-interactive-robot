"""Waveshare Pico LCD 2 240x320

https://www.waveshare.com/wiki/Pico-LCD-2

"""

from machine import Pin, SPI
import st7789py as st7789

TFA = 0
BFA = 0
WIDE = 1
TALL = 0
SCROLL = 0  # orientation for scroll.py
FEATHERS = 1  # orientation for feathers.py


def config(rotation=2):
    """
    Configures and returns an instance of the ST7789 display driver.

    Args:
        rotation (int): The rotation of the display. Defaults to 0.

    Returns:
        ST7789: An instance of the ST7789 display driver.
    """
    return st7789.ST7789(
        SPI(1, baudrate=60000000, sck=Pin(10), mosi=Pin(11)),
        240,
        320,
        reset=Pin(12, Pin.OUT),
        cs=Pin(9, Pin.OUT),
        dc=Pin(8, Pin.OUT),
        backlight=Pin(13, Pin.OUT),
        rotation=rotation,
    )