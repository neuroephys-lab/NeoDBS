import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import cwt, morlet
import DataHandling as DH



# Signal parameters
fs = 250 
file2 = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
Data = DH.getData(file2)
signal = DH.getSignals(Data,'Streaming')[0]['Y']

# Wavelet parameters
widths = np.arange(1, 31)  # Array of widths for the wavelet (scales)

# Calculate the CWT using the Morlet wavelet
cwtm = cwt(signal, morlet, widths)
cwtm_mag = np.abs(cwtm)
# Avoid log(0) by adding a small epsilon
cwtm_db = 10 * np.log10(cwtm_mag + 1e-10)
morlet_f_c = 0.8125

'''The value 0.8125 (or sometimes cited as slightly different values close to this) is an empirically determined or documented value that represents the approximate center frequency \(f_c\) of the Morlet wavelet in scipy when the default w parameter is used. It's the frequency where the wavelet's energy is maximally concentrated in the frequency domain for that specific w value.
'''
# Calculate the frequencies corresponding to the widths (scales)
# f = fc / (s * dt) = fc * fs / s
frequencies = (morlet_f_c * fs/2) / widths

# Plot the original signal and the CWT
plt.figure(figsize=(10, 6))

plt.subplot(3, 1, 1)
plt.plot(np.arange(0,len(signal)/fs,1/fs), signal)
plt.title("Original")
plt.xlabel("Time [s]")
plt.ylabel("Amplitude")

plt.subplot(3, 1, 2)
plt.imshow(cwtm_db, extent=[0, len(signal)/fs, frequencies[0], frequencies[-1]], aspect='auto', cmap='viridis')
plt.title("Continuous Morlet Wavelet Transform (dB)")
plt.xlabel("Time [s]")
plt.ylabel("Frequency [Hz]") # Updated label
plt.colorbar(label="Magnitude (dB)")
plt.gca().invert_yaxis() # Invert the y-axis so higher frequencies are at the top


freqs_mne = np.arange(1, 31)  # Frequencies like in MNE
n_cycles_mne = 7.0  # n_cycles like in MNE
scales_scipy = (n_cycles_mne * fs) / (2 * np.pi * (freqs_mne + 1e-10))
cwt_scipy = cwt(signal, morlet, widths)
cwt_scipy_mag = np.abs(cwt_scipy)
cwt_scipy_db = 10 * np.log10(cwt_scipy_mag + 1e-10)
plt.subplot(3, 1, 3)
plt.imshow(cwt_scipy_db, extent=[0, len(signal)/fs,  frequencies[0], frequencies[-1]], aspect='auto', cmap='viridis')
plt.title("CWT approximating MNE (dB) with frequencies from n_cycles")
plt.xlabel("Time [s]")
plt.ylabel("Frequency [Hz]")
plt.colorbar(label="Magnitude (dB)")
plt.gca().invert_yaxis() # Invert the y-axis so higher frequencies are at the top

plt.tight_layout()
plt.show()
