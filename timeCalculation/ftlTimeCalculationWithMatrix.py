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
    sys.exit()


# In[3]:


db = sys.argv[1]
loadId = sys.argv[2]


# In[4]:


# db = 'FTL'
# loadId = int(input())


# In[5]:


def getLoadOrders():
    collection = client[db]['plannings']
    result = list()
    try:
        query = collection.find({'ID': int(loadId)}, 
                                {'UUID': 1, 
                                 'flowType': 1, 
                                 'depo': 1, 
                                 'depotType': 1,
                                 'return': 1,
                                 'startTime': 1,
                                 'shift': 1,
                                 'stopLocations': 1,
                                 '_id': 0})
        for x in query:
            result.append(x)
        return result
    except:
        print("Execution Failed when getting load's orders' data")
        sys.exit()


# In[6]:


output = getLoadOrders()


# In[7]:


flowType = output[0]['flowType']
startTime = output[0]['startTime']
returned = output[0]['return']
stops = output[0]['stopLocations']
depotType = output[0]['depotType']


# In[8]:


def queryFunctionToGetDurationMultiplier():
    collection = client[db]['jobs']
    result = list()
    try:
        query = collection.find({'UUID': output[0]['UUID']},
                                {'params.DurationMultiplier': 1,
                                 '_id': 0})
        for x in query:
            result.append(x)
        return result
    except:
        print('cannot get data of Duration Multiplier')
        sys.exit()


# In[9]:


durMult = queryFunctionToGetDurationMultiplier()[0]['params']['DurationMultiplier']


# In[10]:


durMult


# In[11]:


if not pd.isnull(output[0]['depo']):
    def getDepotLatLon():
        collection = client[db]['depos']
        result = list()
        try:
            query = collection.find({'_id': output[0]['depo']},
                                    {'lat': 1, 
                                     'lon': 1, 
                                     'workinghours': 1,
                                     '_id': 0})
            for x in query:
                result.append(x)
            return result
        except:
            print("Execution Failed when getting info from depots")
            sys.exit()


# In[12]:


if not pd.isnull(output[0]['depo']):
    depot = getDepotLatLon()


# In[13]:


shiftElements = ['break_time', 'rest', 'shift', 'drivingtime', 'recharge', 'max_shift']


# In[14]:


def getShifts():
    collection = client[db]['shifts']
    result = list()
    try:
        query = collection.find({'_id': output[0]['shift']},
                                {i: 1 for i in shiftElements})
        for x in query:
            result.append(x)
        return result
    except:
        print("Execution Failed when getting shift")
        sys.exit()


# In[15]:


shiftFoo = getShifts() 


# In[16]:


break_time = shiftFoo[0]['break_time']
rest = shiftFoo[0]['rest']
shift = shiftFoo[0]['shift']
drivingtime = shiftFoo[0]['drivingtime']
recharge = shiftFoo[0]['recharge']
max_shift = shiftFoo[0]['max_shift']


# In[17]:


stopsCount = 0
for i in range(len(stops)):
    stopsCount += len(stops[i]['actions'])


# In[18]:


df = pd.DataFrame(columns = ['id', 'lat', 'lon', 'from', 'to', 'serviceTime'], index = range(stopsCount))


# In[19]:


utcDiff = -4


# In[20]:


startTime = startTime + timedelta(hours = utcDiff)


# In[21]:


k = 0
for i in range(len(stops)):
    for j in range(len(stops[i]['actions'])):
        if list(stops[i]['actions'].values())[j] == 0:
            df['from'][k] = stops[i]['datas'][j]['pickupdateFrom'] + timedelta(hours = utcDiff)
            df['to'][k] = stops[i]['datas'][j]['pickupdateTo'] + timedelta(hours = utcDiff)
            df['lat'][k] = stops[i]['datas'][j]['pickupLat']
            df['lon'][k] = stops[i]['datas'][j]['pickupLon']
        else:
            df['from'][k] = stops[i]['datas'][j]['deliverydateFrom'] + timedelta(hours = utcDiff)
            df['to'][k] = stops[i]['datas'][j]['deliverydateTo'] + timedelta(hours = utcDiff)
            df['lat'][k] = stops[i]['datas'][j]['deliveryLat']
            df['lon'][k] = stops[i]['datas'][j]['deliveryLon']
        df['id'][k] = stops[i]['datas'][j]['ID']
        df['serviceTime'][k] = stops[i]['datas'][j]['servicetime']
        k += 1


# In[22]:


df


# In[23]:


# LP2D _ depotType = 1
# D2E  _ depotType = 0


# In[24]:


if (flowType == 3 and not pd.isnull(output[0]['depo'])):
    if depotType == 0:
        for i in range(len(df)):
            if i%2 == 0:
                df['id'][i] = 'depot' + str(i)
                df['lat'][i] = depot[0]['lat']
                df['lon'][i] = depot[0]['lon']
                df['from'][i] = startTime
                df['to'][i] = startTime + timedelta(weeks = 260.7) #added 5 years
    elif depotType == 1:
        for i in range(len(df)):
            if i%2 != 0:
                df['id'][i] = 'depot' + str(i)
                df['lat'][i] = depot[0]['lat']
                df['lon'][i] = depot[0]['lon']
                df['from'][i] = startTime
                df['to'][i] = startTime + timedelta(weeks = 260.7)


# In[25]:


load_orders = df['id'].values
df.index = load_orders
df = df.drop(['id'], axis = 1)
if flowType != 3:
    df.loc['depot'] = [depot[0]['lat'], depot[0]['lon'], startTime, startTime + timedelta(weeks = 260.7), 0]
    new_indices = ['depot'] + [i for i in load_orders]
    df = df.reindex(new_indices)
    if returned != 1:
        df.loc['depo'] = [depot[0]['lat'], depot[0]['lon'], startTime, startTime + timedelta(weeks = 260.7), 0]


# In[27]:


df['id'] = df.index
df.index = range(len(df))
df = df[['id', 'lat', 'lon', 'from', 'to', 'serviceTime']]


# In[29]:


df


# In[30]:


def getResponseHTTPRequest():
    base_url = 'http://planet.map.lessplatform.com/table/v1/driving/'
    for i in df.index:
        base_url += df['lon'][i] + ',' + df['lat'][i] + ';'
    base_url = base_url[:-1] + '?annotations=distance,duration&generate_hints=false&exclude=ferry'
    jsonResult = urllib.request.urlopen(base_url).read()
    response = json.loads(jsonResult)
    return response


# In[31]:


jsonResponse = getResponseHTTPRequest()


# In[32]:


dur = pd.DataFrame(jsonResponse['durations'], index = df.index, columns=df.index)


# In[33]:


dist = pd.DataFrame(jsonResponse['distances'], index = df.index, columns=df.index)


# In[34]:


totalRouteDistance = 0.0
totalDrivingTime = 0.0
for i in range(len(dist)-1):
    totalRouteDistance += dist.iloc[i, i+1]
    totalDrivingTime += dur.iloc[i, i+1]
totalRouteDistance = totalRouteDistance/1609


# In[35]:


print('Total Route Distance is ', str(totalRouteDistance), ' miles')


# In[36]:


drivingTimeDuration = str(int(math.modf(totalDrivingTime * durMult/3600)[1])) + ':' + str(int(math.modf(totalDrivingTime * durMult/3600)[0]*60))
print('Total Driving Time (duration) is ', str(drivingTimeDuration))


# In[37]:


def vrpTimeCalculations():
    ETA = []
    arriveTimes = []
    waitingTimes = []
    departTimes = []
    
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
    eta = startTime
    ETA.append(eta)
    arriveTimes.append(eta)
    waitingTimes.append(0)
    departTimes.append(eta + timedelta(seconds = df['serviceTime'][0]))
    
    for i in range(len(dur)-1):
        drvduration = dur.iloc[i, i+1] * durMult
        TotalDrvduration += drvduration
        if eta + timedelta(seconds = df['serviceTime'][i] + drvduration) >= df['from'][i+1]:
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
#     if returned == 0:
#         drvduration = jsonResponse['routes'][0]['legs'][-1]['duration']
#         TotalDrvduration += drvduration
#         eta += timedelta(seconds = df.iloc[-2][4] + drvduration)
#         wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
#         if ((wholeDuration >= shiftInterval) | (drvduration >= drivingtime)):
#             d = max((wholeDuration - shiftInterval)//shift + 1, (drvduration - drivingtime)//drivingtime + 1)
#             eta += timedelta(seconds = d * recharge)
#             shiftInterval += d * shift
#             c += d
#         if wholeDuration >= breakTimeInterval:
#             b = (wholeDuration - breakTimeInterval)//shift + 1
#             eta += timedelta(seconds = b * rest)
#             breakTimeInterval += b * shift
#         returnDayDepotWorkingHourFrom = pd.to_datetime(str(eta.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[eta.date().weekday()]['from']).time()))
#         returnDayDepotWorkingHourTo = pd.to_datetime(str(eta.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[eta.date().weekday()]['to']).time())) 
#         if returnDayDepotWorkingHourFrom >= returnDayDepotWorkingHourTo:
#             returnDayDepotWorkingHourTo += timedelta(days = 1)
#         if eta < returnDayDepotWorkingHourFrom:
#             eta = returnDayDepotWorkingHourFrom
#         elif eta > returnDayDepotWorkingHourTo:
#             eta = returnDayDepotWorkingHourFrom + timedelta(days = 1)
#         ETA.append(eta)
#     else:
    eta += timedelta(seconds = df['serviceTime'][len(df)-1])
    wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
    if wholeDuration > max_shift:
        #return False
        print('False max shift')
    totalLoadDuration = eta - startTime
    return ETA, arriveTimes, departTimes, waitingTimes, totalLoadDuration


# In[38]:


def pdpTimeCalculations():
    ETA = []
    arriveTimes = []
    waitingTimes = []
    departTimes = []
    
    wholeDuration = 0
    TotalDrvduration = 0
    drvduration = 0
    totalLoadDuration = 0
    arrTime = 0
    
    c = 1     # _totalRechargeCoeff
    b = 1     # _restCoeff
    # d         _rechargeCoeff
    
    breakTimeInterval = break_time
    shiftInterval = shift
    
    arriveTimes.append(startTime)
    
    if startTime < df['from'][0]:
        eta = df['from'][0]
        wholeDuration = (eta - startTime).total_seconds()
        if wholeDuration >= breakTimeInterval:
            b = (wholeDuration - breakTimeInterval)//shift + 1
            eta += timedelta(seconds = b * rest)
            breakTimeInterval += b * shift
            wholeDuration = (eta - startTime).total_seconds()
        if wholeDuration >= shiftInterval:
            d = (wholeDuration - shiftInterval)//shift + 1
            eta += timedelta(seconds = d * recharge)
            shiftInterval += d * shift
            c += d
    else:
        eta = startTime
    ETA.append(eta)
    waitingTimes.append((eta - startTime).total_seconds()/60) #in minutes
    departTimes.append(eta + timedelta(seconds = df['serviceTime'][0]))
    
    if eta + timedelta(seconds = df['serviceTime'][0]) > df['to'][0]:
            #return False
            print({0: 'Departure over time'})
    
    for i in range(len(dur)-1):
        drvduration = dur.iloc[i, i+1] * durMult
        TotalDrvduration += drvduration
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


# In[39]:


if flowType == 3:
    solution = pdpTimeCalculations()
else:
    solution = vrpTimeCalculations()


# In[40]:


data = pd.DataFrame(columns = ['ID', 'eta', 'arrivalTime', 'departureTime', 'waitingTime'])


# In[41]:


data['ID'] = df['id']
data['eta'] = [i.strftime("%Y-%m-%d %H:%M:%S") for i in solution[1]]
data['arrivalTime'] = [i.strftime("%Y-%m-%d %H:%M:%S") for i in solution[0]]
data['departureTime'] = [i.strftime("%Y-%m-%d %H:%M:%S") for i in solution[2]]
data['waitingTime'] = [i for i in solution[3]]


# In[42]:


data['ID'] = data['ID'].astype(str)


# In[43]:


if (flowType == 3 and not pd.isnull(output[0]['depo'])):
    for i in range(len(data)):
        if 'depot' in data['ID'][i]:
            data = data.drop([i], axis = 0)


# In[44]:


print("Total Route Duration: ", str(solution[4]))


# In[45]:


print(data)


# In[46]:


print('______________________________________________________________________________________________________________________')


# In[48]:


# i = int(input())
# str(int(math.modf(dur.iloc[i, i+1]*durMult/3600)[1])) + ':' + str(int(math.modf(dur.iloc[i, i+1]*durMult/3600)[0]*60))


# In[ ]:




