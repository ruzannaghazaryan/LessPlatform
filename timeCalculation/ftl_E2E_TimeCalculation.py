#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd

import math
from datetime import datetime, timedelta

import urllib
import json
import sys

import pymongo
from bson.objectid import ObjectId


# In[2]:


try:
    client = pymongo.MongoClient('mongodb://admin:hello8008there@144.217.38.21:27017')
except:
    print('cannot connect to MongoDB')


# In[ ]:


db = 'FTL'
collection = 'plannings'
loadId = int(sys.argv[1])


# In[3]:


# loadId = int(input())


# In[ ]:


def queryFunctionToGetLoads(coll, loadID):
    myCollection = client[db][coll]
    query = {'ID': loadID}
    result = list()
    try:
        doc = myCollection.find(query)
        for x in doc:
            result.append(x)
        return result
    except:
        print('cannot get data')


# In[ ]:


load = queryFunctionToGetLoads(collection, loadId)
stops = load[0]['stopLocations']


# In[ ]:


stopsCount = 0
for i in range(len(stops)):
    stopsCount += len(stops[i]['actions'])


# In[ ]:


df = pd.DataFrame(columns = ['id', 'lat', 'lon', 'from', 'to', 'serviceTime'], index = range(stopsCount))


# In[ ]:


k = 0
for i in range(len(stops)):
    for j in range(len(stops[i]['actions'])):
        if list(stops[i]['actions'].values())[j] == 0:
            df['from'][k] = stops[i]['datas'][j]['pickupdateFrom'] + timedelta(hours = -4)
            df['to'][k] = stops[i]['datas'][j]['pickupdateTo'] + timedelta(hours = -4)
            df['lat'][k] = stops[i]['datas'][j]['pickupLat']
            df['lon'][k] = stops[i]['datas'][j]['pickupLon']
        else:
            df['from'][k] = stops[i]['datas'][j]['deliverydateFrom'] + timedelta(hours = -4)
            df['to'][k] = stops[i]['datas'][j]['deliverydateTo'] + timedelta(hours = -4)
            df['lat'][k] = stops[i]['datas'][j]['deliveryLat']
            df['lon'][k] = stops[i]['datas'][j]['deliveryLon']
        df['id'][k] = stops[i]['datas'][j]['ID']
        df['serviceTime'][k] = stops[i]['datas'][j]['servicetime']
        k += 1 


# In[ ]:


def getResponseHTTPRequest():
    base_url = 'http://planet.map.lessplatform.com/route/v1/driving/'
    for i in df.index:
        base_url += df['lon'][i] + ',' + df['lat'][i] + ';'
    base_url = base_url[:-1] + '?overview=false&exclude=ferry'
    jsonResult = urllib.request.urlopen(base_url).read()
    response = json.loads(jsonResult)
    return response


# In[ ]:


jsonResponse = getResponseHTTPRequest()


# In[ ]:


totalRouteDistance = jsonResponse['routes'][0]['distance']/1609
print('Total Route Distance is ', str(totalRouteDistance), ' miles')


# In[ ]:


drivingTimeDuration = str(int(math.modf(jsonResponse['routes'][0]['duration']/3600)[1])) + ':' + str(int(math.modf(jsonResponse['routes'][0]['duration']/3600)[0]*60))
print('Total Driving Time (duration) is ', str(drivingTimeDuration))


# In[ ]:


startTime = df['from'][0]


# In[ ]:


def queryFunctionToGetShift():
    myCollection = client[db]['shifts']
    query = {'_id': load[0]['shift']}
    result = list()
    try:
        doc = myCollection.find(query)
        for x in doc:
            result.append(x)
        return result
    except:
        print('cannot get data')


# In[ ]:


shifts = queryFunctionToGetShift()


# In[ ]:


shift = shifts[0]['shift']
break_time = shifts[0]['break_time']
drivingtime = shifts[0]['drivingtime']
max_shift = shifts[0]['max_shift']
rest = shifts[0]['rest']
recharge = shifts[0]['recharge']


# In[ ]:


def queryFunctionToGetDurationMultiplier():
    myCollection = client[db]['jobs']
    query = {'UUID': load[0]['UUID']}
    result = list()
    try:
        doc = myCollection.find(query)
        for x in doc:
            result.append(x)
        return result
    except:
        print('cannot get data')


# In[ ]:


durMult = queryFunctionToGetDurationMultiplier()[0]['params']['DurationMultiplier']


# In[ ]:


def pdpTimeCalculations():
    ETA = []
    arriveTimes = []
    waitingTimes = []
    departTimes = []
    
    ETA.append(startTime)
    arriveTimes.append(startTime)
    waitingTimes.append(0) #in minutes
    departTimes.append(startTime + timedelta(seconds = df['serviceTime'][0]))
    
    c = 1     # _totalRechargeCoeff
    b = 1     # _restCoeff
    # d         _rechargeCoeff
    
    wholeDuration = 0
    drvduration = 0
    totalLoadDuration = 0
    arrTime = 0
    
    eta = startTime
    breakTimeInterval = break_time
    shiftInterval = shift
    
    for i in range(len(jsonResponse['routes'][0]['legs'])):
        drvduration = jsonResponse['routes'][0]['legs'][i]['duration'] * durMult
        if eta + timedelta(seconds = (df['serviceTime'][i] + drvduration)) >= df['from'][i+1]:
            eta += timedelta(seconds = df['serviceTime'][i] + drvduration)
            wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
            if wholeDuration >= breakTimeInterval:
                b = (wholeDuration - breakTimeInterval)//shift + 1
                eta += timedelta(seconds = b * rest)
                breakTimeInterval += b * shift
                wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
            if ((wholeDuration >= shiftInterval) | (drvduration >= drivingtime)):
                d = max((wholeDuration - shiftInterval)//shift + 1, (drvduration - drivingtime)//drivingtime + 1)
                eta += timedelta(seconds = d * recharge)
                shiftInterval += d * shift
                c += d
            arriveTimes.append(eta)
            waitingTimes.append(0)
            departTimes.append(eta + timedelta(seconds = df['serviceTime'][i+1]))
        else:
            ata = df['from'][i+1]
            arrTime = eta + timedelta(seconds = df['serviceTime'][i] + drvduration)
            wholeDuration = (arrTime - startTime).total_seconds() - (c-1) * recharge
            if wholeDuration >= breakTimeInterval:
                b = (wholeDuration - breakTimeInterval)//shift + 1
                arrTime += timedelta(seconds = b * rest)
                breakTimeInterval += b * shift
                wholeDuration = (arrTime - startTime).total_seconds() - (c-1) * recharge
            if ((wholeDuration >= shiftInterval) | (drvduration >= drivingtime)):
                d = max((wholeDuration - shiftInterval)//shift + 1, (drvduration - drivingtime)//drivingtime + 1)
                arrTime += timedelta(seconds = d * recharge)
                shiftInterval += d * shift
                c += d
            arriveTimes.append(arrTime)
            if arrTime >= ata:
                eta = arrTime
                waitingTimes.append(0)
                departTimes.append(eta + timedelta(seconds = df['serviceTime'][i+1]))
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
                waitingTimes.append((eta - arrTime).total_seconds()/60)
                departTimes.append(eta + timedelta(seconds = df['serviceTime'][i+1]))
        if eta + timedelta(seconds = df['serviceTime'][i+1]) > df['to'][i+1]:
            #return False
            print({i: 'Departure over time'})
        #else:
        ETA.append(eta)
    eta += timedelta(seconds = df['serviceTime'][(len(df)-1)])
    wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
    if wholeDuration > max_shift:
        #return False
        print('False max shift')
    totalLoadDuration = eta - startTime
    return ETA, arriveTimes, departTimes, waitingTimes, totalLoadDuration


# In[ ]:


output = pdpTimeCalculations()


# In[ ]:


data = pd.DataFrame(columns = ['eta', 'arrivalTime', 'departureTime', 'waitingTime'])


# In[ ]:


data['eta'] = [i.strftime("%Y-%m-%d %H:%M:%S") for i in output[1]]
data['arrivalTime'] = [i.strftime("%Y-%m-%d %H:%M:%S") for i in output[0]]
data['departureTime'] = [i.strftime("%Y-%m-%d %H:%M:%S") for i in output[2]]
data['waitingTime'] = [i for i in output[3]]


# In[ ]:


print(data)


# In[ ]:


print("Total Route Duration: ", str(output[4]))


# In[8]:


print('______________________________________________________________________________________________________________________')


# ___

# In[ ]:


#print(startTime)


# In[ ]:


# i = int(input())
# str(int(math.modf(df['serviceTime'][i]/3600)[1])) + ':' + str(int(math.modf(df['serviceTime'][i]/3600)[0]*60))


# In[ ]:


# i = int(input())
# print(jsonResponse['routes'][0]['legs'][i]['duration']/60),
# str(int(math.modf(jsonResponse['routes'][0]['legs'][i]['duration']*durMult/3600)[1])) + ':' + str(int(math.modf(jsonResponse['routes'][0]['legs'][i]['duration']*durMult/3600)[0]*60))


# In[ ]:




