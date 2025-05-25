import numpy as np
import DataHandling as DH
import utils as utl
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
import dearpygui.dearpygui as dpg
import Features as ft

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
file2 = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

Data = DH.getData(file_path)
events = DH.getSignals(Data,'Events')


for e,event in enumerate(events):
    fig1, ax1 = plt.subplots()
    for side in ['Left', 'Right']:
        stream = event[side]
        # ax1.plot(stream['X'],stream['Y'],label = f'{e} - OG')
        # psd = np.array(stream['Y'])*np.array(stream['X'])
        x = np.log10(stream['X'])
        y = np.log10(stream['Y'])
        ax1.plot(x,y,label = f'{e} - Normalized')
    ax1.vlines([np.log10(10)],ymin=-1,ymax=1,linestyles='--')
    ax1.legend()
plt.show()
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