from metrics import GetStoredDistance, ResetDistanceBuffer, StoreDistance
from simmodule.networkExceptions import GPSNotFixedException, SIMNetworkError
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
                try:
                    serverData = GetVehicleStatus()
                except SIMNetworkError as err:
                    print(err)

            if("2\r\n".encode() in serverData or "1\r\n".encode() in serverData):
                print("Releasing lock... <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                vehicleStatus = 1
            
            time.sleep(2)
        elif(vehicleStatus == 1):
            with lock:
                try:
                    serverData = GetVehicleStatus()
                except SIMNetworkError as err:
                    print(err)
            if("2\r\n".encode() not in serverData):
                print("Locking vehicle >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                vehicleStatus = 0

            time.sleep(20)

def PushGPSData():
    while(True):
        time.sleep(1)
        with lock:
            try:
                lat, lng = GetCoordinates()
                PostGPSData(lat, lng)
            except GPSNotFixedException as err:
                print(err)
        
        time.sleep(120)

def Metrics():
    counter = 0
    while(True):
        time.sleep(2)

        with lock:
            try:
                print("Fetching coordinates to distance")
                lat, lng = GetCoordinates()
                StoreDistance(float(lat), float(lng))
            except GPSNotFixedException as err:
                print(err)
        
        if(counter > 12):
            distance  = GetStoredDistance()
            #Send distance data
            counter = 0
            ResetDistanceBuffer()

        counter = counter + 1
        time.sleep(5)

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
    #gpsThread.start()

    metricsThread = threading.Thread(target=Metrics)
    metricsThread.start()

    print("Threads started")


if __name__ == "__main__":
    main()