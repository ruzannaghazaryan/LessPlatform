
daily_driving_time = 11*3600   #11-Hour Driving Limit (in seconds)

# shift, break_time, rest, recharge, max_shift - These variables are the same variables that we have in SQL "shifts" table.

# returned (1 or 0) - get its value from autoplan information to know if the route is non_return (1) or returned (0).

# depotWorkingHours - get json of 'workinghours' of the corresponding depot from 'depos' table.




def getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule():
    ETA = []  #a list where will be collected startTime of the load and ETA of each node in the load
    ETA.append(startTime) #appending to a list start time of the load
    aleph = 1 #coefficient of driving time (11 hours)
    alpha = 1 #coefficient of working time (14 hours)
    c = 1     #coefficient of recharge (10 hours) 
    drvduration = Duration Between Depot and First Node #drvduration Variable includes only driving time
    wholeDuration = 0 #This variable is calculated for each node in the load. It shows how many working hours it takes to get to the current node (it includes driving time, service time as well as waiting time)
    arrTime = 0       #Delivery Time From of the node
    eta = 0           #Estimated time of Arrival of each node
    breakTimeInterval = break_time #shows the interval of hours after which the driver must have a break (rest)
    totalRouteDuration = 0 #(in seconds), this variable must not exceed max_shift in order the load to be feasible
    returnDayDepotWorkingHourFrom = 0 #working hour from of the corresponding depot for the day when the driver returns to depot (check if that day is monday, tuesday, etc. and get workinghour 'from' for that day of week from json)
    returnDayDepotWorkingHourTo = 0   #working hour to of the corresponding depot for the day when the driver returns to depot (check if that day is monday, tuesday, etc. and get workinghour 'to' for that day of week from json)
    totalLoadDuration = 0             #not in seconds, but as time interval (ex: 03:31)
    # The Below Part of the Code calculates only the ETA of the First Node
    if startTime + drvduration >= Delivery Time From of the First Node:
        eta = startTime + drvduration
        if drvduration >= aleph * daily_driving_time:
            eta += rest + recharge
            breakTimeInterval += daily_driving_time #how many hours later the next break must be taken
            aleph = math.ceil(drvduration/daily_driving_time)
            alpha = math.ceil(drvduration/daily_driving_time)
            c += 1  #shows the interval of hours after which driving/working limit is reached and the driver must be off duty for another 10 consecutive hours before driving the truck again
        elif drvduration >= break_time:
            eta += rest #if the break_time interval is reached, then the driver must take a rest (have a break)
            breakTimeInterval += shift  
    else:
        eta = Delivery Time From of the First Node
        wholeDuration = eta - startTime #the duration between Delivery Time From of the First Node and the startTime of the load
        if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
            eta = max(startTime + drvduration + rest + recharge, Delivery Time From of the First Node)
            c += 1
            breakTimeInterval += shift
            aleph = math.ceil(drvduration/daily_driving_time)
            alpha = math.ceil(wholeDuration/shift)
            if aleph < alpha:
                aleph = alpha
        elif wholeDuration >= break_time:
            eta = max(startTime + drvduration + rest, Delivery Time From of the First Node)
            breakTimeInterval += shift
    if eta + service time of the first node > Delivery Time To of the First Node:
        return False
    else:
        ETA.append(eta)
    #Here ends the calculation of the ETA of the First Node and starts the calculation of the following nodes (from 2nd,...)
    for each order in the load: #for i in range(1, order's count) _ in addition I would like to say that depots are not considered as orders 
    # <=> i = 1 will be taken the distance between the 1st Node and 2nd Node, ..., 
    # i = (order's count - 1) will be taken the distance between the penultimate order and the last order (here 'last order - depot' calculation is not considered)
        drvduration += the Duration between the i Node and i+1 Node
        if (eta + (the Duration between the i Node and i+1 Node) + Service Time of the i Node) >= Delivery Time From of the i+1 Node:
            eta += (the Duration between the i Node and i+1 Node) + Service Time of the i Node)
            wholeDuration = eta - startTime - (c-1) * recharge
            if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
                eta += recharge 
                aleph = math.ceil(drvduration/daily_driving_time)
                alpha = math.ceil(wholeDuration/shift)
                if aleph < alpha:
                    aleph = alpha 
                c += 1
            if wholeDuration >= breakTimeInterval:
                eta += rest
                breakTimeInterval += shift           
        else:
            arrTime = Delivery Time From of the (i+1) Node
            wholeDuration = arrTime - startTime - (c-1) * recharge
            if wholeDuration >= breakTimeInterval:
                eta = max(eta + rest, Delivery Time From of the (i+1) Node)
                breakTimeInterval += shift
            if wholeDuration >= alpha * shift or drvduration >= aleph * daily_driving_time:
                eta = max((eta + (the Duration between the i Node and i+1 Node) + Service Time of the i Node + recharge), (arrTime), (startTime + alpha*shift + c*recharge)))
                aleph = math.ceil(drvduration/daily_driving_time)
                alpha = math.ceil(wholeDuration/shift)
                if aleph < alpha:
                    aleph = alpha
                c += 1 
            else:
                eta = arrTime
        if eta + service time of i+1 node > Delivery Date To of i+1 Node:
            return False
        else:
            ETA.append(eta)
    if returned == 0:
        eta += service time of the last order + the Duration between the last order and depot
        returnDayDepotWorkingHourFrom = get datetime by the following way <=> eta.date() _this will be date of datetime and to get time of datetime do <=> depotWorkingHours[eta.date().weekday()]['from']).time() #pd.to_datetime(str(eta.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[eta.date().weekday()]['from']).time()))
        returnDayDepotWorkingHourTo = get datetime by the following way <=> eta.date() _this will be date of datetime and to get time of datetime do <=> depotWorkingHours[eta.date().weekday()]['to']).time() #pd.to_datetime(str(eta.date()) + ' ' + str(pd.to_datetime(depotWorkingHours[eta.date().weekday()]['to']).time())) 
        if returnDayDepotWorkingHourFrom >= returnDayDepotWorkingHourTo:
            returnDayDepotWorkingHourTo += timedelta(days = 1) #add 1 day to returnDayDepotWorkingHourTo
        if eta > returnDayDepotWorkingHourTo:
            return False
        else:
            ETA.append(eta)
            totalRouteDuration = eta - startTime - (c-1) * recharge
    else:
        eta += service time of the last order
        totalRouteDuration = eta - startTime - (c-1) * recharge
    if totalRouteDuration > max_shift:
        return False
    else:
        totalLoadDuration = eta - startTime
    return ETA, totalLoadDuration






eta_ = []   
if getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule() == False:
    print("The Route is Infeasible because of Insufficient Time Windows")
else:
    eta_ = [i for i in getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule()[0]]
    ETAs = pd.DataFrame(eta_, columns = ['ETA'])
    for i in range(len(ETAs)):
        ETAs['ETA'][i] += timedelta(hours = -4)
    print(ETAs)
    print("Total Route Duration:  " + str(getTotalRouteDurationWithServiceAndWaitingTimeWeeklySchedule()[1]))