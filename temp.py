import scipy.signal as ss
import Preprocessing as pre
import dearpygui.dearpygui as dpg
import DataHandling as DH
import matplotlib.pyplot as plt
import numpy as np
import Features as ft
''' For feature extraction - get all scipy functions'''

#Spectral analysis
spectral_analysis_functions = ['periodogram','welch','coherence','spectrogram','stft'] 

#phase modulation, coherence (phase amplitude coupling) --> se tiver mais que 1 canal

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"
Data = DH.getData(file_path)
stream = DH.getSignals(Data, 'Streaming')[0]

params = pre.get_required_params('periodogram')

arg = {}
for param, default in params.items():
    match param:
        case 'x': arg[param] =stream['X']
        case 'fs': arg[param] = 250
        case 'window': arg[param] = 'tukey'
        #case 'return_onesided': arg[param] = False
        case _:
            if default:
                print(f"{param}: {default}")
                arg[param] = default
            else:
                pass
            '''
                value = input(f"{param}: ")
                arg[param] = value'''

plt.figure()   

for i in range(10,20):
    arg['nfft'] = i
    func = pre.call_function('periodogram', arg)

    plt.plot(func[0],func[1], label = f"nfft: {i}")
    plt.xlim(0,np.max(func[0]))

psd, freqs  = ft.psd_fft(stream['Y'])
plt.plot(freqs,psd,label="PSD")

plt.legend()  
plt.show()

'''dpg.create_context()

with dpg.window(label="Tutorial"):
    # create plot
    with dpg.plot(label="Line Series", height=400, width=400):
        # optionally create legend
        dpg.add_plot_legend()

        # REQUIRED: create x and y axes
        dpg.add_plot_axis(dpg.mvXAxis, label="x")
        dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")

        dpg.add_line_series(stream['X'], stream['Y'], label  = ' Raw', parent = "y_axis")
        

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()'''