import DataHandling as DH
import numpy as np
import dearpygui.dearpygui as dpg
import utils as utl
import matplotlib.pyplot as plt


file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

Data = DH.getData(file)



dpg.create_context()

with dpg.window():
    with dpg.plot(height=-1,width=-1):
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)")
        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="PSD Values")
        for side in [0,1]:
            values = DH.info_electrodes(Data,side=side)['PSD']
            freq,psd = values['SignalFrequencies'], values['SignalPsdValues']
            dpg.add_line_series(freq,psd,label=values['Channel'],parent=y_axis)
        


dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()


