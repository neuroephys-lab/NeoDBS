import DataHandling as DH
import numpy as np
import dearpygui.dearpygui as dpg
import utils as utl
import matplotlib.pyplot as plt

file1 = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
file2 = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-22\\Report_Json_Session_Report_20241125T163306.json"



stim1 = DH.getStimulation(DH.getData(file1))
stim2 = DH.getStimulation(DH.getData(file2))

for x in stim2['X']: stim1['X'].append(x)
for y in stim2['Y']: stim1['Y'].append(y)
for y in stim2['Info']: stim1['Info'].append(y)

infos = stim1['Info']


dpg.create_context()

with dpg.window():
    with dpg.plot():
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", scale = dpg.mvPlotScale_Time) #tag=f"{tab_label}_x_axis"
        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Stimulation Amplitude (mA)")
        x = [utl.parse_datetime(x).timestamp() for x in stim1['X']]
        dpg.add_line_series(x,stim1['Y'],parent=y_axis)
    with dpg.child_window():
        for info in infos:
            dpg.add_text(info)


dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()


