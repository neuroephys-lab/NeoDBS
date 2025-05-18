import numpy as np
import DataHandling as DH
import utils as utl
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
import dearpygui.dearpygui as dpg
import json

file_path = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
file2 = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

Data = DH.getData(file_path)
# d2 = DH.getData(file2)

timeline = DH.getSignals(Data,'Timeline')
events = DH.getSignals(Data,'Events')

'''
2024-11-08T17:13:20Z
2024-11-09T08:56:04Z
2024-11-09T08:58:38Z
'''


def getTimelineIndexofEvent(timeline, events):

    index = {}
    flag = False

    

    for idx,e in enumerate(events):
        xe = utl.parse_datetime(e['DateInitial'])

        for j,t in enumerate(timeline):
            xt = t['Left']['X']
            xt = [utl.parse_datetime(x) for x in xt]

            # Loop with enumerate to get index
            for i, x in enumerate(xt):
                if abs(x - xe) < timedelta(minutes=10):
                    index[str(idx)] = [i,j]
                    flag = True
                    break
        if flag==False:
            index[str(idx)] = f'{xe}: Event not present in any Timeline Stream'

    return index

def segmentTimelineEvent(timeline, indexes):
    segments = {}
    for edx, idxs in indexes.items():
        if isinstance(idxs,str):
            print(idxs)
        else:
            x, signal = idxs
            segments[edx] = {}
            for side in ['Left', 'Right']:
                xx = timeline[signal][side]['X'][x-6:x+6]
                yy = timeline[signal][side]['Y'][x-6:x+6]
                segment = {'X': xx, 'Y': yy}
                segments[edx][side] =  segment

    return segments

index = getTimelineIndexofEvent(timeline, events)

segments = segmentTimelineEvent(timeline,index)

plt.figure()
for i,segment in segments.items():
    for side in ['Left', 'Right']:
        x = segment[side]['X']
        y = segment[side]['Y']
        plt.plot(x,y,label = f"{i} - {side}")

plt.legend()
plt.show()