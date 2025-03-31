#AUC


import Features as ft
import dearpygui.dearpygui as dpg
import DataHandling as DH
import numpy as np
import Preprocessing as pre
from scipy.signal import square

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"
Data = DH.getData(file_path)
stream = DH.getSignals(Data, 'Streaming')[0]

#t, signal = ft.wave(frequency=20, sampling_rate=250, duration=10, amplitude=0.2)

signal = np.array(stream['Y'])


medtronic = ft.MedtronicPSD(signal)

bands = {
            'Delta': [0,4],
            'Theta': [4,8],
            'Alpha': [8,12],
            'Beta': [12,30],
            'Gamma': [30,100]
        }

dpg.create_context()

with dpg.window(label="main", width=-1, height=-1):
    with dpg.plot( width=-1, height=-1, tag = 'plot'):
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="AUC", tag="y_axis")
        dpg.add_shade_series(medtronic['Frequency'], medtronic['Power'], label='Raw', parent="y_axis")
        i=0

        for function in ['simpson']: #'simpson','trapezoid','cumulative_simpson','cumulative_trapezoid'
            i+=1

            params = pre.get_required_params(function, module='si')
            parameters = {}
            for name, param in params.items():
                if param == None:
                    #value = input(f"{name}: ")
                    value = None
                else:
                    value = param
                parameters[name] =value
            aauc = []
            for _, band in bands.items():
                a, b = band
                freq_array = medtronic['Frequency']
                mask = (freq_array >= a) & (freq_array <= b)
                
                parameters['y'] = medtronic['Power'][mask]
                f = freq_array[mask]

                if len(f) == 0:
                    print(f"Warning: No data in band {band}")
                    continue

                auc = pre.call_function(function, param_dict=parameters, module='si')
                aauc.append(auc)
            mid = []
            
            for b, value in bands.items():
                mid.append(np.mean(value))
            dpg.add_line_series(mid,aauc, label = function,parent="y_axis")
        


    
dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()