
from simmodule.networkExceptions import GPSNotFixedException
from simmodule.network import SendCommand

AT_CMD_CGNSPWR1 = "AT+CGNSPWR=1\n"
AT_CMD_GNSPWRR = "AT+CGNSPWR?\n"

AT_CMD_CGNSINF = "AT+CGNSINF\n"

AT_RSP_OK = "OK"
AT_RSP_CGNSINF = "+CGNSINF"
AT_RSP_CGNSPWR = "+CGNSPWR"

initialized = False

def InitializeGPS():
    global initialized
    print("Initializing GPS...")
    response = SendCommand(AT_CMD_GNSPWRR, AT_RSP_CGNSPWR)
    response = response.decode('utf-8').split(" ")[1]
    if(response == "0\r\n"):
        SendCommand(AT_CMD_CGNSPWR1, AT_RSP_OK)
        initialized = True
    print("GPS Init Complete!")
    initialized = True

def GetCoordinates():
    if(not initialized):
        InitializeGPS()
    
    response = SendCommand(AT_CMD_CGNSINF, AT_RSP_CGNSINF)
    response = response.decode('utf-8').split(" ")
    dataSplit = response[1].split(",")

    if(dataSplit[1] == '0' or dataSplit[0] == '0'):
        raise GPSNotFixedException("GPS does not have a fixed position!")

    latitude = dataSplit[3]
    longitude = dataSplit[4]

    return latitude, longitude