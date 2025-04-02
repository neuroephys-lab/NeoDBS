import DataHandling as DH
import utils as utl
import matplotlib.pyplot as plt
from datetime import timedelta

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"
Data = DH.getData(file_path)
streaming = DH.getSignals(Data, 'Streaming')

file = 'streaming_events.txt'

events = utl.read_event_file(file)

events_times = []

plt.figure()
for stream in streaming:
    date = stream['Date']
    x= stream['X']
    y = stream['Y']
    new_time = [date + timedelta(seconds=val) for val in stream['X']]
    
    for event in events:
        hour, minute, type = event
        
        idx = utl.find_closest_index(new_time,hour,minute)
        if idx != None: 
            events_times.append([idx, type])

    plt.plot(new_time,y,label=date)

    if events_times:
        for time, type in events_times:
            print(time," | ", stream['Y'][time])
            plt.vlines(new_time[time],label = type, ymin=-500, ymax=500, colors='red')
        events_times = []

plt.legend()
plt.show()