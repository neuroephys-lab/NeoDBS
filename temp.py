import DataHandling as DH
import dearpygui.dearpygui as dpg
import utils as utl
import numpy as np


# file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

Data = DH.getData(file)
Events = DH.getSignals(Data,'Events')
Z2L = DH.info_electrodes(Data)['PSD']['SignalPsdValues']
Z2R = DH.info_electrodes(Data,side=1)['PSD']['SignalPsdValues']
electrodes = {'Left': Z2L, 'Right': Z2R}

dpg.create_context()
with dpg.window():
    with dpg.plot(height=-1,width=-1,tag='plot'):
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
        colormap = 1
        dpg.bind_colormap('plot',colormap)
        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)")
        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="PSD Values")

        for event in Events:
            for side in ['Left','Right']:
                stream = event[side]
                label = f"{event['EventName']} | {utl.after_point(stream['Channel'])}_{side}"
                new_y = np.array(stream['Y']) - np.array(electrodes[side])
                dpg.add_line_series(stream['X'], new_y,label = label,parent=y_axis)

        
    

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()


