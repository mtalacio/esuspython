from types import resolve_bases
from metrics import GetElapsedTime, GetPermanentDistance, GetSpeedAndBattery, GetStoredDistance, ResetAll, ResetDistanceBuffer, StartMetricsClient, StoreDistance
from simmodule.networkExceptions import GPSNotFixedException, InvalidResponseException, SIMNetworkError
import time
from simmodule.network import GetVehicleStatus, InitializeModule, PostDistance, PostGPSData
from simmodule.gps import GetCoordinates, InitializeGPS
import threading
from tkinter import *
from tkinter import ttk
import pyqrcode
import RPi.GPIO as GPIO

lock = threading.Lock()

vehicleStatus = 0

def AwaitForSync():
    global vehicleStatus
    serverData = b""
    while(True):
        with lock:
            try:
                serverData = GetVehicleStatus()
            except SIMNetworkError as err:
                print(err)
        if("2\r\n".encode() in serverData or "1\r\n".encode() in serverData):
            print("Starting vehicle... <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
            vehicleStatus = 1
            StartRunningThreads()
            break
        time.sleep(1)

def StartSync():
    syncThread = threading.Thread(target=AwaitForSync)
    syncThread.start()

root = Tk()
root.attributes("-fullscreen", True)

root.overrideredirect(True)

def raiseFrame(frame):
    frame.tkraise()

# loader frame
loader = ttk.Frame(root)
loader.columnconfigure(0, weight=1)
loader.rowconfigure(0, weight=1)
loader.grid(column=0, row=0, sticky='news')

statusLabel = ttk.Label(loader, text="Connecting...", font=("Arial", 20))
statusLabel.grid(column=0, row=0)

# sync frame

code = pyqrcode.create("$-321")
qr_image = code.xbm(scale=6)
code_bmp = BitmapImage(data=qr_image)
code_bmp.config(background="white")

content = ttk.Frame(root)
content.grid(column=0, row=0, sticky='news')
logo = PhotoImage(file="/home/pi/Desktop/esuspython/esus.png")
logoLabel = ttk.Label(content)
logoLabel['image'] = code_bmp

logoLabel.grid(column=0, row=0, pady=30)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

content.columnconfigure(0, weight=1)

content.rowconfigure(1, minsize=100)

#running frame
running = ttk.Frame(root)
running.grid(column=0, row=0, sticky='news')

running.columnconfigure(1, weight=1)
running.rowconfigure(2, minsize=80)

logoLabel = ttk.Label(running)
logoLabel['image'] = logo
logoLabel.grid(column=0, row=0, pady=10, padx=10, rowspan=2)

batLabel = ttk.Label(running, text="Battery level:")
batLabel.grid(column=1, row=0, sticky=(SE))
battery = ttk.Progressbar(running, orient=HORIZONTAL, length=100, mode="determinate")
battery.grid(column=1, row=1, sticky=(E))
battery['value'] = 99
levelLabel = ttk.Label(running, text="0%")
levelLabel.grid(column=2, row=1, padx=10, sticky=(W))

kmLabel = ttk.Label(running, text="Distance this session",  font=("Arial", 12))
kmLabel.grid(column=1, row=2, sticky=(S))

kmLabel = ttk.Label(running, text="0 km", font=("Arial", 30))
kmLabel.grid(column=1, row=3, sticky=(N))

speed = ttk.Label(running, text="0 km/h", font=("Arial", 30))
speed.grid(column=0, row=3)

raiseFrame(loader)

connected = False

flag = False

GPIO.setmode(GPIO.BOARD)
GPIO.setup(8, GPIO.OUT)
GPIO.output(8, GPIO.LOW)

def Reset():
    global flag
    flag = True
    raiseFrame(content)

def GetVehicleData():
    global vehicleStatus 
    while(True):
        if(flag):
            break

        if(vehicleStatus == 0):
            with lock:
                if(flag):
                    break
                try:
                    serverData = GetVehicleStatus()
                except SIMNetworkError as err:
                    print(err)
                except InvalidResponseException as err:
                    print(err)
            if("2\r\n".encode() in serverData or "1\r\n".encode() in serverData):
                print("Releasing lock... <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                vehicleStatus = 1
                GPIO.output(8, GPIO.LOW)
            elif("0\r\n".encode() in serverData):
                Reset()
            time.sleep(2)
        elif(vehicleStatus == 1):
            with lock:
                try:
                    serverData = GetVehicleStatus()
                except SIMNetworkError as err:
                    print(err)
                except InvalidResponseException as err:
                    print(err)
            if("2\r\n".encode() not in serverData):
                print("Locking vehicle >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                GPIO.output(8, GPIO.HIGH)

                vehicleStatus = 0
                if("0\r\n".encode() in serverData):
                    Reset()

            time.sleep(20)

def PushGPSData():
    while(True):
        if(flag):
            break

        time.sleep(1)
        with lock:
            if(flag):
                break
            try:
                lat, lng = GetCoordinates()
                if(connected):
                    PostGPSData(lat, lng)
            except GPSNotFixedException as err:
                print(err)
            except InvalidResponseException as err:
                print(err)
            except SIMNetworkError as err:
                print(err)
        time.sleep(120)

def Metrics():
    counter = 0
    StartMetricsClient()
    time.sleep(2)
    while(True):
        if(flag):
            break

        with lock:
            if(flag):
                break
            try:
                print("Fetching coordinates to distance")
                lat, lng = GetCoordinates()
                StoreDistance(float(lat), float(lng))
                kmLabel['text'] = str(round(GetPermanentDistance(), 2)) + " km"
            except GPSNotFixedException as err:
                print(err)

            speedData, batteryData = GetSpeedAndBattery()
            speed['text'] = str(round(speedData, 2)) + " km/h"
            batteryData = float(batteryData)
            batteryData = batteryData / 10
            battery['value'] = batteryData
            levelLabel['text'] = str(batteryData) + "%"
        if(counter > 30):
            with lock:
                try:
                    print("Sending distance data")
                    distance = GetStoredDistance()
                    elapsed = GetElapsedTime()

                    if(distance > 0.7 or distance < 0.01):
                        distance = 0
                    
                    if(connected):
                        PostDistance(distance, elapsed)
                except SIMNetworkError as err:
                    print(err)
                except InvalidResponseException as err:
                    print(err)
            counter = 0
            ResetDistanceBuffer()

        counter = counter + 1
        time.sleep(1)

def StartRunningThreads():
    global flag
    flag = False
    ResetAll()

    if(connected):
        lockThread = threading.Thread(target=GetVehicleData)
        lockThread.start()

    gpsThread = threading.Thread(target=PushGPSData)
    gpsThread.start()

    metricsThread = threading.Thread(target=Metrics)
    metricsThread.start()

    raiseFrame(running)

def ConfigThread():
    global connected
    try:
        statusLabel['text'] = "Starting vehicle..."
        time.sleep(10)
        connected = InitializeModule()
        if(not connected):
            statusLabel['text'] = "Could not connect to network!"

        statusLabel['text'] = "Starting GPS..."
        InitializeGPS()

        if(not connected):
            StartRunningThreads()
            return
        
        raiseFrame(content)
        syncThread = threading.Thread(target=AwaitForSync)
        syncThread.start()
    except Exception as err:
        print(err)
        statusLabel['text'] = err.message
        exit()

def main():
    configThread = threading.Thread(target=ConfigThread)
    configThread.start()
    print("Start")
    root.mainloop()
    print("Threads started")

if __name__ == "__main__":
    main()