import numpy as np
import DataHandling as DH
import utils as utl
import re
from datetime import timedelta, datetime
import dearpygui.dearpygui as dpg
import json

file_path = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
file2 = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

# Data = DH.getData(file_path)
# d2 = DH.getData(file2)

# file = open(file2,'r',encoding='utf-8')
# Data = json.load(file)
# # print(Data['SessionDate'])
# Data = DH.add_utc_conversion_to_dates(Data,DH.extract_time_offset(Data))
# # print(Data['SessionDate'])
Data = DH.getData(file2)
print(DH.getTimelineBand(Data))


