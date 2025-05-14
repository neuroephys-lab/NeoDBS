import DataHandling as DH
import utils as utl
import dearpygui.dearpygui as dpg
import matplotlib.pyplot as plt


file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

Data= DH.getData(file_path)

sense, calibration, artifacts = DH.getSignals(Data,'Setup')

for artifact in artifacts: 
    print(artifact['Artifact'])