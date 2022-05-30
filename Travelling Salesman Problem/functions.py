#!/usr/bin/env python
# coding: utf-8

# In[2]:


import numpy as np
import pandas as pd
# import mysql.connector
import matplotlib.pyplot as plt
import urllib.request
import json
# import requests
from math import acos, cos, sin, degrees, atan
from IPython.core.debugger import set_trace
from random import randint


# In[3]:


def scatterplotAllPoints(dframe, depot, avg_point):
    plt.figure(figsize=(10, 7))
    plt.axis('equal')
    plt.scatter(dframe['Latitude'], dframe['Longitude'], c = 'b', marker = 'o')
    plt.scatter(depot[0], depot[1], c = 'r', marker = 's', s = 50)
#     plt.scatter(avg_point[0], avg_point[1], c = 'orange', marker='x', s = 100)
#     plt.plot([depot[0], avg_point[0]], [depot[1], avg_point[1]])
    plt.show()




def collectingTwoParts(dframe, avg_point, depot):
    part1 = pd.DataFrame(columns = ['id', 'Latitude', 'Longitude', 'det', 'sign', 'cosPhi', 'a', 'b', 'c', 'sinPhi', 'angle'])
    part2 = pd.DataFrame(columns = ['id', 'Latitude', 'Longitude', 'det', 'sign', 'cosPhi', 'a', 'b', 'c', 'sinPhi', 'angle'])
    
    
    for i in range(1, len(dframe) + 1):
        det = (avg_point[0] - depot[0])*(dframe['Longitude'][i] - depot[1]) - (avg_point[1] - depot[1])*(dframe['Latitude'][i] - depot[0])
        if np.sign(det) == 1:
            part1 = part1.append({'id': dframe['id'][i],
                                  'Latitude': dframe['Latitude'][i],
                                  'Longitude': dframe['Longitude'][i],
                                  'det': det,
                                  'sign': np.sign(det)},
                                ignore_index=True)
        elif np.sign(det) == -1:
            part2 = part2.append({'id': dframe['id'][i],
                                  'Latitude': dframe['Latitude'][i],
                                  'Longitude': dframe['Longitude'][i],
                                  'det': det,
                                  'sign': np.sign(det)},
                                ignore_index=True)
        else:
            print('There is a point on the line.')
            
    dfs = [part1, part2]
    for i in dfs:
        for j in range(len(i)):
            i['a'][j] = np.sqrt((depot[0] - avg_point[0])**2 + (depot[1] - avg_point[1])**2)
            i['b'][j] = np.sqrt((i['Latitude'][j] - depot[0])**2 + (i['Longitude'][j] - depot[1])**2)
            i['c'][j] = np.sqrt((i['Latitude'][j] - avg_point[0])**2 + (i['Longitude'][j] - avg_point[1])**2)
            i['cosPhi'][j] = (i['a'][j]**2 + i['b'][j]**2 - i['c'][j]**2)/(2*i['a'][j]*i['b'][j])
            i['sinPhi'][j] = np.sqrt(1 - i['cosPhi'][j]**2)
            
    return part1, part2
    
    
    
    
    
def plotLeftOrRightPoints(dframe, avg_point, depot):
    for i in range(len(dframe)):
        plt.scatter(dframe['Latitude'][i], dframe['Longitude'][i], c = 'b', marker = 'o')
        plt.annotate(dframe['id'][i], (dframe['Latitude'][i], dframe['Longitude'][i]), (dframe['Latitude'][i], dframe['Longitude'][i]+0.01))
    plt.scatter(depot[0], depot[1], c = 'r', marker = 's', s = 50)
    plt.scatter(avg_point[0], avg_point[1], c = 'orange', marker='x', s = 100)
    plt.plot([depot[0], avg_point[0]], [depot[1], avg_point[1]])
    plt.axis('equal')
    plt.show()
    
    
    



def dataframeForPointsWithBootAngles(dframe, dframeToCheckBelonging):
    indToBeDropped = []
    bootAngle = pd.DataFrame(columns=['id', 'belonging', 'Latitude', 'Longitude', 'proj', 'cosPhi', 'a', 'b', 'c', 'angle', 'coef2'])           
    for i in range(len(dframe)):
        if dframe['angle'][i] > 110:
            indToBeDropped.append(i)
            row = {}
            cols = ['id', 'Latitude', 'Longitude', 'proj', 'cosPhi', 'a', 'b', 'c', 'angle', 'coef2']
            for k in cols:
                row[k] = dframe[k][i]
            if dframe['id'][i] in list(dframeToCheckBelonging['id']):
                row['belonging'] = 'part2'
            else:
                row['belonging'] = 'part1'
            bootAngle = bootAngle.append(row, ignore_index=True)
         
    dframe = dframe.drop(indToBeDropped)
    dframe.index = range(len(dframe))
    return dframe, bootAngle







def ggg(data, dist):
    sequence = []
    angSeq = []
    minCoefIndex = list(data['coef2']).index(data['coef2'].min())
    tek = [data['id'][minCoefIndex]]
    sequence.append(data['id'][minCoefIndex])
    currentAngle = data['angle'][minCoefIndex]
    data = data.drop(minCoefIndex)
    data.index = range(len(data))
    while len(data) > 0:
        currentSeq = []
        for i in range(len(data)):
            if 0.7 * currentAngle <= data['angle'][i] <= 1.3 * currentAngle:
                currentSeq.append(data['id'][i])
        if len(currentSeq) == 1:
            sequence.extend(currentSeq)
            tek.extend(currentSeq)
            currentAngle = data['angle'][list(data['id']).index(currentSeq[0])]
            data = data.drop(list(data['id']).index(currentSeq[0]))
            data.index = range(len(data))
        elif len(currentSeq) > 1:
            distFromDepo = {}
            nodeIndices = {}
            for j in currentSeq:
                distFromDepo[j] = data['b'][list(data['id']).index(j)]
                nodeIndices[j] = list(data['id']).index(j)
            sortedDistFromDepo = list(dict(sorted(distFromDepo.items(), key = lambda x: x[1])).keys())
            reverseSortedDistFromDepo = list(dict(sorted(distFromDepo.items(), key = lambda x: x[1], reverse=True)).keys())
            a = sequence[:]
            b = sequence[:]
            a.extend(sortedDistFromDepo)
            b.extend(reverseSortedDistFromDepo)
            dist_a = dist[0][int(a[0] - 1)]
            dist_b = dist[0][int(b[0] - 1)]
            for l in range(len(a) - 1):
                dist_a += dist[int(a[l] - 1)][int(a[l + 1] - 1)]
                dist_b += dist[int(b[l] - 1)][int(b[l + 1] - 1)]
            if dist_a <= dist_b:
                sequence.extend(sortedDistFromDepo)
                tek.extend(sortedDistFromDepo)
                currentAngle = data['angle'][list(data['id']).index(sortedDistFromDepo[-1])]
            elif dist_a > dist_b:
                sequence.extend(reverseSortedDistFromDepo)
                tek.extend(reverseSortedDistFromDepo)
                currentAngle = data['angle'][list(data['id']).index(reverseSortedDistFromDepo[-1])]
            data = data.drop(list(nodeIndices.values()))
            data.index = range(len(data))
        else:
            currentNode = int(sequence[-1])
            remainedIds = [int(i) for i in data['id']]
            distFromCurrentNode = {}
            for k in remainedIds:
                distFromCurrentNode[k] = dist[currentNode - 1][k - 1]
            sortedDistFromCurrentNode = list(dict(sorted(distFromCurrentNode.items(), key = lambda x: x[1])).keys())
            nextNode = sortedDistFromCurrentNode[0]
            angSeq.append(tek)
            tek = [nextNode]
            sequence.append(nextNode)
            currentAngle = data['angle'][list(data['id']).index(nextNode)]
            data = data.drop(list(data['id']).index(nextNode))
            data.index = range(len(data))
    return sequence, angSeq





def plotLeftOrRightResults(dataframe, resultList, depo, avgPoint):
    
    plt.figure(figsize=(7,5.5))
    
    m = dataframe[dataframe['id'] == resultList[0]].index[0]
    plt.plot([depo[0], dataframe['Latitude'][m]], [depo[1], dataframe['Longitude'][m]], c = 'g')
    
    for i in range(len(resultList) - 1):
        current = dataframe[dataframe['id'] == resultList[i]].index[0]
        nextNode = dataframe[dataframe['id'] == resultList[i+1]].index[0]
        plt.scatter(dataframe['Latitude'][current], dataframe['Longitude'][current], c = 'b', marker = 'o')
        plt.plot([dataframe['Latitude'][current], dataframe['Latitude'][nextNode]],
                 [dataframe['Longitude'][current], dataframe['Longitude'][nextNode]], c = 'g')
        plt.annotate(dataframe['id'][current], (dataframe['Latitude'][current], dataframe['Longitude'][current]), 
                    (dataframe['Latitude'][current]+60, dataframe['Longitude'][current]+10))
    lastNode = dataframe[dataframe['id'] == resultList[-1]].index[0]
    plt.scatter(dataframe['Latitude'][lastNode], dataframe['Longitude'][lastNode], c = 'b', marker = 'o')
    plt.annotate(dataframe['id'][lastNode], (dataframe['Latitude'][lastNode], dataframe['Longitude'][lastNode]), 
                    (dataframe['Latitude'][lastNode]+60, dataframe['Longitude'][lastNode]+10))
    
    plt.scatter(depo[0], depo[1], c = 'r', marker = 's', s = 50)
    plt.scatter(avgPoint[0], avgPoint[1], c = 'orange', marker='x', s = 100)
    plt.plot([depo[0], avgPoint[0]], [depo[1], avgPoint[1]])
    plt.show()
    
    
    
    
    
def calculateDistanceForGivenList(listname, dist):
    distance = 0
    for i in range(len(listname) - 1):
        distance += dist[listname[i] - 1][listname[i + 1] - 1]
    return distance





def getPlot(listname, df, depo, avgPoint):
    plt.figure(figsize=(15, 10))
    
    depoFirst1 = df[df['id'] == listname[1]].index[0]
    depoFirst2 = df[df['id'] == listname[-2]].index[0]
    plt.plot([depo[0], df['Latitude'][depoFirst1]], [depo[1], df['Longitude'][depoFirst1]], c = 'g')
    plt.plot([depo[0], df['Latitude'][depoFirst2]], [depo[1], df['Longitude'][depoFirst2]], c = 'g')
    
    for i in range(1, len(listname) - 2):
        current = df[df['id'] == listname[i]].index[0]
        nextNode = df[df['id'] == listname[i+1]].index[0]
        plt.scatter(df['Latitude'][current], df['Longitude'][current], c = 'b', marker = 'o')
        plt.plot([df['Latitude'][current], df['Latitude'][nextNode]],
                 [df['Longitude'][current], df['Longitude'][nextNode]], c = 'g')
        plt.annotate(df['id'][current], (df['Latitude'][current], df['Longitude'][current]), 
                    (df['Latitude'][current]+60, df['Longitude'][current]+10))
    lastNode1 = df[df['id'] == listname[-2]].index[0]
    plt.scatter(df['Latitude'][lastNode1], df['Longitude'][lastNode1], c = 'b', marker = 'o')
    plt.annotate(df['id'][lastNode1], (df['Latitude'][lastNode1], df['Longitude'][lastNode1]), 
                (df['Latitude'][lastNode1]+60, df['Longitude'][lastNode1]+10))
    
    plt.scatter(depo[0], depo[1], c = 'r', marker = 's', s = 50)
#     plt.scatter(avgPoint[0], avgPoint[1], c = 'orange', marker='x', s = 100)
#     plt.plot([depo[0], avgPoint[0]], [depo[1], avgPoint[1]])
    plt.show()
    
    
    
    
    
    
def swapTwoPoints(listname, dist):
    import functions
    currentList = listname[:]
    distCurrent = functions.calculateDistanceForGivenList(currentList, dist)
    for i in range(1, len(listname) - 2):
        compareList = currentList[:]
        compareList[i], compareList[i + 1] = compareList[i + 1], compareList[i]
        distCompareList = functions.calculateDistanceForGivenList(compareList, dist)
        if distCompareList < distCurrent:
            currentList = compareList
            distCurrent = distCompareList
    return currentList, distCurrent
    
    
    

    
    
    
    
def getPlotWithRemovedPoints(listname, df, depo, avgPoint, removedPoints):
    plt.figure(figsize=(15, 10))
    
    depoFirst1 = df[df['id'] == listname[1]].index[0]
    depoFirst2 = df[df['id'] == listname[-2]].index[0]
    plt.plot([depo[0], df['Latitude'][depoFirst1]], [depo[1], df['Longitude'][depoFirst1]], c = 'g')
    plt.plot([depo[0], df['Latitude'][depoFirst2]], [depo[1], df['Longitude'][depoFirst2]], c = 'g')
    
    for i in range(1, len(listname) - 2):
        current = df[df['id'] == listname[i]].index[0]
        nextNode = df[df['id'] == listname[i+1]].index[0]
        plt.scatter(df['Latitude'][current], df['Longitude'][current], c = 'b', marker = 'o')
        plt.plot([df['Latitude'][current], df['Latitude'][nextNode]],
                 [df['Longitude'][current], df['Longitude'][nextNode]], c = 'g')
        plt.annotate(df['id'][current], (df['Latitude'][current], df['Longitude'][current]), 
                    (df['Latitude'][current]+60, df['Longitude'][current]+10))
    lastNode1 = df[df['id'] == listname[-2]].index[0]
    plt.scatter(df['Latitude'][lastNode1], df['Longitude'][lastNode1], c = 'b', marker = 'o')
    plt.annotate(df['id'][lastNode1], (df['Latitude'][lastNode1], df['Longitude'][lastNode1]), 
                (df['Latitude'][lastNode1]+60, df['Longitude'][lastNode1]+10))
    
    plt.scatter(depo[0], depo[1], c = 'r', marker = 's', s = 50)
    plt.scatter(avgPoint[0], avgPoint[1], c = 'orange', marker='x', s = 100)
    plt.plot([depo[0], avgPoint[0]], [depo[1], avgPoint[1]])
    for l in removedPoints:
        pointInd = df[df['id'] == l].index[0]
        plt.scatter(df['Latitude'][pointInd], df['Longitude'][pointInd], c = 'y', marker = 'X', s = 50)
        plt.annotate(df['id'][pointInd], (df['Latitude'][pointInd], df['Longitude'][pointInd]), 
                    (df['Latitude'][pointInd]+60, df['Longitude'][pointInd]+10))
    plt.show()
    
    
    
    
    
    
    
def distFromDepot(listname, dist):  
    k = {}
    for i in range(len(listname)):
        k[int(listname[i])] = dist[0][int(listname[i]) - 1]
    return k





def removingOutliers(listname):    
    removed = []
    hope = listname[:]
    i = 0
    while i != len(hope) - 2:
        if hope[i+1] < hope[i] and hope[i+2] > hope[i+1]:
            firstDiffPercent = (hope[i] - hope[i+1])/hope[i] * 100
            secondDiffPercent = (hope[i+2] - hope[i+1])/hope[i+1] * 100
            if (firstDiffPercent > 25 or secondDiffPercent > 25):
                removed.append(hope[i+1])
                hope.remove(hope[i+1])
                if i == 0:
                    i = 0
                else:
                    i -= 1
            else:
                i += 1
        else:
            i += 1
    return hope, removed




def addingRemovedPointsToRoute(removedList, remainedList, dist):
    import functions
    remained_ = remainedList[:]
    for i in removedList:
        u = {}
        b = remained_[:]
        d = remained_[:]
        e = remained_[:]
        f = remained_[:]
        for j in remained_:
            u[j] = dist[i - 1][j - 1]
            
        close = list(dict(sorted(u.items(), key = lambda x: x[1])).keys())[0]
        close2 = list(dict(sorted(u.items(), key = lambda x: x[1])).keys())[1]
        findIndexOfClose = remained_.index(close)
        findIndexOfClose2 = remained_.index(close2)
        
        b.insert(findIndexOfClose, i)
        e.insert(findIndexOfClose2, i)
        if functions.calculateDistanceForGivenList(b, dist) <= functions.calculateDistanceForGivenList(e, dist):
            remainedTemp1 = b
        else:
            remainedTemp1 = e
                
        d.insert(findIndexOfClose + 1, i)
        f.insert(findIndexOfClose2 + 1, i)
        if functions.calculateDistanceForGivenList(d, dist) <= functions.calculateDistanceForGivenList(f, dist):
            remainedTemp2 = d
        else:
            remainedTemp2 = f
        
        if functions.calculateDistanceForGivenList(remainedTemp1, dist) <= functions.calculateDistanceForGivenList(remainedTemp2, dist):
            remained_ = remainedTemp1
        else:
            remained_ = remainedTemp2
    return remained_







def addingReverselyRemovedPointsToRoute(removedList, remainedList, dist):
    import functions
    remained_ = remainedList[:]
    for i in removedList[::-1]:
        u = {}
        b = remained_[:]
        d = remained_[:]
        e = remained_[:]
        f = remained_[:]
        for j in remained_:
            u[j] = dist[i - 1][j - 1]
            
        close = list(dict(sorted(u.items(), key = lambda x: x[1])).keys())[0]
        close2 = list(dict(sorted(u.items(), key = lambda x: x[1])).keys())[1]
        findIndexOfClose = remained_.index(close)
        findIndexOfClose2 = remained_.index(close2)
        
        b.insert(findIndexOfClose, i)
        e.insert(findIndexOfClose2, i)
        if functions.calculateDistanceForGivenList(b, dist) <= functions.calculateDistanceForGivenList(e, dist):
            remainedTemp1 = b
        else:
            remainedTemp1 = e
                
        d.insert(findIndexOfClose + 1, i)
        f.insert(findIndexOfClose2 + 1, i)
        if functions.calculateDistanceForGivenList(d, dist) <= functions.calculateDistanceForGivenList(f, dist):
            remainedTemp2 = d
        else:
            remainedTemp2 = f
        
        if functions.calculateDistanceForGivenList(remainedTemp1, dist) <= functions.calculateDistanceForGivenList(remainedTemp2, dist):
            remained_ = remainedTemp1
        else:
            remained_ = remainedTemp2
    return remained_




def swapping(listname, dist):
    import functions
    
    listInd = list(range(len(listname)))
    fixedIndices = [listInd[0], listInd[-1]]
    toBeSwappedIndices = listInd[1:-1]
    optimallySwappedInd = []
    temp = listname[:]
    best = listname[:]
    for i in toBeSwappedIndices:
        for j in toBeSwappedIndices:
            if i != j:
                temp[i], temp[j] = temp[j], temp[i]
                if functions.calculateDistanceForGivenList(temp, dist) < functions.calculateDistanceForGivenList(best, dist):
                    best = temp[:]
                    optimallySwappedInd.clear()
                    optimallySwappedInd.extend([i, j])
#                     print({i: optimallySwappedInd})
                temp[i], temp[j] = temp[j], temp[i]
            else:
                if i == j == toBeSwappedIndices[-1]:
                    if len(optimallySwappedInd) == 0:
                        return best
                    else:
                        fixedIndices.extend(optimallySwappedInd)
                        toBeSwappedIndices = [i for i in listInd if i not in fixedIndices]
                        if len(toBeSwappedIndices) < 2:
                            return best
                        temp = best[:]
    return best
    
    
    
    

    
def getPlotSmall(listname, df, depo, avgPoint):
    plt.figure(figsize=(15, 10))
    
    depoFirst1 = df[df['id'] == listname[1]].index[0]
    depoFirst2 = df[df['id'] == listname[-2]].index[0]
    plt.plot([depo[0], df['Latitude'][depoFirst1]], [depo[1], df['Longitude'][depoFirst1]], c = 'g')
    plt.plot([depo[0], df['Latitude'][depoFirst2]], [depo[1], df['Longitude'][depoFirst2]], c = 'g')
    
    for i in range(1, len(listname) - 2):
        current = df[df['id'] == listname[i]].index[0]
        nextNode = df[df['id'] == listname[i+1]].index[0]
        plt.scatter(df['Latitude'][current], df['Longitude'][current], c = 'b', marker = 'o')
        plt.plot([df['Latitude'][current], df['Latitude'][nextNode]],
                 [df['Longitude'][current], df['Longitude'][nextNode]], c = 'g')
        plt.annotate(df['id'][current], (df['Latitude'][current], df['Longitude'][current]), 
                    (df['Latitude'][current]+.5, df['Longitude'][current]+.5))
    lastNode1 = df[df['id'] == listname[-2]].index[0]
    plt.scatter(df['Latitude'][lastNode1], df['Longitude'][lastNode1], c = 'b', marker = 'o')
    plt.annotate(df['id'][lastNode1], (df['Latitude'][lastNode1], df['Longitude'][lastNode1]), 
                (df['Latitude'][lastNode1]+.5, df['Longitude'][lastNode1]+.5))
    
    plt.scatter(depo[0], depo[1], c = 'r', marker = 's', s = 50)
#     plt.scatter(avgPoint[0], avgPoint[1], c = 'orange', marker='x', s = 100)
#     plt.plot([depo[0], avgPoint[0]], [depo[1], avgPoint[1]])
    plt.show()
    
    
    