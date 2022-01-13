#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import requests
import json
import pymongo
import sys


# In[2]:


try:
    client = pymongo.MongoClient('mongodb://admin:hello8008there@144.217.38.21:27017')
except:
    print('cannot connect to MongoDB')
    sys.exit()


# In[20]:


db = 'FTL'
# print('Please input loadID:')
# loadId = int(input())


# In[4]:


loadId = int(sys.argv[1])


# In[5]:


def getLoadOrders():
    collection = client[db]['plannings']
    result = list()
    try:
        query = collection.find({'ID': loadId}, 
                                {'stopLocations': 1,
                                 'flowType': 1,
                                 'depo': 1, 
                                 'depotType': 1,
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


stops = output[0]['stopLocations']
flowType = output[0]['flowType']
depotType = output[0]['depotType']


# In[8]:


if not pd.isnull(output[0]['depo']):
    def getDepotLatLon():
        collection = client[db]['depos']
        result = list()
        try:
            query = collection.find({'_id': output[0]['depo']},
                                    {'lat': 1, 
                                     'lon': 1, 
                                     '_id': 0})
            for x in query:
                result.append(x)
            return result
        except:
            print("Execution Failed when getting info from depots")
            sys.exit()


# In[9]:


if not pd.isnull(output[0]['depo']):
    depot = getDepotLatLon()


# In[10]:


stopsCount = 0
for i in range(len(stops)):
    stopsCount += len(stops[i]['actions'])


# In[11]:


seq = [0 if i%2 == 0 else 1 for i in range(stopsCount)]


# In[12]:


df = pd.DataFrame(columns = ['id', 'lat', 'lon', 'p/d'], index = range(stopsCount))


# In[13]:


k = 0
for i in range(len(stops)):
    for j in range(len(stops[i]['actions'])):
        if list(stops[i]['actions'].values())[j] == 0:
            df['lat'][k] = stops[i]['datas'][j]['pickupLat']
            df['lon'][k] = stops[i]['datas'][j]['pickupLon']
            df['p/d'][k] = 0
        else:
            df['lat'][k] = stops[i]['datas'][j]['deliveryLat']
            df['lon'][k] = stops[i]['datas'][j]['deliveryLon']
            df['p/d'][k] = 1
        df['id'][k] = stops[i]['datas'][j]['ID']
        k += 1


# In[14]:


if len(df) == 2:
    print('No deadhead')
    sys.exit()

if list(df['p/d'].values) == seq:
    print('This is E2E TL load')


# In[15]:


if (flowType == 3 and pd.notnull(output[0]['depo'])):
    if depotType == 0:
        for i in range(len(df)):
            if i%2 == 0:
                df['id'][i] = 'depot' + str(i)
                df['lat'][i] = depot[0]['lat']
                df['lon'][i] = depot[0]['lon']
    elif depotType == 1:
        for i in range(len(df)):
            if i%2 != 0:
                df['id'][i] = 'depot' + str(i)
                df['lat'][i] = depot[0]['lat']
                df['lon'][i] = depot[0]['lon']


# In[16]:


def getResponseHTTPRequest():
    base_url = 'http://planet.getflatbeds.com/route/v1/driving/'
    for i in range(1, len(df)-1, 2):
        base_url += df['lon'][i] + ',' + df['lat'][i] + ';' + df['lon'][i+1] + ',' + df['lat'][i+1] + ';'
    base_url = base_url[:-1] + '?overview=false&exclude=ferry'
    #jsonResult = urllib.request.urlopen(base_url).read()
    #response = json.loads(jsonResult)
    jsonResult = requests.get(base_url)
    response = jsonResult.json()
    return response


# In[17]:


jsonResponse = getResponseHTTPRequest()


# In[18]:


deadhead = 0
for i in range(len(jsonResponse['routes'][0]['legs'])):
    if i%2 == 0:
        deadhead += jsonResponse['routes'][0]['legs'][i]['distance']/1609


# In[19]:


print('Deadhead:', deadhead, 'miles')


# In[ ]:




