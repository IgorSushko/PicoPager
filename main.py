import time
from machine import I2C, Pin
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd
from phew import connect_to_wifi, server
from wifiCredentials import wifiDetails

button = Pin(15, Pin.IN, Pin.PULL_UP)

# Define I2C constants
I2C_ADDR     = 0x27  # Default I2C address for LCD backpack (some are 0x3F)
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

# Initialize I2C on I2C1 (Pins 6 and 7) with 400kHz frequency
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

# Initialize the LCD
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

networkDetails = wifiDetails()
st = None

while st is None:
    # Try to connect with retries
    st = connect_to_wifi(networkDetails.getSSID(), networkDetails.getPassword())
    
    if st is None:
        lcd.clear()
        lcd.putstr("Connection failed")
        time.sleep(2)  # Wait before retrying

print(f"Got IP:  {st}")
lcd.clear()
lcd.move_to(0, 0)
lcd.putstr("Assigned IP:")
lcd.move_to(0, 1)
lcd.putstr(st)

page = open("index.html","r")
html = page.read()
page.close()

@server.route("/", methods=["GET"])
def home(request):
    return str(html)

@server.route("/", methods=["POST"])
def save_message(request):
    message = request.form.get("message")
    print("Received message:", message)
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Received message:")
    lcd.move_to(0, 1)
    lcd.putstr(message[:16])
    return str(html)


@server.catchall()
def catchall(request):
    return "Page not found", 404

server.run()
