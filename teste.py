import numpy as np
import DataHandling as DH
import json 

file_path = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
file = open(file_path,'r',encoding='utf-8')
raw = json.load(file)
data = DH.getData(file_path)
print(len(raw.keys()))
print(data.keys())