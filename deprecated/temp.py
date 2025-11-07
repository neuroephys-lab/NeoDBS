'''import DataHandling as DH
import dearpygui.dearpygui as dpg
import Features as ft
import numpy as np


file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

Data = DH.getData(file)

dpg.create_context()
signals,labels,colors = [],[],[]
with dpg.window():
    with dpg.plot(height=-1,width=-1,tag='plot'):
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
        colormap = 6
        dpg.bind_colormap('plot',colormap)
        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)")
        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="PSD Values")
        for side in [0,1]:
            values = DH.info_electrodes(Data,side=side)['PSD']
            freq,psd = values['SignalFrequencies'], values['SignalPsdValues']
            signals.append({'X':freq,'Y':psd})
            labels.append(values['Channel'])
            c = dpg.add_line_series(freq,psd,label=values['Channel'],parent=y_axis)
            color = dpg.get_colormap_color(colormap,side)
            colors.append(tuple(cl for cl in color))
        
info = signals,labels,colors,'Plot',['Frequency (Hz)','PSD Values']
ft.export_plot(info,'2D')
    

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()


'''

import DataHandling as DH
import dearpygui.dearpygui as dpg
import Features as ft
import numpy as np


file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

Data = DH.getData(file)

# dpg.create_context()
# signals,labels,colors = [],[],[]
# with dpg.window():
#     with dpg.plot(height=-1,width=-1,tag='plot'):
#         dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
#         colormap = 6
#         dpg.bind_colormap('plot',colormap)
#         x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)")
#         y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="PSD Values")
#         for side in [0,1]:
#             values = DH.info_electrodes(Data,side=side)['PSD']
#             freq,psd = values['SignalFrequencies'], values['SignalPsdValues']
#             signals.append({'X':freq,'Y':psd})
#             labels.append(values['Channel'])
#             c = dpg.add_line_series(freq,psd,label=values['Channel'],parent=y_axis)
#             color = dpg.get_colormap_color(colormap,side)
#             colors.append(tuple(cl for cl in color))
        
from scipy.signal import spectrogram

signals = []
# Generate a test signal: sum of two sine waves
fs = 1000  # sampling frequency (Hz)
t = np.linspace(0, 2, 2 * fs, endpoint=False)
signal = np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 250 * t)

# Compute spectrogram
f, t_spec, Sxx = spectrogram(signal, fs=fs)

signals.append([f, t_spec, Sxx])

info = signals,['Signal1'],[],'Spectrogram',['Time (s)','Frequency (Hz)', 'Power (dB)']
ft.export_plot(info,'3D')
    

# dpg.create_viewport(title='Temporario', width=800, height=600)
# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()


