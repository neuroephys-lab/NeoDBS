import numpy as np
import dearpygui.dearpygui as dpg
import DataHandling as DH
import Features as ft

# Example frequency and time data (use your real data here)
time = np.arange(0, 30, 1/250)  # Example time in seconds

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-12-05\\Report_Json_Session_Report_20250212T121745.json"
Data = DH.getData(file_path)
events = DH.getSignals(Data, 'Events')

d,t,a,b,g = [],[],[],[],[]

for event in events:
    delta = ft.mean_power_band(event,[0,3])
    d.append(delta)
    theta = ft.mean_power_band(event,[4,8])
    t.append(theta)
    alpha = ft.mean_power_band(event,[8,12])
    a.append(alpha)
    beta = ft.mean_power_band(event,[12,30])
    b.append(beta)
    gamma = ft.mean_power_band(event,[30,100])
    g.append(gamma)
    print(f"{event['DateInitial']}: d = {delta} | t = {theta} | a = {alpha} | b = {beta} | g = {gamma}")

print(f"MEAN DELTA: {np.mean(d)}")
print(f"MEAN THETA: {np.mean(t)}")
print(f"MEAN ALPHA: {np.mean(a)}")
print(f"MEAN BETA: {np.mean(b)}")
print(f"MEAN GAMMA: {np.mean(g)}")

