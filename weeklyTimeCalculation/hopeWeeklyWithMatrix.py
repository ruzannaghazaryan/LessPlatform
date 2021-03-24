#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import sys
import mysql.connector
import urllib.request
import json
import math
from datetime import timedelta, datetime


# In[44]:


load_id = sys.argv[1]
page = str(sys.argv[2])
db = str(sys.argv[3])



# In[4]:


mydb  = mysql.connector.connect(
                                host = '144.217.38.21',
                                user = 'bf4u',
                                password = 'Zn6+YsUU',
                                database = db
                                )
mycursor = mydb.cursor()


# In[5]:


def getLoadOrders():
    query = "SELECT `orders`, `flowType`, `depoId`, `return`, `startTime`, `shiftId` FROM " + page + " WHERE id = " + load_id
    try:
        mycursor.execute(query)
    except:
        print("Execute Fail")
    result = mycursor.fetchall()[0]
    return result


# In[6]:


output = getLoadOrders()


# In[7]:


load_order = output[0].split(',')
load_orders = tuple(int(i) for i in load_order)
flowType = output[1]
depoId = output[2]
returned = output[3]
startTime = output[4]
shiftId = output[5]


# In[8]:


def getShifts():
    query = "SELECT `break_time`, `rest`, `shift`, `drivingtime`, `recharge`, `max_shift` FROM shifts WHERE id = " + str(shiftId)
    try:
        mycursor.execute(query)
    except:
        print("Execute Fail")
    resultShift = mycursor.fetchall()[0]
    return resultShift
    
break_time = getShifts()[0]
rest = getShifts()[1]
shift = getShifts()[2]
drivingtime = getShifts()[3]
recharge = getShifts()[4]
max_shift = getShifts()[5]


# In[9]:


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
    except:
        print("Execute Fail")
    results = mycursor.fetchall()
    return results


# In[10]:


df = pd.DataFrame(getLoadOrdersLatLon(), columns = ['id', 'Latitude', 'Longitude', 'TWFrom', "TWTo", "servicetime"])



# In[12]:


df.index = df['id']


# In[13]:


df = df.drop(['id'], axis = 1)


# In[14]:


def getDepotLatLon():
    query = "SELECT lat, lon, workinghours FROM depos WHERE id = " + str(depoId)
    try:
        mycursor.execute(query)
    except:
        print("Execute Fail")
    resultat = mycursor.fetchall()[0]
    return resultat


# In[15]:


DepotLatLon = getDepotLatLon()
depotLat = DepotLatLon[0]
depotLon = DepotLatLon[1]
depotWorkingHours = json.loads(DepotLatLon[2])


# In[16]:


daysOfWeek = list(depotWorkingHours.keys())
correspondingIntegersToDaysOfWeek = [4, 0, 6, 1, 5, 3, 2]
for i in range(len(daysOfWeek)):
    depotWorkingHours[correspondingIntegersToDaysOfWeek[i]] = depotWorkingHours.pop(daysOfWeek[i])


# In[17]:


df.loc['depot'] = [depotLat, depotLon, str(startTime.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[startTime.date().weekday()]['from']).time()), str(startTime.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[startTime.date().weekday()]['to']).time()), 0]
df.loc['depo'] = [depotLat, depotLon, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 0]


# In[19]:


df['TWFrom'] = pd.to_datetime(df['TWFrom'])
df['TWTo'] = pd.to_datetime(df['TWTo'])


# In[20]:


new_indices = ['depot'] + [i for i in load_orders] + ['depo']


# In[21]:


df = df.reindex(new_indices)


# In[24]:


def getResponseHTTPRequest():
    base_url = 'http://map.lessplatform.com/table/v1/driving/'
    for i in df.index:
        base_url += df['Longitude'][i] + ',' + df['Latitude'][i] + ';'
    base_url = base_url[:-1] + '?annotations=distance,duration&generate_hints=false'
    jsonResult = urllib.request.urlopen(base_url).read()
    response = json.loads(jsonResult)
    return response


# In[25]:


jsonResponse = getResponseHTTPRequest()
jsonResponse


# In[38]:


dur = pd.DataFrame(jsonResponse['durations'], index = df.index, columns=df.index)
# dur


# In[33]:


dist = pd.DataFrame(jsonResponse['distances'], index = df.index, columns=df.index)
# dist


# In[41]:


if returned == 1:
    dist.loc[:, 'depo'] = 0.0
#     dur.loc[:, 'depo'] = 0.0


# In[36]:


totalRouteDistance = 0.0
for i in range(len(dist)-1):
    totalRouteDistance += dist.iloc[i, i+1]
totalRouteDistance = totalRouteDistance/1609
print("Total Route Distance in miles:  " + str(totalRouteDistance))


# In[37]:


daily_driving_time = 11*3600   



# In[42]:


def getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule():
    ETA = []
    ETA.append(startTime)
    aleph = 1
    alpha = 1
    c = 1
    drvduration = dur.iloc[0,1]
    wholeDuration = 0
    arrTime = 0 
    eta = 0
    breakTimeInterval = break_time
    totalRouteDuration = 0
    returnDayDepotWorkingHourFrom = 0
    returnDayDepotWorkingHourTo = 0
    totalLoadDuration = 0
    if startTime + timedelta(seconds = drvduration) >= df.iloc[1, 2]:
        eta = startTime + timedelta(seconds = drvduration)
        if drvduration >= aleph * daily_driving_time:
            eta += timedelta(seconds = rest) + timedelta(seconds = recharge)
            breakTimeInterval += (daily_driving_time - break_time) + break_time # + recharge
            aleph = math.ceil(drvduration/daily_driving_time)
            alpha = math.ceil(drvduration/daily_driving_time)
            c += 1
        elif drvduration >= break_time:
            eta += timedelta(seconds = rest)
            breakTimeInterval += shift # + recharge 
    else:
        eta = df.iloc[1, 2]
        wholeDuration = (eta - startTime).total_seconds()
        if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
            eta = max(startTime + timedelta(drvduration) + timedelta(rest) + timedelta(recharge), df.iloc[1, 2])
            c += 1
            breakTimeInterval += shift # + recharge 
            aleph = math.ceil(drvduration/daily_driving_time)
            alpha = math.ceil(wholeDuration/shift)
            if aleph < alpha:
                aleph = alpha
        elif wholeDuration >= break_time:
            eta = max(startTime + timedelta(seconds = drvduration) + timedelta(seconds = rest), df.iloc[1, 2])
            breakTimeInterval += shift # + recharge 
    if eta + timedelta(seconds = df.iloc[1, 4]) > df.iloc[1, 3]:
        #return False
        print('False ' + str(1))
    #else:
    ETA.append(eta)
    for i in range(1, len(dur) - 2):
        drvduration += dur.iloc[i, i+1]
        if (eta + timedelta(seconds = dur.iloc[i, i+1]) + timedelta(seconds = df.iloc[i, 4]) >= df.iloc[i+1, 2]):
            eta += timedelta(seconds = dur.iloc[i, i+1]) + timedelta(seconds = df.iloc[i, 4])
            wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
            if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
                eta += timedelta(seconds = recharge) 
                aleph = math.ceil(drvduration/daily_driving_time)
                alpha = math.ceil(wholeDuration/shift)
                if aleph < alpha:
                    aleph = alpha 
                c += 1
            if wholeDuration >= breakTimeInterval:
                eta += timedelta(seconds = rest)
                breakTimeInterval += shift           
        else:
            arrTime = df.iloc[i+1, 2]
            wholeDuration = (arrTime - startTime).total_seconds() - (c-1) * recharge
            if wholeDuration >= breakTimeInterval:
                eta = max(eta + timedelta(seconds = rest), df.iloc[i+1, 2])
                breakTimeInterval += shift
            if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
                eta = max((eta + timedelta(seconds = dur.iloc[i, i+1]) + timedelta(seconds = df.iloc[i, 4]) + timedelta(seconds = recharge)), (arrTime), (startTime + timedelta(seconds = alpha*shift + c*recharge)))
                aleph = math.ceil(drvduration/daily_driving_time)
                alpha = math.ceil(wholeDuration/shift)
                if aleph < alpha:
                    aleph = alpha
                c += 1 
            else:
                eta = arrTime
        if eta + timedelta(seconds = df.iloc[i+1, 4]) > df.iloc[i+1, 3]:
            #return False
            print('False ' + str(i+1))
#         else:
        ETA.append(eta)
    if returned == 0:
        eta += timedelta(seconds = df.iloc[-2][4] + dur.iloc[len(dur)-2, len(dur)-1])
        returnDayDepotWorkingHourFrom = pd.to_datetime(str(eta.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[eta.date().weekday()]['from']).time()))
        returnDayDepotWorkingHourTo = pd.to_datetime(str(eta.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[eta.date().weekday()]['to']).time())) 
        if returnDayDepotWorkingHourFrom >= returnDayDepotWorkingHourTo:
            returnDayDepotWorkingHourTo += timedelta(days = 1)
        if eta > returnDayDepotWorkingHourTo:
            #return False
            print('False returning depo')
#         else:
        ETA.append(eta)
        totalRouteDuration = (eta - startTime).total_seconds() - (c-1) * recharge
    else:
        eta += timedelta(seconds = df.iloc[-2][4])
        totalRouteDuration = (eta - startTime).total_seconds() - (c-1) * recharge
    if totalRouteDuration > max_shift:
        #return False
        print('False max shift')
#     else:
    totalLoadDuration = eta - startTime
    return ETA, totalLoadDuration


# In[43]:


eta_ = []   
#if shiftId == 1:
#    eta_ = [i for i in getTotalRouteDurationWithServiceAndWaitingTimeDailySchedule()]
#else:
# if getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule() == False:
#     print("The Route is Infeasible because of Insufficient Time Windows")
# else:
eta_ = [i for i in getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule()[0]]
ETAs = pd.DataFrame(eta_, columns = ['ETA'])
for i in range(len(ETAs)):
    ETAs['ETA'][i] += timedelta(hours = -5)
print(ETAs)
#    totalRouteDuration = ETAs.iloc[-1, 0] - ETAs.iloc[0, 0]
print("Total Route Duration:  " + str(getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule()[1]))






