import numpy as np
import DataHandling as DH
import utils as utl
import re

file_path = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

Data = DH.getData(file_path)

timeline = DH.getSignals(Data, 'Timeline')
events = DH.getSignals(Data,'Events')
inicio, fim = timeline[0]['Date'], timeline[-1]['Date']

print(inicio, ' --> ', fim)
for event in events:
    date = event['DateInitial']
    if inicio <= date <= fim:
        print(event['EventName'])