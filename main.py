import time
from simmodule.network import GetVehicleStatus, InitializeModule, PostGPSData
from simmodule.gps import GetCoordinates, InitializeGPS
import threading

lock = threading.Lock()

vehicleStatus = 0

def GetVehicleData():
    global vehicleStatus 
    while(True):
        if(vehicleStatus == 0):
            with lock:
                serverData = GetVehicleStatus()
            if("2\r\n".encode() in serverData or "1\r\n".encode() in serverData):
                print("Releasing lock... <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                vehicleStatus = 1
            
            time.sleep(2)
        elif(vehicleStatus == 1):
            with lock:
                serverData = GetVehicleStatus()
            if("2\r\n".encode() not in serverData):
                print("Locking vehicle >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                vehicleStatus = 0

            time.sleep(10)

def PushGPSData():
    while(True):
        time.sleep(1)
        with lock:
            try:
                lat, lng = GetCoordinates()
                PostGPSData(lat, lng)
            except GPSNotFixedException as err:
                print(err)
        
        time.sleep(10)



def main():
    try:
        InitializeModule()
        InitializeGPS()
    except Exception as err:
        print(err)
        exit()

    print("Start")

    lockThread = threading.Thread(target=GetVehicleData)
    lockThread.start()

    gpsThread = threading.Thread(target=PushGPSData)
    gpsThread.start()

    print("Threads started")


if __name__ == "__main__":
    main()