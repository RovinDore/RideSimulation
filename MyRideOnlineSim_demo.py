import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
import random
import calendar
import json
import time
from time import sleep
import datetime
from datetime import timedelta

#Set up global variables
#====================================================================================
credMyRide = credentials.Certificate('')
firebase_admin.initialize_app(credMyRide, {
    u'databaseURL': u'',
    u'projectId': u''
})

# Firestore data
firestoreDB = firestore.client()
firestoreRef = firestoreDB.collection(u'siteSettings').document(u'busSimulation')

#Realtime data
firebaseRef = db.reference(u'/MyRide/BusGEO/')

newCoords = []
simBuses = [] #array for buses simulation data
mainLoop = 1
interval = 30
#=========================================
#end global variables

# add bus data to global array
def addSimArray(name, route, country):
    global interval, newCoords
    
    if route == 'W':
        endArr = len(WestRoute_dict) - 1
    else:
        endArr = len(EastRoute_dict) - 1
        
    #Bus data
    startSec = random.randint(1, interval)
    startLoop = random.randint(1, endArr)
    randDirection = random.randint(0, 360)
    startDirection = randDirection % 2
    startDeg = 0
    dbName = name.replace(" ", "")
    
    if startDirection == 0:
        if route == 'W':
            startDeg = 270
        else:
            startDeg = 90
    else:
        if route == 'W':
            startDeg = 90
        else:
            startDeg = 270
        
    data = {
        'busName': name,
        'seconds': startSec,
        'loop': startLoop,
        'direction': startDirection,
        'heading': startDeg,
        'dbName': dbName,
        'route': route,
        'country': country
    }
    
    simBuses.append(data)

#switch status of active buses to off
def offBuses():
    global simBuses, firebaseRef, firestoreRef
    
    print('Turning off buses')
    for bus in simBuses:
        # direction = bus['direction']
        busName = bus['busName']
        dbName = bus['dbName']
        route = bus['route']
        country = bus['country']
        listPosition = int(bus['loop'])
        
        #Set bus coords East / West
        if route == 'W':
            nowCoord = WestRoute_dict[listPosition]['coords']
        else:
            nowCoord = EastRoute_dict[listPosition]['coords']
            
        millis = int(round(time.time() * 1000))
        lat = nowCoord['lat']
        lng = nowCoord['lng']
        finalCoords = {
            'lat': lat,
            'lng': lng
        }
        sendData = {
            'coords': finalCoords,
            'busName': busName,
            'time': millis,
            'gpsState': False,
            'degrees': bus['heading'],
            'country': country
        }
        
        firebaseRef.child(dbName).set(sendData)

    firestoreRef.update({u'action': u"All Buses turned off!"})
    print('All Buses turned off') 

# Main function
def runSim():
    global mainLoop, newCoords, simBuses, firebaseRef, interval, firestoreRef
    
    mainLoop = 1
    print("Starting simulation")
    doLoad()
    print("BUSES!!!")
    for bus in simBuses:
        print(bus)
    
    doLoad()
    
    #Determine when to restart buses
    runMySim = False

    while True:
        print (mainLoop)
        firestoreRef.update({u'loop': mainLoop})

        simStatus = firestoreRef.get()
        simStatus = simStatus.to_dict()
        # print(u'Document data: {}'.format(simStatus.to_dict()))
        if simStatus['active'] == True and simStatus['status'] == 'play':
            runMySim = True
            #print(datetime.datetime.now())
            for bus in simBuses:
                if bus['seconds'] == mainLoop:
                    direction = bus['direction']
                    busName = bus['busName']
                    dbName = bus['dbName']
                    country = bus['country']
                    listPosition = int(bus['loop'])
                    route = bus['route']
                    
                    #Set bus coords East / West
                    if route == 'W':
                        nowCoord = WestRoute_dict[listPosition]['coords']
                        listEnd = len(WestRoute_dict) - 1
                    else:
                        nowCoord = EastRoute_dict[listPosition]['coords']
                        listEnd = len(EastRoute_dict) - 1

                    millis = int(round(time.time() * 1000))
                    lat = nowCoord['lat']
                    lng = nowCoord['lng']
                    finalCoords = {
                        'lat': lat,
                        'lng': lng
                    }            
                    sendData = {
                        'coords': finalCoords,
                        'busName': busName,
                        'time': millis,
                        'gpsState': True,
                        'degrees': bus['heading'],
                        'country': country
                    }
                    #Send data to firebase
                    firebaseRef.child(dbName).set(sendData)
                    firestoreRef.update({u'action': u"sent data for: " + busName})
                    print ("sent data for:", busName, "#", listPosition)
                    
                    if direction == 1:
                        bus['loop'] += 1
                        if bus['loop'] >= listEnd:
                            bus['direction'] = 0
                            bus['heading'] = 270
                    else:
                        bus['loop'] -= 1
                        if bus['loop'] <= 0:
                            bus['direction'] = 1
                            bus['heading'] = 90
        else:
            if simStatus['status'] == 'pause':
                firestoreRef.update({u'action': u"Simulation Paused!"})
                print ('Simulation Paused')
            elif simStatus['active'] == False:
                if runMySim == True:
                    offBuses()
                    simBuses = []
                    loadBuses_West()
                    loadBuses_East()
                    runMySim = False
                    firestoreRef.update({u'action': u"Simulation Deactivated!"})
                    print ('Simulation Deactivated!')
                print ('Waiting for Activation')
            # elif simStatus['active'] == True:
            #     if runMySim == False:
            #         loadBuses_West()
            #         loadBuses_East()
            else:
                print ('Simulation running without updating')

        if simStatus['status'] == 'play':
            if mainLoop == interval:
                mainLoop = 1
            else:
                if simStatus['active'] == True:
                    mainLoop += 1
                else:
                    mainLoop = 1
            
        time.sleep(1)

def doLoad():
    for x in range(0, 3):
        print (".")
        time.sleep(1)

def loadBuses_West():
    global WestRoute_dict, firestoreRef
    print('Getting West Side locations')
    with open('./westsidebus.json', 'r') as WestRoute:
        WestRoute_dict = json.load(WestRoute)
    print('Got locations! #', len(WestRoute_dict))
    doLoad()
    print('Setting West Side buses')
    addSimArray('Hot Tool', 'W', 'SK')
    addSimArray('Jabo', 'W', 'SK')
    addSimArray('Jigga', 'W', 'SK')
    addSimArray('Mickey', 'W', 'SK')
    addSimArray('Darblo', 'W', 'SK')
    addSimArray('Formula', 'W', 'SK')
    addSimArray('Red Man', 'W', 'SK')
    addSimArray('Pink Elephant', 'W', 'SK')
    addSimArray('Black Beauty', 'W', 'SK')

    addSimArray('Jabo Nevis', 'W', 'NV')
    addSimArray('Jigga Nevis', 'W', 'NV')
    addSimArray('Mickey Nevis', 'W', 'NV')
    addSimArray('Darblo Nevis', 'W', 'NV')
    addSimArray('Shuckle', 'W', 'NV')
    firestoreRef.update({u'action': u"West Side Bus Route Set!"})

def loadBuses_East():
    global EastRoute_dict, firestoreRef
    print('Getting East Side locations')
    #Json file East side bus route
    with open('./eastsidebus.json', 'r') as EastRoute:
        EastRoute_dict = json.load(EastRoute)
    print('Got locations! #', len(EastRoute_dict))
    doLoad()
    print('Setting East Side buses')
    addSimArray('Golden Touch', 'E', 'SK')
    addSimArray('Do Road', 'E', 'SK')
    addSimArray('Bus', 'E', 'SK')

    addSimArray('Golden Touch Nevis', 'E', 'NV')
    addSimArray('Do Road Nevis', 'E', 'NV')
    addSimArray('Bus Nevis', 'E', 'NV')
    addSimArray('Ride Out', 'E', 'NV')
    firestoreRef.update({u'action': u"East Side Bus Route Set!"})
    
print('Starting program')
doLoad()
    
print('Setting bus data')
loadBuses_West()
loadBuses_East()

print('Finish setting bus data')
doLoad()

try:
    offBuses()
    runSim()
except:
    #print("Restarting sim")
    pause = 0
    
    if pause == 1:
        print("How long? (seconds)")
        length = input()
        time.sleep(length)
        runSim()
    else:
        print('Restarting simulation')
        firestoreRef.update({u'action': u"Something went wrong restarting Simulation!"})
        offBuses()
        simBuses = []
        # time.sleep(30)
        loadBuses_West()
        loadBuses_East()
        runSim()
finally:
    offBuses()
    print('Good Bye!')