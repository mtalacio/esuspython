from simmodule.networkExceptions import InvalidResponseException, SIMNetworkError
import serial
import time
import RPi.GPIO as GPIO

AT_CMD_SAPBR1 = "AT+SAPBR=1,1\n"
AT_CMD_HTTPINIT = "AT+HTTPINIT\n"
AT_CMD_HTTPPARA_CID = "AT+HTTPPARA=\"CID\",\"1\"\n"
AT_CMD_HTTPPARA_URL = "AT+HTTPPARA=\"URL\","
AT_CMD_HTTPPARA_CONTENT = "AT+HTTPPARA=\"CONTENT\",\"application/json\"\n"
AT_CMD_HTTPDATA = "AT+HTTPDATA="
AT_CMD_HTTPACTION0 = "AT+HTTPACTION=0\n"
AT_CMD_HTTPACTION1 = "AT+HTTPACTION=1\n"
AT_CMD_HTTPREAD = "AT+HTTPREAD\n"
AT_CMD_HTTPTERM = "AT+HTTPTERM\n"
AT_CMD_SAPBR0 = "AT+SAPBR=0,1\n"

AT_RSP_OK = "OK"
AT_RSP_HTTPACTION = "+HTTPACTION"
AT_RSP_REG = "+CREG: 0,1"

AT_CMD_SAPBR_GPRS = "AT+SAPBR=3,1,\"Contype\",\"GPRS\"\n"
AT_CMD_SAPBR_APN = "AT+SAPBR=3,1,\"APN\",\"internet\"\n"
AT_CMD_CMEE = "AT+CMEE=2\n"
AT_CMD_CREG = "AT+CREG?\n"

URL_GET = "http://us-central1-esus-d4f3d.cloudfunctions.net/getStatus?id=321&company=oDUmqHdibXU8bETkm6KY5PK2aiQ2"
URL_POST = "http://us-central1-esus-d4f3d.cloudfunctions.net/pushVehicleLocation"
COMPANY_ID = "oDUmqHdibXU8bETkm6KY5PK2aiQ2"
VEHICLE_ID = "321"

ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=5)

gprsInitialized = False
httpInitialized = False

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)

def ToggleModulePower():
    GPIO.output(7, GPIO.LOW)
    time.sleep(4)
    GPIO.output(7, GPIO.HIGH)
    GPIO.cleanup()

def ReadSerial():
    data = ser.readline()
    if(data == "\r\n".encode()):
        time.sleep(0.1)
        return ReadSerial()
    
    print("Received > " + data.decode('utf-8'))
    return data

def SendCommand(command, expected):
    print("Sending " + command)
    ser.write(command.encode())
    ser.flush()

    data = ReadSerial()
    internalTries = 0
    while(expected.encode() not in data):
        if(internalTries > 3):
            raise InvalidResponseException("Error in sending message > " + command)
        data = ReadSerial()
        internalTries = internalTries + 1
    
    return data


def SendCommandPayload(command, payload, expected, quotes):
    print("Sending " + command + payload)
    ser.write(command.encode())
    if(quotes):
        ser.write("\"".encode())
    ser.write(payload.encode())
    if(quotes):
        ser.write("\"".encode())
    ser.write("\n".encode())
    ser.flush()
    
    data = ReadSerial()
    internalTries = 0
    while(expected.encode() not in data):
        if(internalTries > 3):
            raise InvalidResponseException("Error in sending message > " + command)
        data = ReadSerial()
        internalTries = internalTries + 1
    
    return data

def HTTPRead():
    command = AT_CMD_HTTPREAD
    print("Sending " + command)
    ser.write(command.encode())
    ser.flush()

    data = ReadSerial()
    internalTries = 0
    while("+HTTPREAD".encode() not in data):
        if(internalTries > 3):
            raise InvalidResponseException("Error in sending message > " + command)
        data = ReadSerial()
        internalTries = internalTries + 1
    
    payload = ReadSerial()
    
    print("Payload Received >> " + payload.decode('utf-8'))
    
    data = ReadSerial()
    while("OK".encode() not in data):
        if(internalTries > 3):
            raise InvalidResponseException("Error in sending message > " + command)
        data = ReadSerial()
        internalTries = internalTries + 1
    
    return payload

def InitializeModule():
    print("Reseting module...")
    try:
        SendCommand("ATE0\n", AT_RSP_OK)
        #ToggleModulePower()
        #ToggleModulePower()
    except InvalidResponseException:
        ToggleModulePower()
        return

    print("Configuring module...")

    SendCommand("ATE0\n", AT_RSP_OK)
    SendCommand("AT\n", AT_RSP_OK)

    SendCommand(AT_CMD_SAPBR_GPRS, AT_RSP_OK)
    SendCommand(AT_CMD_SAPBR_APN, AT_RSP_OK)
    SendCommand(AT_CMD_CMEE, AT_RSP_OK)
    SendCommand(AT_CMD_CREG, AT_RSP_REG)
    print("Module ready!")

def TerminateGprs():
    global httpInitialized, gprsInitialized

    print("Terminating GPRS connection by error")

    if(httpInitialized):
        SendCommand(AT_CMD_HTTPTERM, AT_RSP_OK)
        httpInitialized = False
    
    if(gprsInitialized):
        SendCommand(AT_CMD_SAPBR0, AT_RSP_OK)
        gprsInitialized = False

def GetVehicleStatus():
    global httpInitialized, gprsInitialized
    print("Starting HTTP GET...")
    
    try:
        SendCommand(AT_CMD_SAPBR1, AT_RSP_OK)
        gprsInitialized = True
        time.sleep(1)
        SendCommand(AT_CMD_HTTPINIT, AT_RSP_OK)
        httpInitialized = True
        time.sleep(1)
        SendCommand(AT_CMD_HTTPPARA_CID, AT_RSP_OK)
        SendCommandPayload(AT_CMD_HTTPPARA_URL, URL_GET, AT_RSP_OK, True)
        SendCommandPayload(AT_CMD_HTTPDATA, "0,5000", AT_RSP_OK, False)
        SendCommand(AT_CMD_HTTPACTION0, AT_RSP_HTTPACTION)

        payload = HTTPRead()

        SendCommand(AT_CMD_HTTPTERM, AT_RSP_OK)
        httpInitialized = False

        SendCommand(AT_CMD_SAPBR0, AT_RSP_OK)
        gprsInitialized = False
    except InvalidResponseException as err:
        print(err.message)
        TerminateGprs()
        raise SIMNetworkError("Get Failed")
    
    return payload

def PostGPSData(latitude, longitude):
    global httpInitialized, gprsInitialized
    print("Starting HTTP POST...")

    try:
        payload = "{\"idv\":\""+ VEHICLE_ID + "\",\"idc\":\"" + COMPANY_ID + "\",\"lat\":\"" + latitude + "\",\"lng\":\"" + longitude +"\"}\n"
        payloadSize = len(payload)

        SendCommand(AT_CMD_SAPBR1, AT_RSP_OK)
        gprsInitialized = True
        time.sleep(1)
        SendCommand(AT_CMD_HTTPINIT, AT_RSP_OK)
        httpInitialized = True
        time.sleep(1)
        SendCommand(AT_CMD_HTTPPARA_CID, AT_RSP_OK)
        SendCommandPayload(AT_CMD_HTTPPARA_URL, URL_POST, AT_RSP_OK, True)
        SendCommand(AT_CMD_HTTPPARA_CONTENT, AT_RSP_OK)
        SendCommandPayload(AT_CMD_HTTPDATA, str(payloadSize) + ",5000", "DOWNLOAD", False)
        SendCommand(payload, AT_RSP_OK)
        SendCommand(AT_CMD_HTTPACTION1, AT_RSP_HTTPACTION)
        payload = HTTPRead()
        
        SendCommand(AT_CMD_HTTPTERM, AT_RSP_OK)
        httpInitialized = False

        SendCommand(AT_CMD_SAPBR0, AT_RSP_OK)
        gprsInitialized = False
    except InvalidResponseException as err:
        print(err.message)
        TerminateGprs()
        raise SIMNetworkError("Post Failed")