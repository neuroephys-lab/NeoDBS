import DataHandling as DH
import dearpygui.dearpygui as dpg
import Features as ft
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import spectrogram
from datetime import datetime

'''
BASE

dpg.create_context()
with dpg.window():

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

# # file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"
file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
# # file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"

'''

file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

Data = DH.getData(file)

print(datetime.fromtimestamp(1731086848.0))
print(datetime.fromtimestamp(1731321984.0))
    

dpg.create_context()

tab_label = "this"

signals,labels,colors = [],[],[]

# Generate a test signal: sum of two sine waves
fs = 250  # sampling frequency (Hz)
# t = np.linspace(0, 15, 2 * fs, endpoint=False)
# signal = np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 102 * t)
# signal = 0.5 * np.sin(2 * np.pi * 101 * t)


signal_info = DH.getSignals(Data,'Streaming')[:1]

for stream in signal_info:

    signal = np.array(stream['Y'])
    # Compute spectrogram
    t = np.array(stream['X'])
    f, t_spec, Sxx = spectrogram(signal, fs=fs)

    signals.append([f, t_spec, Sxx])

num_plots = len(signals)
num_cols = 2
num_rows = (num_plots + 1) // num_cols 
limits = []
ploted_signals, labels = [],  []

def exp(sender,app_data,user_data):
    info,type = user_data
    ft.export_plot(info,type)
    

with dpg.window():
    with dpg.group(horizontal=True, parent=f"{tab_label}", tag=f"{tab_label}_plot_group"):

        dpg.add_colormap_scale(tag=f"{tab_label}_colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Jet,
                                            height=400*num_rows)
        
        with dpg.subplots(rows=num_rows, columns=num_cols, label="Spectrograms", width=800, height=400*num_rows, tag=f"{tab_label}_subplots"):
            for _,signal in enumerate(signals):
                frequencies, times, Sxx = signal
                Sxx_log = 10 * np.log10(Sxx + 1e-10)  # Convert to dB scale
                ploted_signals.append([frequencies, times,Sxx_log])
                plot_tag = f"{tab_label}_{_}"
                with dpg.plot(label='Spectrogram', width=-1, height=-1, tag = plot_tag):
                    dpg.add_plot_legend()
                    x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                    y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")
                    Sxx_log = np.flipud(Sxx_log)
                    t = dpg.add_heat_series(Sxx_log.flatten(), rows=Sxx.shape[0], cols=Sxx.shape[1],
                                            scale_min=np.min(Sxx_log), scale_max=np.max(Sxx_log), 
                                            parent=y_axis, format="", bounds_min=[0,0], bounds_max=[times[-1],125])
                                         
                    dpg.bind_colormap(plot_tag, dpg.mvPlotColormap_Jet)
                    config = dpg.get_item_configuration(t)
                    mins = config.get('bounds_min')
                    maxs = config.get('bounds_max')
                    xlim = [mins[0],maxs[0]]
                    ylim = [mins[1],maxs[1]]
                    density = [config.get('scale_min'),config.get('scale_max')]
                    limits.append([xlim,ylim,density])
                    labels.append('Spectrogram')
                    # plot_limits = [dpg.get_axis_limits(t) for t in [x_axis,y_axis]]
                    # plot_limits.append([np.min(Sxx_log),np.max(Sxx_log)])
                    # limits.append(plot_limits)
                    # print(dpg.get_item_configuration(t))

            

            title = dpg.get_item_label(plot_tag)
            axis_labels = [dpg.get_item_label(x_axis),dpg.get_item_label(y_axis), dpg.get_item_label(f"{tab_label}_colormap_scale")]
            colors = []

            info = ploted_signals,labels,colors,title,axis_labels, limits
    dpg.add_button(label='Save',callback=exp,user_data=(info,'3D'),parent=tab_label)
            

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

