"""PicoPager - web-triggered pager on Raspberry Pi Pico 2W.

Flow:
    browser form --POST /--> HTTP server (phew) --> message shown on 16x2 LCD
    local button (GP15) pressed --> LCD shows "Message was Approved"
    browser polls /check_approval --> shows JS alert once approved

Wiring:
    LCD1602 + PCF8574 backpack:  GP4 = SDA, GP5 = SCL (I2C bus 0, addr 0x27)
    Approve button:              GP15 to GND (internal pull-up, LOW = pressed)
"""

import _thread
import time

from machine import I2C, Pin

from phew import server
from phew import connect_to_wifi

from wifiCredentials import wifiDetails
from vendor.pico_i2c_lcd import I2cLcd

# --- Configuration -----------------------------------------------------------

# Default I2C address for PCF8574 backpack; use 0x3F if 0x27 does not respond.
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
I2C_FREQ = 400_000
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5

# Approve button: input with internal pull-up, LOW when pressed.
BUTTON_PIN = 15
BUTTON_POLL_INTERVAL = 0.2  # seconds

# How long the "Message was Approved" banner stays on the LCD before the
# latest message is shown again.
APPROVAL_BANNER_SECONDS = 5.0

# --- Hardware setup ----------------------------------------------------------

i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

_button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)


def _button_pressed():
    """True while the approve button is held down."""
    return _button.value() == 0


def _sanitize_line(text):
    """Remove non-printable ASCII characters and limit to LCD width."""
    result = ""

    for ch in text:
        code = ord(ch)

        # Printable ASCII characters: space (32) ... ~ (126)
        if 32 <= code <= 126:
            result += ch

    return result[:I2C_NUM_COLS]


def _show_header_and_footer(header, footer):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(_sanitize_line(header))
    lcd.move_to(0, 1)
    lcd.putstr(_sanitize_line(footer))


def _show_message(message):
    _show_header_and_footer("Received message:", message)


def _show_approved():
    _show_header_and_footer("Message was", "Approved")


# --- Approval state (guarded by the lock: phew handlers run in its own
# worker thread, so the web thread and the button thread must not tear it
# apart) ----------------------------------------------------------------------

_state_lock = _thread.allocate_lock()
_current_message = ""
_approved = False


def _on_button_pressed():
    """Called by the button polling thread."""
    global _approved
    with _state_lock:
        _approved = True
    print("Button pressed: message approved.")
    _show_approved()
    # Keep the banner visible for a while, then show the message again.
    time.sleep(APPROVAL_BANNER_SECONDS)
    with _state_lock:
        current = _current_message
    if current:
        _show_message(current)


def _poll_button():
    """Background thread: react to the physical approve button."""
    while True:
        if _button_pressed():
            _on_button_pressed()
            # De-bounce: wait until the button is released again.
            while _button_pressed():
                time.sleep(0.05)
        time.sleep(BUTTON_POLL_INTERVAL)


# --- Wi-Fi -------------------------------------------------------------------

def _connect_wifi():
    """Connect to Wi-Fi, retrying forever. Returns the assigned IP address."""
    details = wifiDetails()
    while True:
        ip = connect_to_wifi(details.getSSID(), details.getPassword())
        if ip is not None:
            return ip
        print("Wi-Fi connection failed, retrying in 2s...")
        _show_header_and_footer("Connection", "failed ...")
        time.sleep(2)


# --- Web server --------------------------------------------------------------

def _load_index_html():
    try:
        with open("index.html", "r") as page:
            return page.read()
    except OSError as exc:
        return "<h1>index.html missing</h1><p>%s</p>" % exc


def _setup_routes(index_html):
    @server.route("/", methods=["GET"])
    def home(request):
        return index_html

    @server.route("/", methods=["POST"])
    def save_message(request):
        global _current_message
        with _state_lock:
            global _approved
            _approved = False

        message = request.form.get("message") or ""
        if not message.strip():
            _show_header_and_footer("Error", "Empty message")
            return index_html

        with _state_lock:
            _current_message = message
        print("Received message: %r" % message)
        _show_message(message)
        return index_html

    @server.route("/check_approval", methods=["GET"])
    def check_status(request):
        with _state_lock:
            approved = _approved
        # If the physical button was pressed in the meantime (e.g. no
        # polling thread caught it), honour it here as well.
        if not approved and _button_pressed():
            _on_button_pressed()
            approved = True
        return "approved" if approved else "pending"

    @server.catchall()
    def catchall(request):
        return "Page not found", 404


# --- Entry point -------------------------------------------------------------

def main():
    print("Connecting to Wi-Fi...")
    ip = _connect_wifi()
    print("Got IP:", ip)
    _show_header_and_footer("Assigned IP:", ip)

    index_html = _load_index_html()
    _setup_routes(index_html)

    _thread.start_new_thread(_poll_button, ())

    print("Starting HTTP server on http://%s/" % ip)
    server.run()


main()
