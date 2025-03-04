import DataHandling as DH
import utils as utl
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

def zscoreRemoval(signal,n):
    '''
    Signal - dict with 'X' and 'Y' keys
    returns:
    1. signal with the removed outliers following the z score method
    2. the removed points
    
    '''
    #maybe only return the mask ?? --> apply the mask in GUI

    x = np.array(signal['X'])
    y = np.array(signal['Y'])
    

    threshold = n*np.std(y)
    mask = np.abs(y-np.mean(y)) < threshold
    
    removed_x = x[~mask]  # Values where mask is False
    removed_y = y[~mask]
    

    filtered_x = x[mask]
    filtered_y = y[mask]
    
    cleaned = {'X': filtered_x.tolist(), 'Y': filtered_y.tolist()}
    removed = {'X': removed_x.tolist(), 'Y': removed_y.tolist()}

    return cleaned, removed  # Convert back to lists if needed

#def MAD based removal
# def wavelet denoising 

def checkMissingData(dictionary):

    '''
    Check missing data in the whole of dictionary, either full json file or just a recording or mode
    Return boolean matrix of missing data and the paths
    '''
    
    GlobalPacketSizes = 0
    Fs = 250

    check = []

    modes = DH.getModes(dictionary)

    for mode in modes:
        if mode== 'Streaming' or mode== 'Indefinite' or mode == 'Survey': #Streaming, Survey
                key_paths = utl.find_key_path(dictionary[mode], 'TicksInMses')

                for path in key_paths:
                    path_parts = utl.parse_path(path)
                    signal = utl.access_by_path(dictionary[mode],path_parts)
                    if 'TicksInMses' in signal.keys() and 'GlobalPacketSizes' in signal.keys() and 'SampleRateInHz' in signal.keys():
                        TickInS = utl.string2numbers(signal['TicksInMses'])
                        GlobalPacketSizes = utl.string2numbers(signal['GlobalPacketSizes'][1:-1]) #take out [ ]
                        Fs = signal['SampleRateInHz']

                        if len(TickInS)!=0:
                            TickInS = (TickInS - TickInS[0])/1000 #convert from ms to s, and start from 0
                            if TickInS[-1]>sum(GlobalPacketSizes)/Fs:
                                #print('WARNING: MISSING PACKETS IN Path: ' + path)
                                check.append(path)
                                Warning(f"Missing packets in {mode}")
                            else: pass                    
                        else: 
                            #print('WARNING: No required keys or data in Path: ' + path)
                            check.append(path)
                            Warning(f"Missing keys or data in {mode}")

                    else: 
                        #print("ERROR: No required keys or data.")
                        check.append(path)
                        Warning(f"Missing keys or data in {mode}")
        
        if mode == 'Timeline':

            key_paths = utl.find_key_path(dictionary[mode],'DateTime')
            new_paths = []
            for path in key_paths: new_paths.append(f"['{mode}']" + path + "['DateTime']")
            
            for i in  range(len(new_paths)-1):
                path1 = utl.parse_path(new_paths[i+1])
                path2 = utl.parse_path(new_paths[i])

                time1 = utl.parse_datetime(utl.access_by_path(dictionary,path1))
                time2 = utl.parse_datetime(utl.access_by_path(dictionary,path2))
                delta = time2-time1
                if delta > timedelta(days=1): 
                    print(time1 , '| ', time2, ' | ', delta)
                    
                minutes = np.round(delta.seconds/60,3)
                remainder = minutes%10
                if minutes >10 and remainder==0: #check if difference in time is bigger than 10 and multiple of ten, meaning lost a packet
                    
                    print(new_paths[i])
                    check.append(new_paths[i])
                    Warning(f"Missing packets in {mode}")

            timelines = DH.getSignals(dictionary,mode)
            for time in timelines:
                date = time['Date']
                path = utl.find_key_path(dictionary,date)

                left = len(time['Left']['X'])
                right = len(time['Right']['X'])
                if left != 144 or right != 144: #24*60/10 = 144 samples per day
                    print('Day not complete')

                    diff = utl.parse_datetime(time['Left']['X'][0]) - utl.parse_datetime(time['Left']['X'][-1])
                    packs = np.round(diff.total_seconds()/600,0)
                    if packs < left:
                        Warning(f'Missing packets in {mode}: {left-packs}')
                        check.append(path)

        if mode == 'Events': print('Still not done')  #check event logs, session date time, and lfpfrequencysnapshots  

    return check