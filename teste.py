import DataHandling as DH
import utils as utl
import dearpygui.dearpygui as dpg
import matplotlib.pyplot as plt
import Preprocessing as pre


# file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

file_path = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

Data= DH.getData(file_path)

Timeline = DH.getSignals(Data,'Timeline')

times = reversed(Timeline[0]['Right']['X'])

days = list(Data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())
New_timeline = DH.right_hemisphere(Data, days)['X']

for t,n in zip(times,New_timeline):
    print(f"{t} | {n}")

