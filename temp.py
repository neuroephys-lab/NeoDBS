
import Features as ft
import dearpygui.dearpygui as dpg
import DataHandling as DH
import numpy as np
import Preprocessing as pre

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"
Data = DH.getData(file_path)
stream = DH.getSignals(Data, 'Streaming')[0]

#t, signal = ft.wave(frequency=20, sampling_rate=250, duration=10, amplitude=0.2)
signal = np.array(stream['Y'])

#multitaper, freqs = mtf.psd_array_multitaper(signal,250)
parameters = {'x': signal,
              'sfreq': '250'}

params = pre.get_required_params('psd_array_multitaper', module='mtf')


parameters = {}
for name, param in params.items():

    if param == None:
        value = input(f"{name}: ")
    else:
        value = param

    parameters[name] =value

parameters['x'] = signal
parameters['sfreq'] = '250'

print(parameters)


multitaper, freqs = pre.call_function('psd_array_multitaper', param_dict=parameters, module='mtf')

dpg.create_context()

with dpg.window(label="main", width=600, height=500):
    with dpg.plot():
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="PSD", tag="y_axis")

        mask = freqs <=100

        dpg.add_line_series(freqs[mask], multitaper[mask], label='Multitaper', parent="y_axis")
        

    
dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()