import matplotlib.pyplot as plt
import utils as utl
from datetime import timedelta
import DataHandling as DH

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

Data = DH.getData(file_path)

streaming = DH.getSignals(Data, 'Streaming')

file = 'streaming_events.txt'

events = utl.read_event_file(file)

events_times = []
segments = []

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

            diff = 15*250
            min = idx-diff
            max = idx+diff
            if min<0:
                min = 0
                max = 30*250
            elif max>len(x)-1:
                max=len(x)-1
                min=len(x)-1-30*250
            new_x = x[min:max]
            new_y = y[min:max]
            mid_index = len(new_x) // 2
            x_shift = new_x[mid_index]

            aligned_x = [xi - x_shift for xi in new_x]

            segment = [aligned_x, new_y]
            segments.append(segment)
            plt.plot(*segment,label = f"{type} - {stream['Channel']}")


plt.legend()
plt.show()