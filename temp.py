import numpy as np
import scipy.signal as signal
import dearpygui.dearpygui as dpg
import Features as ft  # Ensure this module has ft.wave function
import DataHandling as DH

# Generate a test wave (14 Hz sine wave)
time, wave = ft.wave(frequency=14, sampling_rate=250, duration=5, amplitude=20)
file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"
Data = DH.getData(file_path)
stream = DH.getSignals(Data, 'Streaming')[0]

# Create DPG context
dpg.create_context()

def plot_stft_dpg(signal_data, fs=250, nperseg=256, tab_tag="stft_plot"):
    """
    Computes and plots the Short-Time Fourier Transform (STFT) using Dear PyGui.

    Parameters:
        - signal_data (array): The input signal (e.g., EEG, audio, etc.).
        - fs (int): Sampling frequency of the signal.
        - nperseg (int): Length of each FFT segment.
        - tab_tag (str): Parent tag for the plot in DPG.
    """
    
    # Compute STFT
    f, t, Zxx = signal.stft(signal_data, fs=fs, nperseg=nperseg)
    power = np.abs(Zxx) ** 2  # Convert to power spectrum

    # Normalize power (avoid division by zero)
    power = power / (np.max(power) + 1e-10)  # Normalize to 0-1

    # Flip vertically to match spectrogram format
    power = np.flipud(power)

    # Debugging output
    print(f"STFT Shape: {power.shape}, Max Value: {np.max(power)}")

    # If STFT has no values, exit
    if power.size == 0:
        print("Error: STFT power matrix is empty!")
        return

    # Ensure the parent plot exists
    if not dpg.does_item_exist(f"{tab_tag}_stft_group"):
        with dpg.group(parent=tab_tag, tag=f"{tab_tag}_stft_group"):
            with dpg.plot(label="STFT Spectrogram", height=400, width=600):
                dpg.add_plot_legend()

                # Axes
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"{tab_tag}_stft_x")
                dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)", tag=f"{tab_tag}_stft_y")

                # Use a heatmap instead of an image series
                dpg.add_heat_series(
                    power.tolist(),  # Convert numpy array to list
                    rows=len(f), cols=len(t),  # Define matrix size
                    parent=f"{tab_tag}_stft_y",
                    label="STFT",
                    scale_min=0, scale_max=1  # Normalize color range
                )
    else:
        # Update the existing heatmap
        dpg.delete_item(f"{tab_tag}_stft_y", children_only=True)
        dpg.add_heat_series(
            power.tolist(),
            rows=len(f), cols=len(t),
            parent=f"{tab_tag}_stft_y",
            label="STFT",
            scale_min=0, scale_max=1
        )

# Create GUI Window
tab_tag = "lala"

y = [val for val in stream['Y']]
y = np.array(y)

with dpg.window(label="STFT Spectrogram", tag=tab_tag, width=700, height=500):
    plot_stft_dpg(y)

# DPG Setup
dpg.create_viewport(title='STFT Visualization', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
