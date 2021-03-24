#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# %load hope.py
#!/usr/bin/env python

# In[ ]:


import pandas as pd
import sys
import mysql.connector
import urllib.request
import json
import math
from datetime import timedelta, datetime


# In[ ]:


load_id = sys.argv[1]
page = str(sys.argv[2])
db = str(sys.argv[3])


# In[ ]:


mydb  = mysql.connector.connect(
                                host = '144.217.38.21',
                                user = 'bf4u',
                                password = 'Zn6+YsUU',
                                database = db
                                )
mycursor = mydb.cursor()


# In[1]:




def getLoadOrders():
    query = "SELECT `orders`, `flowType`, `depoId`, `return`, `startTime`, `shiftId` FROM " + page + " WHERE id = " + load_id
    try:
        mycursor.execute(query)
    except:
        print("Execute Fail")
    result = mycursor.fetchall()[0]
    return result



# In[ ]:


output = getLoadOrders()
#print(output)


# In[ ]:


load_order = output[0].split(',')
load_orders = tuple(int(i) for i in load_order)
flowType = output[1]
depoId = output[2]
returned = output[3]
startTime = output[4]
shiftId = output[5]





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
    except:
        print("Execute Fail")
    results = mycursor.fetchall()
    return results


# In[ ]:


# getLoadOrdersLatLon()


# In[ ]:


df = pd.DataFrame(getLoadOrdersLatLon(), columns = ['id', 'Latitude', 'Longitude', 'TWFrom', "TWTo", "servicetime"])


# In[ ]:


df.index = df['id']


# In[ ]:


df = df.drop(['id'], axis = 1)


# In[ ]:


df


# In[ ]:


def getDepotLatLon():
    query = "SELECT lat, lon, workinghours FROM depos WHERE id = " + str(depoId)
    try:
        mycursor.execute(query)
    except:
        print("Execute Fail")
    resultat = mycursor.fetchall()[0]
    return resultat
    
    


# In[ ]:


DepotLatLon = getDepotLatLon()


# In[ ]:


depotLat = DepotLatLon[0]
depotLon = DepotLatLon[1]
depotWorkingHours = json.loads(DepotLatLon[2])


daysOfWeek = list(depotWorkingHours.keys())
correspondingIntegersToDaysOfWeek = [4, 0, 6, 1, 5, 3, 2]
for i in range(len(daysOfWeek)):
    depotWorkingHours[correspondingIntegersToDaysOfWeek[i]] = depotWorkingHours.pop(daysOfWeek[i])





df.loc['depot'] = [depotLat, depotLon, str(startTime.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[startTime.date().weekday()]['from']).time()), str(startTime.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[startTime.date().weekday()]['to']).time()), 0]
df.loc['depo'] = [depotLat, depotLon, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 0]


# In[ ]:


df['TWFrom'] = pd.to_datetime(df['TWFrom'])
df['TWTo'] = pd.to_datetime(df['TWTo'])


# In[ ]:


new_indices = ['depot'] + [i for i in load_orders] + ['depo']


# In[ ]:


df = df.reindex(new_indices)


# In[ ]:


#if returned == 1:
 #   df = df[:-1]


# In[ ]:


def getResponseHTTPRequest():
    base_url = 'http://planet.map.lessplatform.com/route/v1/driving/' #'http://map.lessplatform.com/route/v1/driving/'
    for i in df.index:
        base_url += df['Longitude'][i] + ',' + df['Latitude'][i] + ';'
    base_url = base_url[:-1] + '?overview=false'
    jsonResult = urllib.request.urlopen(base_url).read()
    response = json.loads(jsonResult)
    return response


# In[ ]:


jsonResponse = getResponseHTTPRequest()
jsonResponse


# In[ ]:

if returned == 0:
    totalRouteDistance = jsonResponse['routes'][0]['distance']/1000
else:
    totalRouteDistance = jsonResponse['routes'][0]['distance']/1000 - jsonResponse['routes'][0]['legs'][-1]['distance']/1000
print("Total Route Distance in km:  " + str(totalRouteDistance))


# In[ ]:

if returned == 0:
    drivingTime = str(int(math.modf(jsonResponse['routes'][0]['duration']/3600)[1])) + ':' + str(int(math.modf(jsonResponse['routes'][0]['duration']/3600)[0]*60))
else:
    drivingTime = str(int(math.modf((jsonResponse['routes'][0]['duration'] - jsonResponse['routes'][0]['legs'][-1]['duration'])/3600)[1])) + ':' + str(int(math.modf((jsonResponse['routes'][0]['duration'] - jsonResponse['routes'][0]['legs'][-1]['duration'])/3600)[0]*60))
print("Driving Time:  " + str(drivingTime))



# In[ ]:



#def getTotalRouteDurationWithServiceAndWaitingTimeDailySchedule():
 #   ETA = []
  #  ETA.append(startTime)
   # eta = max(startTime + timedelta(seconds = jsonResponse['routes'][0]['legs'][0]['duration']), df.iloc[1, 2])
    #ETA.append(eta)
    #for i in range(1, len(jsonResponse['routes'][0]['legs'])):
     #   if (eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]))>= df.iloc[i+1, 2]:
      #      eta += timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4])
       # else:
        #    eta = df.iloc[i+1, 2] 
            
#         eta = max(eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']), df.iloc[i+1, 2]) + timedelta(seconds = df.iloc[i, 4])
        #ETA.append(eta)
    #return(ETA)
    


daily_driving_time = 11*3600   

    
    
# def getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule():
#     ETA = []
#     ETA.append(startTime)
#     aleph = 1
#     t = 1
#     alpha = 1
#     drvduration = jsonResponse['routes'][0]['legs'][0]['duration']
#     wholeDuration = 0
#     eta = startTime + timedelta(seconds = drvduration)
#     if drvduration >= aleph * daily_driving_time:
#         eta = max(startTime + timedelta(seconds = drvduration) + timedelta(seconds = rest) + timedelta(seconds = recharge), df.iloc[1, 2])
#         t = math.ceil(drvduration/break_time)
#         aleph = math.ceil(drvduration/daily_driving_time)
#         alpha = math.ceil(drvduration/daily_driving_time)
#     elif drvduration >= break_time:
#         eta = max(startTime + timedelta(seconds = drvduration) + timedelta(seconds = rest), df.iloc[1, 2])
#         t = math.ceil(drvduration/break_time)
#     ETA.append(eta)
#     for i in range(1, len(jsonResponse['routes'][0]['legs'])):
#         drvduration += jsonResponse['routes'][0]['legs'][i]['duration']
#         eta = max(eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]), df.iloc[i+1, 2])
#         wholeDuration = (eta - startTime).total_seconds()
#         if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
#             eta += timedelta(seconds = rest) + timedelta(seconds = recharge)
#             aleph = math.ceil(drvduration/daily_driving_time)
#             alpha = math.ceil(wholeDuration/shift)
#             t = math.ceil(wholeDuration/break_time)
#         elif wholeDuration >= t * break_time:
#             eta += timedelta(seconds = rest)
#             t = math.ceil(wholeDuration/break_time)
# #         eta = max(eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']), df.iloc[i+1, 2]) + timedelta(seconds = df.iloc[i, 4])
#         ETA.append(eta)
#     return(ETA)
    
    
    
    

#def getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule():
#     ETA = []
#     ETA.append(startTime)
#     aleph = 1
#     t = 1
#     c = 1
#     alpha = 1
#     drvduration = jsonResponse['routes'][0]['legs'][0]['duration']
#     wholeDuration = 0
#     arrTime = 0 
#     eta = startTime + timedelta(seconds = drvduration)
#     if drvduration >= aleph * daily_driving_time:
#         eta = max(startTime + timedelta(seconds = drvduration) + timedelta(seconds = rest) + timedelta(seconds = recharge), df.iloc[1, 2])
#         t = math.ceil(drvduration/break_time)
#         aleph = math.ceil(drvduration/daily_driving_time)
#         alpha = math.ceil(drvduration/daily_driving_time)
#         c += 1
#     elif drvduration >= break_time:
#         eta = max(startTime + timedelta(seconds = drvduration) + timedelta(seconds = rest), df.iloc[1, 2])
#         t = math.ceil(drvduration/break_time)
#     ETA.append(eta)
#     for i in range(1, len(jsonResponse['routes'][0]['legs'])):
#         drvduration += jsonResponse['routes'][0]['legs'][i]['duration']
#         if (eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]) >= df.iloc[i+1, 2]):
#             eta = eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4])
#             wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
#             if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
#                 eta += timedelta(seconds = recharge) 
#                 aleph = math.ceil(drvduration/daily_driving_time)
#                 alpha = math.ceil(wholeDuration/shift)
#                 # t = math.ceil(wholeDuration/break_time)
#                 c += 1
#             elif wholeDuration >= t * break_time:
#                 eta += timedelta(seconds = rest)
#                 t = math.ceil(wholeDuration/break_time)
#         else:
#             arrTime = df.iloc[i+1, 2]
#             wholeDuration = (arrTime - startTime).total_seconds() - (c-1) * recharge
#             if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
#                 if (startTime + timedelta(seconds = alpha*shift + c*recharge) <= arrTime):
#                     eta = arrTime
#                     aleph = math.ceil(drvduration/daily_driving_time)
#                     alpha = math.ceil(wholeDuration/shift)
#                     t = math.ceil(wholeDuration/break_time)
#                     c += 1
#                 else:
#                     eta += timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]) + timedelta(seconds = recharge)
#                     aleph = math.ceil(drvduration/daily_driving_time)
#                     alpha = math.ceil(wholeDuration/shift)
#                     c += 1
#                     if wholeDuration >= t * break_time:
#                         eta += timedelta(seconds = rest)
#                         t = math.ceil(wholeDuration/break_time)
#         ETA.append(eta)
#     return ETA






#def getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule():
#     ETA = []
#     ETA.append(startTime)
#     aleph = 1
#     #t = 1
#     c = 1
#     alpha = 1
#     drvduration = jsonResponse['routes'][0]['legs'][0]['duration']
#     wholeDuration = 0
#     arrTime = 0 
#     breakTimeInterval = break_time
#     eta = startTime + timedelta(seconds = drvduration)
#     if drvduration >= aleph * daily_driving_time:
#         eta = max(startTime + timedelta(seconds = drvduration) + timedelta(seconds = rest) + timedelta(seconds = recharge), df.iloc[1, 2])
#         breakTimeInterval = daily_driving_time + recharge + break_time 
#         # t = math.ceil(drvduration/break_time)
#         aleph = math.ceil(drvduration/daily_driving_time)
#         alpha = math.ceil(drvduration/daily_driving_time)
#         c += 1
#     elif drvduration >= break_time:
#         eta = max(startTime + timedelta(seconds = drvduration) + timedelta(seconds = rest), df.iloc[1, 2])
#         breakTimeInterval = shift + recharge + break_time
#         # t = math.ceil(drvduration/break_time)
#     ETA.append(eta)
#     for i in range(1, len(jsonResponse['routes'][0]['legs'])):
#         drvduration += jsonResponse['routes'][0]['legs'][i]['duration']
#         if (eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]) >= df.iloc[i+1, 2]):
#             eta += timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4])
#             wholeDuration = (eta - startTime).total_seconds() - (c-1) * recharge
#             if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
#                 eta += timedelta(seconds = recharge) 
#                 aleph = math.ceil(drvduration/daily_driving_time)
#                 alpha = math.ceil(wholeDuration/shift)
#                 if aleph < alpha:
#                     aleph = alpha 
#                 # t = math.ceil(wholeDuration/break_time)
#                 c += 1
#             if wholeDuration >= breakTimeInterval:
#                 eta += timedelta(seconds = rest)
#                 breakTimeInterval += (shift - break_time) + recharge + break_time           
#         else:
#             arrTime = df.iloc[i+1, 2]
#             wholeDuration = (arrTime - startTime).total_seconds() - (c-1) * recharge
#             if wholeDuration >= breakTimeInterval:
#                 eta += timedelta(seconds = rest)
#                 breakTimeInterval += (shift - break_time) + recharge + break_time
#             if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
#                 eta = max((eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]) + timedelta(seconds = recharge)), (arrTime), (startTime + timedelta(seconds = alpha*shift + c*recharge)))
#                 #if (startTime + timedelta(seconds = alpha*shift + c*recharge) <= arrTime):
#                     #eta = arrTime
#                 aleph = math.ceil(drvduration/daily_driving_time)
#                 alpha = math.ceil(wholeDuration/shift)
#                 if aleph < alpha:
#                     aleph = alpha
#                     # t = math.ceil(wholeDuration/break_time)
#                 c += 1 
#                 #else:
#                     #eta += timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]) + timedelta(seconds = recharge)
#                     #aleph = math.ceil(drvduration/daily_driving_time)
#                     #alpha = math.ceil(wholeDuration/shift)
#                     #c += 1
#             #if wholeDuration >= breakTimeInterval:
#                 #eta = max(eta + timedelta(seconds = rest), arrTime)
#                 # t = math.ceil(wholeDuration/break_time)
#             #if wholeDuration >= breakTimeInterval:
#                 #breakTimeInterval += (shift - break_time) + recharge + break_time
#         ETA.append(eta)
#     return ETA





def getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule():
    ETA = []
    ETA.append(startTime)
    aleph = 1
    alpha = 1
    c = 1
    drvduration = jsonResponse['routes'][0]['legs'][0]['duration']
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
            breakTimeInterval += daily_driving_time # + recharge 
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
    else:
        ETA.append(eta)
    for i in range(1, len(jsonResponse['routes'][0]['legs']) - 1):
        drvduration += jsonResponse['routes'][0]['legs'][i]['duration']
        if (eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]) >= df.iloc[i+1, 2]):
            eta += timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4])
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
                eta = max((eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]) + timedelta(seconds = recharge)), (arrTime), (startTime + timedelta(seconds = alpha*shift + c*recharge)))
                aleph = math.ceil(drvduration/daily_driving_time)
                alpha = math.ceil(wholeDuration/shift)
                if aleph < alpha:
                    aleph = alpha
                c += 1 
            else:
                eta = arrTime
        if eta + timedelta(seconds = df.iloc[i+1, 4]) > df.iloc[i+1, 3]:
            #return False
            print('False ' + str(i))
        else:
            ETA.append(eta)
    if returned == 0:
        eta += timedelta(seconds = df.iloc[-2][4] + jsonResponse['routes'][0]['legs'][-1]['duration'])
        returnDayDepotWorkingHourFrom = pd.to_datetime(str(eta.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[eta.date().weekday()]['from']).time()))
        returnDayDepotWorkingHourTo = pd.to_datetime(str(eta.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[eta.date().weekday()]['to']).time())) 
        if returnDayDepotWorkingHourFrom >= returnDayDepotWorkingHourTo:
            returnDayDepotWorkingHourTo += timedelta(days = 1)
        if eta > returnDayDepotWorkingHourTo:
            #return False
            print('return 0')
        else:
            ETA.append(eta)
            totalRouteDuration = (eta - startTime).total_seconds() - (c-1) * recharge
    else:
        eta += timedelta(seconds = df.iloc[-2][4])
        totalRouteDuration = (eta - startTime).total_seconds() - (c-1) * recharge
    if totalRouteDuration > max_shift:
        #return False
        print('False max shift')
    else:
        totalLoadDuration = eta - startTime
    return ETA, totalLoadDuration



eta_ = []   
#if shiftId == 1:
#    eta_ = [i for i in getTotalRouteDurationWithServiceAndWaitingTimeDailySchedule()]
#else:
if getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule() == False:
    print("The Route is Infeasible because of Insufficient Time Windows")
else:
    eta_ = [i for i in getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule()[0]]
    ETAs = pd.DataFrame(eta_, columns = ['ETA'])
    for i in range(len(ETAs)):
        ETAs['ETA'][i] += timedelta(hours = 8)#-5)
    print(ETAs)
#    totalRouteDuration = ETAs.iloc[-1, 0] - ETAs.iloc[0, 0]
    print("Total Route Duration:  " + str(getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule()[1]))



#totalRouteDuration = ETAs.iloc[-1, 0] - ETAs.iloc[0, 0]
#if returned == 1:
#    totalRouteDuration += timedelta(seconds = df.iloc[-1][4])

#if shiftId == 1:
#    if totalRouteDuration.total_seconds() >= break_time:
#        totalRouteDuration += timedelta(seconds = rest)
#print("Total Route Duration:  " + str(totalRouteDuration))

#if shiftId != 1:
 #   if totalRouteDuration.total_seconds() >= max_shift:
  #      print('60/70-Hour Limit is VIOLATED')
#else:
 #   if totalRouteDuration.total_seconds() >= max_shift:
  #      print('The 11/14 Hour Truck Driving Rule is VIOLATED')


# In[ ]:





# In[ ]:




