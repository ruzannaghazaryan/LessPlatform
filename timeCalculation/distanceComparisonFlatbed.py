#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pymongo
import json
import numpy as np
import pandas as pd
import urllib
from datetime import datetime, timedelta
import math
import sys


# In[2]:


try:
    client = pymongo.MongoClient('mongodb://admin:hello8008there@144.217.38.21:27017')
except:
    print('cannot connect to MongoDB')


# In[3]:


db = str(sys.argv[1])
collection = 'Plannings'
matchId = str(sys.argv[2])


# In[4]:


# db = 'lessTest'
# collection = 'Plannings'


# In[51]:


# matchId = input()


# In[38]:


from bson.objectid import ObjectId


# In[39]:


def queryFunction(coll, matchID):
    myCollection = client[db][coll]
    query = {'_id': ObjectId(matchID)}
    result = list()
    try:
        doc = myCollection.find(query)
        for x in doc:
            result.append(x)
            return result
    except:
        print('cannot get data')


# In[40]:


orders = queryFunction(collection, matchId)


# In[41]:


if len(orders) != 1:
    print('length of data is not 1')


# In[42]:


df = pd.DataFrame(columns=['lat', 'lon', 'from', 'to', 'serviceTime'], index = range(len(orders[0]['stopLocations'])))


# In[43]:


for i in range(len(orders[0]['stopLocations'])):
    df['lat'][i] = orders[0]['stopLocations'][i]['lat']
    df['lon'][i] = orders[0]['stopLocations'][i]['lon']
#     orderId = orders[0]['stopLocations'][i]['orderId'][0]
#     if ((df['lat'][i] == orders[0]['stopLocations'][i]['orders'][orderId]['order']['start']['lat']) & (df['lon'][i] == orders[0]['stopLocations'][i]['orders'][orderId]['order']['start']['lon'])):
#         df['from'][i] = orders[0]['stopLocations'][i]['orders'][orderId]['order']['start']['timeWindowFrom']
#         df['to'][i] = orders[0]['stopLocations'][i]['orders'][orderId]['order']['start']['timeWindowTo']
#     else:
#         df['from'][i] = orders[0]['stopLocations'][i]['orders'][orderId]['order']['end']['timeWindowFrom']
#         df['to'][i] = orders[0]['stopLocations'][i]['orders'][orderId]['order']['end']['timeWindowTo']
#     df['serviceTime'][i] = orders[0]['stopLocations'][i]['orders'][orderId]['order']['servicetime']


# In[52]:


# df['from'] = pd.to_datetime(df['from']) + timedelta(hours = -4)
# df['to'] = pd.to_datetime(df['to']) + timedelta(hours = -4)


# In[45]:


def getResponseHTTPRequest():
    base_url = 'http://planet.map.lessplatform.com/table/v1/driving/'
    for i in df.index:
        base_url += str(df['lon'][i]) + ',' + str(df['lat'][i]) + ';'
    base_url = base_url[:-1] + '?annotations=distance,duration&generate_hints=false&exclude=ferry'
    jsonResult = urllib.request.urlopen(base_url).read()
    response = json.loads(jsonResult)
    return response


# In[46]:


jsonResponse = getResponseHTTPRequest()


# In[47]:


dist = pd.DataFrame(jsonResponse['distances'], index = df.index, columns=df.index)


# In[48]:


totalRouteDistance = 0.0
for i in range(len(dist)-1):
    totalRouteDistance += dist.iloc[i, i+1]
totalRouteDistance = totalRouteDistance/1609
print("Total Route Distance in miles with matrixRequest:  " + str(totalRouteDistance))


# In[49]:


def getResponseHTTPRequest2():
    base_url = 'http://planet.map.lessplatform.com/route/v1/driving/'
    for i in df.index:
        base_url += str(df['lon'][i]) + ',' + str(df['lat'][i]) + ';'
    base_url = base_url[:-1] + '?overview=false&exclude=ferry'
    jsonResult = urllib.request.urlopen(base_url).read()
    response = json.loads(jsonResult)
    return response


# In[50]:


jsonResponse2 = getResponseHTTPRequest2()
totalRouteDistance2 = jsonResponse2['routes'][0]['distance']/1609
print('Total Route Distance is ' + str(totalRouteDistance) + ' miles')


# In[ ]:




