from math import asin, cos, radians, sin, sqrt

lastLatitude = -1
lastLongitude = -1

distanceBuffer = 0

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
    distance = c * 6371000
    lastLatitude = lat
    lastLongitude = lng
    print("Storing distance " + str(distance) + "m")
    return distance
    

def StoreDistance(lat, lng):
    global distanceBuffer
    distanceBuffer = distanceBuffer + CalculateDistance(lat, lng)

def GetStoredDistance():
    return distanceBuffer

def ResetDistanceBuffer():
    global distanceBuffer
    distanceBuffer = 0