import numpy as np
import mne
import dearpygui.dearpygui as dpg
import DataHandling as DH

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
Data = DH.getData(file_path)
a = np.array(DH.getSignals(Data, 'Indefinite')[0]['Y'])



sfreq = 250
signal = a[np.newaxis, np.newaxis, :]

# Define parameters for the Morlet wavelet transform
freqs = np.arange(1, 100, 1)  # Frequencies from 1Hz to 50Hz
n_cycles = freqs / 2  # Number of cycles per frequency
tfr = mne.time_frequency.tfr_array_morlet(signal, sfreq=sfreq, freqs=freqs, n_cycles=n_cycles, output='power')   



n_cycles = freqs / 2  # Number of cycles per frequency
tfr = mne.time_frequency.tfr_array_morlet(signal, sfreq=sfreq, freqs=freqs, n_cycles=n_cycles, output='power')

# Normalize power values (0 to 1)
tfr = (tfr - np.min(tfr)) / (np.max(tfr) - np.min(tfr))

# Flip upside down
tfr = np.flipud(tfr[0, 0, :, :])

downsampled_tfr = tfr[::5, ::5]
heatmap_data = downsampled_tfr.flatten().tolist()

# Set up Dear PyGui
dpg.create_context()

global_min = np.min(downsampled_tfr)
global_max = np.max(downsampled_tfr)

with dpg.window(label="Wavelet Transform Heatmap", width=800, height=600):
    with dpg.group(horizontal=True):
        dpg.add_colormap_scale(tag="colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Jet,
                               min_scale=global_min, max_scale=global_max, height=400)

        with dpg.plot(label=f"Spectrogram", width=700, height=500, tag="plot"):
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

            # Add downsampled heatmap series
            dpg.add_heat_series(heatmap_data, rows=downsampled_tfr.shape[0], cols=downsampled_tfr.shape[1], 
                                parent=y_axis, scale_min=0.0, scale_max=1.0, label="Wavelet Power", format="")

            dpg.bind_colormap("plot", dpg.mvPlotColormap_Jet)

dpg.create_viewport(title="FEATURES", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
