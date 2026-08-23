# PicoPager

A web-based "pager" for the **Raspberry Pi Pico 2W**: send a short message
from a browser (phone or laptop), have it displayed on a 16x2 LCD, and
acknowledge it with a physical button. The sender's browser is alerted once
the message is approved.

## Hardware

| Part                | Connection                                             |
|---------------------|--------------------------------------------------------|
| Pico 2W            | Wi-Fi (built-in CYW43)                                 |
| LCD1602 + PCF8574 I2C backpack | GP4 = SDA, GP5 = SCL (I2C bus 0, addr 0x27 or 0x3F) |
| Approve button     | GP15 to GND (internal pull-up used; LOW = pressed)     |

## How it works

```
Browser form --POST /--> phew HTTP server --> message shown on LCD
Browser polls GET /check_approval (every 1.5 s)
Local button pressed --> LCD: "Message was Approved" --> "approved" returned
Browser shows JS alert: "Your msg is received and has been approved"
```

- `main.py` ? entry point: Wi-Fi (with retries), LCD init, phew routes,
  background button-polling thread.
- `index.html` ? the (unchanged) web page: form + approval polling.
- `wifiCredentials.py` ? Wi-Fi SSID/password (edit before flashing).
- `vendor/lcd_api.py`, `vendor/pico_i2c_lcd.py` ? upstream
  [micropython-lib `pico_i2c_lcd`](https://github.com/micropython/micropython-lib)
  driver for HD44780 LCDs over a PCF8574 I2C backpack.

## Setup

1. Edit `wifiCredentials.py` and set your `ssid` / `password`.
2. Flash MicroPython (with the `phew` web framework) onto the Pico 2W, e.g.
   with `mpremote`:
   ```
   mpremote connect auto fs cp main.py index.html wifiCredentials.py :
   mpremote connect auto fs mkdir -p vendor
   mpremote connect auto fs cp vendor/lcd_api.py vendor/pico_i2c_lcd.py :vendor/
   ```
   (or copy the files with any USB mass-storage tool)
3. Reset the board. It shows connection status, then its assigned IP on the LCD.
4. Open `http://<pico-ip>/` in a browser, type a message (max 15 chars),
   press **Send**.
5. Press the physical button on the Pico to approve. The LCD shows
   "Message was Approved", and the browser shows the confirmation alert.

## Notes

- Messages are limited to 15 chars (fits one LCD line).
- Each new message resets the approval state.
- If the LCD is not found at 0x27, change `I2C_ADDR` in `main.py` to 0x3F.
