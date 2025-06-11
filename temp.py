import DataHandling as DH

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-12-19\\Report_Json_Session_Report_20250212T121933.json"


data = DH.getData(file_path) 
timeline = DH.getSignals(data,'Timeline')

first = timeline[0]
print(first['Date'])
corrected = DH.correctMissingTimeline(data,first)

print(corrected[0])
