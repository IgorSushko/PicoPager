import time
from machine import I2C, Pin
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd


def init1602():
    # Define I2C constants
    I2C_ADDR     = 0x27  # Default I2C address for LCD backpack (some are 0x3F)
    I2C_NUM_ROWS = 2
    I2C_NUM_COLS = 16

    # Initialize I2C on I2C1 (Pins 6 and 7) with 400kHz frequency
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

    # Initialize the LCD
    lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
    
def showOn1602():
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Received from WEB:")
    lcd.move_to(0, 1)
    lcd.putstr(message[:16])