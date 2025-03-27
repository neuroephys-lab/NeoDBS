import numpy as np
import dearpygui.dearpygui as dpg
import DataHandling as DH
import Features as ft
import Preprocessing as pre

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
Data = DH.getData(file_path)
s1 = np.array(DH.getSignals(Data, 'Streaming')[0]['Y'])
s2 = np.array(DH.getSignals(Data, 'Streaming')[1]['Y'])
t = np.array(DH.getSignals(Data, 'Streaming')[1]['X'])

params = pre.get_required_params('fftconvolve')

parameters_values = {}
for param, default in params.items():
    if default:
        parameters_values[param] = default
    else:
        parameters_values[param] = None

parameters_values['in1'] = s1
parameters_values['in2'] = s1

print(parameters_values)

auto = pre.call_function('fftconvolve', parameters_values)
auto = [a*100/np.max(auto) for a in auto]

# filter =pre.get_required_params('butter')
# parameters_values = {}
# for param, default in params.items():
#     if default:
#         parameters_values[param] = default
#     else:
#         parameters_values[param] = None
# parameters_values['N'] = 3
# parameters_values['Wn'] = [1.2,2.1]
# parameters_values['fs'] = 250
# parameters_values['btype'] = 'bandstop'
# args = pre.call_function('butter', parameters_values)
# auto = pre.call_function2('filtfilt', *args, auto)


dpg.create_context()    

with dpg.window(label = 'main'):
    with dpg.plot(height=-1,width=-1):
        dpg.add_plot_legend()
        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label = 'Time')
        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power")

        dpg.add_line_series(t, np.ascontiguousarray(auto), label = 'Autocorrelation', parent = y_axis)

dpg.create_viewport()
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()