#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import mysql.connector


# In[2]:


db = input('input the database you need: ')


# In[3]:


table = input('input the table you need: ')


# In[4]:


mydb = mysql.connector.connect(
                                user = '',
                                host = '',
                                password = '',
                                database = db
                               )


# In[5]:


mycursor = mydb.cursor()


# In[6]:


query = ['SELECT * FROM ' + table,
         'SHOW COLUMNS FROM ' + table]


# In[7]:


result = list()
for i in range(len(query)):    
    try:
        mycursor.execute(query[i])
        result.append(mycursor.fetchall())
    except:
        print("Execute Failed in " + query[i])


# In[8]:


data = pd.DataFrame(result[0], columns = [i[0] for i in result[1]], index = range(len(result[0])))



# In[10]:

print(data.shape)
print('Got the data. You can GO ON. Just run print(data) to see the result.')


# In[ ]:




