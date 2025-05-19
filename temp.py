import numpy as np
import DataHandling as DH
import utils as utl
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
import dearpygui.dearpygui as dpg
import json

file_path = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
file2 = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

Data = DH.getData(file2)
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
        key = str(idx) + f"_{e['EventName']}"
        for j,t in enumerate(timeline):
            xt = t['Left']['X']
            xt = [utl.parse_datetime(x) for x in xt]

            # Loop with enumerate to get index
            for i, x in enumerate(xt):
                if abs(x - xe) < timedelta(minutes=10):
                    
                    index[key] = [i,j]
                    flag = True
                    break
        if flag==False:
            index[key] = f'{xe}: Event not present in any Timeline Stream'

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
                #if it axis accepts string we neede to order the signal,
                # in case of dpg, that receives timestamps, it will automatically order the signal because theyre numbers
                if x<6: min,max = 0, 12
                elif x+6 > len(timeline[signal][side]['X']):
                    max = len(timeline[signal][side]['X'])-1
                    min = max-12
                else: min,max =  x-6, x+6

                xx = list(reversed(timeline[signal][side]['X'][min:max])) 
                yy = list(reversed(timeline[signal][side]['Y'][min:max]))

                #for dpg
                # xx = timeline[signal][side]['X'][x-6:x+6]
                # yy = timeline[signal][side]['Y'][x-6:x+6]
                segment = {'X': xx, 'Y': yy}
                segments[edx][side] =  segment

    return segments

print(((722-600)//600)+1)

# index = getTimelineIndexofEvent(timeline, events)

# segments, flags = DH.segmentTimelineEvent(timeline,index)

# plt.figure()
# for idx,item in enumerate(segments.items()):
#     i,segment = item
#     for side in ['Left', 'Right']:
#         x = segment[side]['X']
#         y = segment[side]['Y']
#         x = [utl.extract_time_from_datetime_string(utl.extract_time(utl.parse_datetime(xx))) for xx in x]
#         x = [xx-x[0] for xx in x]
#         if flags[idx] == True:
#             meio = [x[6]]
#             plt.vlines(meio, ymin=min(y), ymax=max(y), label = f"{i} - {side} center")

#         plt.plot(x,y,label = f"{i} - {side}")
#         print(x)
#         print(x[:6])
#         print(x[6:])
# plt.legend()
# plt.show()