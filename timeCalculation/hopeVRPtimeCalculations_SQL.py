#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import sys
import mysql.connector
import urllib.request
import json
import math
from datetime import timedelta, datetime


# In[ ]:


#get_ipython().run_line_magic('config', 'Completer.use_jedi = False')


# In[ ]:


load_id = str(sys.argv[1])
page = str(sys.argv[2])
db = str(sys.argv[3])


# In[ ]:


# load_id = input()
# page = 'load_temps'
# db = 'bfdb'


# In[ ]:


mydb  = mysql.connector.connect(
                                host = '144.217.38.21',
                                user = 'bf4u',
                                password = 'Zn6+YsUU',
                                database = db
                                )
mycursor = mydb.cursor()


# In[ ]:


def getLoadOrders():
    query = "SELECT `orders`, `flowType`, `depoId`, `return`, `startTime`, `shiftId` FROM " + page + " WHERE id = " + load_id
    try:
        mycursor.execute(query)
        result = mycursor.fetchall()[0]
        return result
    except:
        print("Execution Failed")


# In[ ]:


output = getLoadOrders()


# In[ ]:


load_order = output[0].split(',')
load_orders = tuple(int(i) for i in load_order)
flowType = output[1]
depoId = output[2]
returned = output[3]
startTime = output[4]
shiftId = output[5]


# In[ ]:


def getShifts():
    query = "SELECT `break_time`, `rest`, `shift`, `drivingtime`, `recharge`, `max_shift` FROM shifts WHERE id = " + str(shiftId)
    try:
        mycursor.execute(query)
        resultShift = mycursor.fetchall()[0]
        return resultShift
    except:
        print("Execution Failed")


# In[ ]:


shiftFoo = getShifts() 


# In[ ]:


break_time = shiftFoo[0]
rest = shiftFoo[1]
shift = shiftFoo[2]
drivingtime = shiftFoo[3]
recharge = shiftFoo[4]
max_shift = shiftFoo[5]


# In[ ]:


def getLoadOrdersLatLon():
    if flowType == 1:
        if len(load_orders) > 1:
            query = "SELECT id, pickupLat, pickupLon, pickupdateFrom, pickupdateTo, servicetime FROM orders WHERE id in " + str(load_orders)
        else:
            query = "SELECT id, pickupLat, pickupLon, pickupdateFrom, pickupdateTo, servicetime FROM orders WHERE id = " + str(load_orders[0])
    if flowType == 2:
        if len(load_orders) > 1:
            query = "SELECT id, deliveryLat, deliveryLon, deliverydateFrom, deliverydateTo, servicetime FROM orders WHERE id in " + str(load_orders)
        else:
            query = "SELECT id, deliveryLat, deliveryLon, deliverydateFrom, deliverydateTo, servicetime FROM orders WHERE id = " + str(load_orders[0])   
    try: 
        mycursor.execute(query)
        results = mycursor.fetchall()
        return results
    except:
        print("Execution Failed")


# In[ ]:


df = pd.DataFrame(getLoadOrdersLatLon(), columns = ['id', 'Latitude', 'Longitude', 'TWFrom', "TWTo", "servicetime"])


# In[ ]:


df.index = df['id']
df = df.drop(['id'], axis = 1)


# In[ ]:


def getDepotLatLon():
    query = "SELECT lat, lon, workinghours FROM depos WHERE id = " + str(depoId)
    try:
        mycursor.execute(query)
        resultat = mycursor.fetchall()[0]
        return resultat
    except:
        print("Execution Failed")


# In[ ]:


DepotLatLon = getDepotLatLon()


# In[ ]:


depotLat = DepotLatLon[0]
depotLon = DepotLatLon[1]
depotWorkingHours = json.loads(DepotLatLon[2])


# In[ ]:


daysOfWeek = list(depotWorkingHours.keys())
correspondingIntegersToDaysOfWeek = [4, 0, 6, 1, 5, 3, 2]
for i in range(len(daysOfWeek)):
    depotWorkingHours[correspondingIntegersToDaysOfWeek[i]] = depotWorkingHours.pop(daysOfWeek[i])


# In[ ]:


if pd.to_datetime(depotWorkingHours[startTime.date().weekday()]['from']).time() < pd.to_datetime(depotWorkingHours[startTime.date().weekday()]['to']).time():
    df.loc['depot'] = [depotLat, depotLon, str(startTime.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[startTime.date().weekday()]['from']).time()), str(startTime.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[startTime.date().weekday()]['to']).time()), 0]
    df.loc['depo'] = [depotLat, depotLon, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 0]
else:
    df.loc['depot'] = [depotLat, depotLon, str(startTime.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[startTime.date().weekday()]['from']).time()), pd.to_datetime(str(startTime.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[startTime.date().weekday()]['to']).time())) + timedelta(days = 1), 0]
    df.loc['depo'] = [depotLat, depotLon, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 0]


# In[ ]:


df['TWFrom'] = pd.to_datetime(df['TWFrom'])
df['TWTo'] = pd.to_datetime(df['TWTo'])


# In[ ]:


new_indices = ['depot'] + [i for i in load_orders] + ['depo']


# In[ ]:


df = df.reindex(new_indices)


# In[ ]:


def getResponseHTTPRequest():
    base_url = 'http://planet.map.lessplatform.com/route/v1/driving/'
    for i in df.index:
        base_url += df['Longitude'][i] + ',' + df['Latitude'][i] + ';'
    base_url = base_url[:-1] + '?overview=false&exclude=ferry'
    jsonResult = urllib.request.urlopen(base_url).read()
    response = json.loads(jsonResult)
    return response


# In[ ]:


jsonResponse = getResponseHTTPRequest()


# In[ ]:


if returned == 0:
    totalRouteDistance = jsonResponse['routes'][0]['distance']/1609
else:
    totalRouteDistance = (jsonResponse['routes'][0]['distance'] - jsonResponse['routes'][0]['legs'][-1]['distance'])/1609
print("Total Route Distance in miles:  ", str(totalRouteDistance))


# In[ ]:


if returned == 0:
    drivingTime = str(int(math.modf(jsonResponse['routes'][0]['duration']/3600)[1])) + ':' + str(int(math.modf(jsonResponse['routes'][0]['duration']/3600)[0]*60))
else:
    drivingTime = str(int(math.modf((jsonResponse['routes'][0]['duration'] - jsonResponse['routes'][0]['legs'][-1]['duration'])/3600)[1])) + ':' + str(int(math.modf((jsonResponse['routes'][0]['duration'] - jsonResponse['routes'][0]['legs'][-1]['duration'])/3600)[0]*60))
print("Driving Time:  " + str(drivingTime))


# In[ ]:


def vrpTimeCalculations():
    ETA = []
    
    c = 1     # totalRechargeCoeff
    b = 1     # restCoeff
    # d       rechargeCoeff
    
    wholeDuration = 0
    drvduration = 0
    TotalDrvduration = 0
    totalLoadDuration = 0
    arrTime = 0
    
    breakTimeInterval = break_time
    shiftInterval = shift
    
    global startTime
    if startTime < df['TWFrom']['depot']:
        startTime = df['TWFrom']['depot']
    eta = startTime
    ETA.append(eta)
    
    for i in range(len(jsonResponse['routes'][0]['legs']) - 1):
        drvduration = jsonResponse['routes'][0]['legs'][i]['duration']
        TotalDrvduration += drvduration
        if eta + timedelta(seconds = df.iloc[i, 4] + drvduration) >= df.iloc[i+1, 2]:
            eta += timedelta(seconds = df.iloc[i, 4] + drvduration)
            wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
            if wholeDuration >= breakTimeInterval:
                b = (wholeDuration - breakTimeInterval)//shift + 1
                eta += timedelta(seconds = b * rest)
                breakTimeInterval += b * shift
            if ((wholeDuration >= shiftInterval) | (drvduration >= drivingtime)):
                d = max((wholeDuration - shiftInterval)//shift + 1, (drvduration - drivingtime)//drivingtime + 1)
                eta += timedelta(seconds = d * recharge)
                shiftInterval += d * shift
                c += d
        else:
            ata = df.iloc[i+1, 2]
            arrTime = eta + timedelta(seconds = df.iloc[i, 4] + drvduration)
            wholeDuration = (arrTime - startTime).total_seconds() - (c-1) * recharge
            if wholeDuration >= breakTimeInterval:
                b = (wholeDuration - breakTimeInterval)//shift + 1
                arrTime += timedelta(seconds = b * rest)
                breakTimeInterval += b * shift
            if ((wholeDuration >= shiftInterval) | (drvduration >= drivingtime)):
                d = max((wholeDuration - shiftInterval)//shift + 1, (drvduration - drivingtime)//drivingtime + 1)
                arrTime += timedelta(seconds = d * recharge)
                shiftInterval += d * shift
                c += d
            if arrTime >= ata:
                eta = arrTime
            else:
                arrTimeDur = (arrTime - startTime).total_seconds() - (c-1) * recharge
                ataDur = (ata - startTime).total_seconds() - (c-1) * recharge
                if arrTimeDur <= shiftInterval <= ataDur:
                    remainder = ataDur - shiftInterval
                    if remainder <= recharge:
                        eta = startTime + timedelta(seconds = shiftInterval + c * recharge)
                        shiftInterval += shift
                        c += 1
                    else:
                        eta = startTime + timedelta(seconds = shiftInterval + c * recharge)
                        shiftInterval += shift
                        c += 1
                        remainder = (ata - eta).total_seconds()
                        while remainder >= shift:
                            eta += timedelta(seconds = shift + recharge)
                            shiftInterval += shift
                            c += 1
                            remainder = (ata - eta).total_seconds()
                            if remainder < 0:
                                break
                        else:
                            eta = ata
                elif ataDur < shiftInterval:
                    eta = ata
                wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
                if wholeDuration >= breakTimeInterval:
                    b = (wholeDuration - breakTimeInterval)//shift + 1
                    breakTimeInterval += b * shift
        if eta + timedelta(seconds = df.iloc[i+1, 4]) > df.iloc[i+1, 3]:
            #return False
            print({i: 'Departure over time'})
        #else:
        ETA.append(eta)
    if returned == 0:
        drvduration = jsonResponse['routes'][0]['legs'][-1]['duration']
        TotalDrvduration += drvduration
        eta += timedelta(seconds = df.iloc[-2][4] + drvduration)
        wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
        if ((wholeDuration >= shiftInterval) | (drvduration >= drivingtime)):
            d = max((wholeDuration - shiftInterval)//shift + 1, (drvduration - drivingtime)//drivingtime + 1)
            eta += timedelta(seconds = d * recharge)
            shiftInterval += d * shift
            c += d
        if wholeDuration >= breakTimeInterval:
            b = (wholeDuration - breakTimeInterval)//shift + 1
            eta += timedelta(seconds = b * rest)
            breakTimeInterval += b * shift
        returnDayDepotWorkingHourFrom = pd.to_datetime(str(eta.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[eta.date().weekday()]['from']).time()))
        returnDayDepotWorkingHourTo = pd.to_datetime(str(eta.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[eta.date().weekday()]['to']).time())) 
        if returnDayDepotWorkingHourFrom >= returnDayDepotWorkingHourTo:
            returnDayDepotWorkingHourTo += timedelta(days = 1)
        if eta < returnDayDepotWorkingHourFrom:
            eta = returnDayDepotWorkingHourFrom
        elif eta > returnDayDepotWorkingHourTo:
            eta = returnDayDepotWorkingHourFrom + timedelta(days = 1)
        ETA.append(eta)
    else:
        eta += timedelta(seconds = df.iloc[-2][4])
    wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
    if wholeDuration > max_shift:
        #return False
        print('False max shift')
    totalLoadDuration = eta - startTime
    return ETA, totalLoadDuration, TotalDrvduration


# In[ ]:


finalResults = vrpTimeCalculations()


# In[ ]:


eta_ = [] 
if finalResults == False:
    print("The Route is Infeasible because of Insufficient Time Windows")
else:
    eta_ = [i for i in finalResults[0]]
    ETAs = pd.DataFrame(eta_, columns = ['ETA'])
    for i in range(len(ETAs)):
        ETAs['ETA'][i] += timedelta(hours = -4)
    print(ETAs)
    print("Total Route Duration:  " + str(finalResults[1]))
    print('TotalDrvduration: ',  str(int(math.modf(finalResults[2]/3600)[1])) + ':' + str(int(math.modf(finalResults[2]/3600)[0]*60)))


# In[ ]:




