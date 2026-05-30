class wifiDetails:
    def __init__(self):
        self.__ssid = 'Your_SSID'
        self.__password = 'Your_PASS'

    def getSSID(self) -> str:
        return self.__ssid
    
    def getPassword(self) -> str:
        return self.__password
    
    def __str__(self) -> str:
        return f"network: ${self.__ssid} ; pass: ${self.__password}"