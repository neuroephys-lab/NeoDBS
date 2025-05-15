import DataHandling as DH
import utils as utl
import dearpygui.dearpygui as dpg
import matplotlib.pyplot as plt
import Preprocessing as pre
import numpy as np


# file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

# file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

# Data= DH.getData(file_path)

# Timeline = DH.getSignals(Data,'Timeline')

# Timeline = DH.correctMissingTimeline(Data,Timeline,'X_missing')
# print('----------------------------------------------------')
# for side in ['Left','Right']: 
#     print(side)
#     for t in Timeline: print(t['Date'], ': ', len(t[side]['Y_missing']))
    
x = [2]
print(np.std(x))