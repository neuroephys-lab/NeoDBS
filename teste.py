import numpy as np
import dearpygui.dearpygui as dpg
import DataHandling as DH
from scipy.signal import butter, filtfilt,coherence, hilbert
from scipy.signal.windows import dpss 

# Example polar data
theta = np.linspace(0, 2 * np.pi, 100)
r = 1 + 0.5 * np.sin(4 * theta)

file_path = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
Data = DH.getData(file_path)
signals = DH.getSignals(Data, 'Streaming')

x = signals[0]
y = signals[1]

def compute_phase_amplitude(x, y, fs, phase_band=(4,8), amp_band=(30,100), n_bins=18):
    # Filtra e extrai fase de x
    b1, a1 = butter(3, np.array(phase_band)/(fs/2), btype='band')
    x_phase = filtfilt(b1, a1, x)
    phase_data = np.angle(hilbert(x_phase))

    # Filtra e extrai amp de y
    b2, a2 = butter(3, np.array(amp_band)/(fs/2), btype='band')
    y_amp = filtfilt(b2, a2, y)
    amp_data = np.abs(hilbert(y_amp))

    # Cria bins e centra-os
    edges = np.linspace(-np.pi, np.pi, n_bins+1)
    centers = (edges[:-1] + edges[1:]) / 2
    digitized = np.digitize(phase_data, edges) - 1 #assign each time point to each bin (phase)

    amp_means = np.zeros(n_bins)
    for i in range(n_bins):
        sel = amp_data[digitized==i]
        amp_means[i] = np.mean(sel) if sel.size>0 else 0 #get the mean amp from the binned values

    # Normaliza
    amp_dist = amp_means / np.sum(amp_means + 1e-16)
    entropy = -np.sum(amp_dist * np.log(amp_dist + 1e-16)) #shannon entropy
    mi = (np.log(n_bins) - entropy) / np.log(n_bins) #modulation index


    return mi, centers, amp_means

dpg.create_context()

with dpg.window(label="Polar Plot"):
    with dpg.plot(label="Polar Approximation", height=400, width=400):
        dpg.add_plot_axis(dpg.mvXAxis, label="X", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Y", tag="y_axis")
        dpg.add_line_series(x, y, label="Polar Line", parent="y_axis")

dpg.create_viewport(title='Polar with DPG', width=450, height=450)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
