"""Wi-Fi credentials for PicoPager.

Fill in your network SSID and password below.
"""


class wifiDetails:
    def __init__(self, ssid=None, password=None):
        if ssid is not None:
            self._ssid = ssid
        else:
            self._ssid = "Your_SSID"
        if password is not None:
            self._password = password
        else:
            self._password = "Your_PASS"

    def getSSID(self):
        return self._ssid

    def getPassword(self):
        return self._password

    def __str__(self):
        return "network: {} ; pass: {}".format(self._ssid, self._password)
