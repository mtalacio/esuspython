from math import asin, cos, radians, sin, sqrt
import time
import socket

lastLatitude = -1
lastLongitude = -1

lastSpeed = 0

distanceBuffer = 0

distanceStorage = 0

lastTime = -1

elapsedTime = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = "127.0.0.1"
PORT = 50000

def StartMetricsClient():
    while True:
        try:
            sock.connect((HOST, PORT))
            print("Metrics server initialized")
            break
        except TimeoutError:
            print("Server not started, waiting 2 seconds")

def CalculateDistance(lat, lng):
    global lastLatitude, lastLongitude
    print("Last lat " + str(lastLatitude))
    print("Last lnt " + str(lastLongitude))
    if(lastLatitude == -1 and lastLongitude == -1):
        lastLatitude = lat
        lastLongitude = lng
        return 0
    
    lngR, latR, lastLongitude, lastLatitude = map(radians, [lng, lat, lastLongitude, lastLatitude])

    dLon = lastLongitude - lngR
    dLat = lastLatitude - latR

    a = sin(dLat/2)**2 + cos(latR) * cos(lastLatitude) * sin(dLon/2)**2
    c = 2 * asin(sqrt(a))
    distance = c * 6371
    lastLatitude = lat
    lastLongitude = lng
    print("Storing distance " + str(distance) + "km")
    return distance

def StoreDistance(lat, lng):
    global distanceBuffer, lastSpeed, lastTime, distanceStorage, elapsedTime
    thisDistance = CalculateDistance(lat, lng)

    if thisDistance > 10 or thisDistance < 1:
        return

    distanceBuffer = distanceBuffer + thisDistance
    distanceStorage = distanceStorage + distanceBuffer
    if lastTime == -1:
        lastTime = time.time()
        return

    elapsed = time.time() - lastTime
    elapsedTime = elapsedTime + elapsed
    lastSpeed = thisDistance / (elapsed / 60 / 60)
    
    lastTime = time.time()

def GetSpeedAndBattery():
    print("Getting from socket")
    sock.sendall(b"R")
    response = sock.recv(1024)
    response = response.decode('utf-8')
    print("Response >> " + response)
    response = response.split(',')

    return response[0], response[1]

def GetStoredDistance():
    return distanceBuffer

def GetPermanentDistance():
    return distanceStorage

def GetElapsedTime():
    return elapsedTime

def ResetDistanceBuffer():
    global distanceBuffer
    distanceBuffer = 0

def ResetElapsedTime():
    global elapsedTime
    elapsedTime = 0

def ResetAll():
    global elapsedTime, lastLatitude, lastLongitude, distanceStorage, distanceBuffer, lastSpeed, lastTime
    lastLatitude = -1
    lastLongitude = -1

    lastSpeed = 0

    distanceBuffer = 0
    distanceStorage = 0

    lastTime = -1
    elapsedTime = 0
