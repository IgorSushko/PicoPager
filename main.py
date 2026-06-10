import time
import _thread
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

def printToLCD1602(headerString,footerString):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(headerString)
    lcd.move_to(0, 1)
    lcd.putstr(footerString)
    

networkDetails = wifiDetails()
st = None
approved = False

while st is None:
    # Try to connect with retries
    st = connect_to_wifi(networkDetails.getSSID(), networkDetails.getPassword())
    
    if st is None:
        printToLCD1602("Connection","failed ...")
        time.sleep(2)  # Wait before retrying
        
button_state = Pin(15).value()        

print(f"Got IP:  {st}")
printToLCD1602("Assigned IP:",st)

page = open("index.html","r")
html = page.read()
page.close()

@server.route("/", methods=["GET"])
def home(request):
    return str(html)

@server.route("/", methods=["POST"])
def save_message(request):
    global approved
    message = request.form.get("message")
    print("Received message:", message)
    printToLCD1602("Received message:",message)
    approved = False
    return str(html)

# Add polling endpoint
@server.route("/check_approval", methods=["GET"])
def check_status(request):
    global approved, button_state
    # Continuously check button in background thread or use async approach
    button_state = Pin(15).value()
    
    if button_state == 0:  # Button pressed (LOW signal with PULL_UP)
        approved = True
        printToLCD1602("Message was","Approved")
    
    response_text = "approved" if approved else "pending"
    return str(response_text)


@server.catchall()
def catchall(request):
    return "Page not found", 404

def poll_button():
    global approved
    while True:
        time.sleep(0.5)  # Check every 0.5 seconds
        if Pin(15).value() == 0:
            approved = True
            printToLCD1602("Message was","Approved")

_thread.start_new_thread(poll_button, ())

server.run()
