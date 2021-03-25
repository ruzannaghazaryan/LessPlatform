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



# In[ ]:


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

load_order = output[0].split(',')
load_orders = tuple(int(i) for i in load_order)
flowType = output[1]
depoId = output[2]
returned = output[3]
startTime = output[4]
shiftId = output[5]


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


df = pd.DataFrame(getLoadOrdersLatLon(), columns = ['id', 'Latitude', 'Longitude', 'TWFrom', "TWTo", "servicetime"])


# In[ ]:


df.index = df['id']


# In[ ]:


df = df.drop(['id'], axis = 1)


# In[ ]:


def getDepotLatLon():
    query = "SELECT lat, lon FROM depos WHERE id = " + str(depoId)
    try:
        mycursor.execute(query)
    except:
        print("Execute Fail")
    resultat = mycursor.fetchall()[0]
    return resultat
    
    


# In[ ]:


DepotLatLon = getDepotLatLon()
DepotLatLon


# In[ ]:


depotLat = DepotLatLon[0]
depotLon = DepotLatLon[1]


# In[ ]:


df.loc['depot'] = [depotLat, depotLon, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 0]
df.loc['depo'] = [depotLat, depotLon, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 0]


# In[ ]:


df['TWFrom'] = pd.to_datetime(df['TWFrom'])
df['TWTo'] = pd.to_datetime(df['TWTo'])


# In[ ]:


new_indices = ['depot'] + [i for i in load_orders] + ['depo']


# In[ ]:


df = df.reindex(new_indices)


# In[ ]:


if returned == 1:
    df = df[:-1]


# In[ ]:


def getResponseHTTPRequest():
    base_url = 'http://map.lessplatform.com/route/v1/driving/'
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


totalRouteDistance = jsonResponse['routes'][0]['distance']/1609
print("Total Route Distance in miles:  " + str(totalRouteDistance))


# In[ ]:


drivingTime = str(int(math.modf(jsonResponse['routes'][0]['duration']/3600)[1])) + ':' + str(int(math.modf(jsonResponse['routes'][0]['duration']/3600)[0]*60))
print("Driving Time:  " + str(drivingTime))


    
# In[ ]:


def getShifts():
    query = "SELECT `break_time`, `rest`, `shift`, `drivingtime`, `recharge` FROM shifts WHERE id = " + str(shiftId)
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







def getTotalRouteDurationWithServiceAndWaitingTime():
	global break_time
	ETA = list()
	ETA.append(startTime)
	dur = 0
	if startTime + timedelta(seconds = jsonResponse['routes'][0]['legs'][0]['duration']) >= df.iloc[1, 2]:
		dur = jsonResponse['routes'][0]['legs'][0]['duration'] 
		if dur >= break_time:
			eta = startTime + timedelta(seconds = jsonResponse['routes'][0]['legs'][0]['duration']) + timedelta(seconds = rest)
			break_time = (shift - break_time) + recharge + break_time
		else:
			eta = startTime + timedelta(seconds = jsonResponse['routes'][0]['legs'][0]['duration'])
	else:
		eta = df.iloc[1, 2]
		dur = (eta - startTime).total_seconds()
		if dur >= break_time:
			if startTime + timedelta(seconds = jsonResponse['routes'][0]['legs'][0]['duration']) + timedelta(seconds = rest) <= df.iloc[1, 2]:
				eta = df.iloc[1, 2]
				break_time = (shift - break_time) + recharge + break_time
			else:
				eta = startTime + timedelta(seconds = jsonResponse['routes'][0]['legs'][0]['duration']) + timedelta(seconds = rest)
				break_time = (shift - break_time) + recharge + break_time
	ETA.append(eta)
	for i in range(1, len(jsonResponse['routes'][0]['legs'])):
		if (eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]))>= df.iloc[i+1, 2]:
			eta += timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4])
			dur = (eta - startTime).total_seconds()
			if dur >= break_time:
				eta += timedelta(seconds = rest)
				break_time = (shift - break_time) + recharge + break_time
		else:
			eta = df.iloc[i+1, 2] 
			dur = (eta - startTime).total_seconds()
			if dur >= break_time:
				if (eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4])) + timedelta(seconds = rest) <= df.iloc[i+1, 2]:
					eta = df.iloc[i+1, 2]
					break_time = (shift - break_time) + recharge + break_time
				else: 
					eta += timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']) + timedelta(seconds = df.iloc[i, 4]) + timedelta(seconds = rest)
            
#         eta = max(eta + timedelta(seconds = jsonResponse['routes'][0]['legs'][i]['duration']), df.iloc[i+1, 2]) + timedelta(seconds = df.iloc[i, 4])
		ETA.append(eta)
	return(ETA)
    
    
    


# In[ ]:


eta_ = [i for i in getTotalRouteDurationWithServiceAndWaitingTime()]


# In[ ]:


ETAs = pd.DataFrame(eta_, columns = ['ETA'])
for i in range(len(ETAs)):
    ETAs['ETA'][i] += timedelta(hours = -5)
print(ETAs)





totalRouteDuration = ETAs.iloc[-1, 0] - ETAs.iloc[0, 0]
if returned == 1:
    totalRouteDuration += timedelta(seconds = df.iloc[-1][4])
print("Total Route Duration:  " + str(totalRouteDuration))


# In[ ]:




