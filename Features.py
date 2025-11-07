import numpy as np
import matplotlib.pyplot as plt
#from spectrum import pyule

bands = {
            'Delta': [0.1,4],
            'Theta': [4,8],
            'Alpha': [8,12],
            'Beta': [12,30],
            'Gamma': [30,100]
        }

def peak_power(stream):
    '''
    Receives a stream with PSD values
    '''
    if 'X' in stream.keys():
        f = 'X'
        p = 'Y'
    elif 'Frequency'in stream.keys():
        f = 'Frequency'
        p = 'Power'

    if len(stream[p]) > 0:

        peak_idx = np.argmax(stream[p])
        peak_f = stream[f][peak_idx]
        peak_power = stream[p][peak_idx]

        return (peak_power, peak_f)
    else: return (0, 0)

def peak_per_band(stream, bands):
    temp = {}
    peaks = {}
    if 'X' in stream.keys():
        f = 'X'
        p = 'Y'
    elif 'Frequency'in stream.keys():
        f = 'Frequency'
        p = 'Power'

    for _, band in bands.items():
        a,b = band
        freq_array = np.array(stream[f])
        mask = (freq_array >= a) & (freq_array <= b)
        power = np.array(stream[p])[mask]
        temp[p] = power
        temp[f] = freq_array[mask]
        
        peaks[_] = peak_power(temp)

    return peaks

def std_dev_band(stream, band):

    if 'X' in stream.keys():
        f = 'X'
        p = 'Y'
    elif 'Frequency'in stream.keys():
        f = 'Frequency'
        p = 'Power'

    a,b = band
    freq_array = np.array(stream[f])
    mask = (freq_array >= a) & (freq_array <= b)
    power = np.array(stream[p])[mask]

    return np.std(power)
   
def std_dev_streams(streams, bands):

    if not isinstance(streams, (list, tuple, np.ndarray)):  
        streams = [streams]
    
    if 'X' in streams[0].keys():
        f = 'X'
        p = 'Y'
    elif 'Frequency'in streams[0].keys():
        f = 'Frequency'
        p = 'Power'
    else:
        raise ValueError("Invalid stream format: Expected keys 'X' or 'Frequency'.")
    
    band_powers = {name: [] for name in bands}

    for stream in streams:
        freq_array = np.array(stream[f])
        power_array = np.array(stream[p])

        for name, (a, b) in bands.items():
            mask = (freq_array >= a) & (freq_array <= b)
            band_powers[name].append(power_array[mask])

    # Calculate standard deviation for each band
    std_devs = {}
    for name, power_list in band_powers.items():
        if power_list:  
            stacked_powers = np.vstack(power_list)
            std_devs[name] = np.std(stacked_powers)  
        else:
            std_devs[name] = None  # No data for this band

    return std_devs   

def mean_power_band(log,band):
    #events
    power = []
    
    fi,ff = band

    temp = []
    if 'X' in log.keys():
        freq = log['X']
        pwr = log['Y']
    if 'Frequency' in log.keys():
        freq = log['Frequency']
        pwr = log['Power']

    for idx, f in enumerate(freq):
        if fi<=f<=ff: temp.append(pwr[idx])
    if temp:
        power.append(np.mean(temp))

    return np.mean(power) if power else np.nan 

def mean_power_all_bands(stream, bands):
    """Computes mean power for frequency bands over a stream of events."""
    
    # Ensure stream is iterable
    if not isinstance(stream, (list, tuple, np.ndarray)):  
        stream = [stream]  # Convert single event to a list

    power_values = {band: [] for band in bands}

    # Process each event
    for event in stream:
        for band, freq_range in bands.items():
            power_values[band].append(mean_power_band(event, freq_range))

    # Compute mean power for each band
    power = {band: np.mean(values) if values else 0 for band, values in power_values.items()}

    return power

def psd_fft(filtered_eeg, fs=250):
    N = len(filtered_eeg)
    hanning_window = np.hanning(N)  # Apply window before FFT
    windowed_signal = filtered_eeg * hanning_window

    fft_values = np.fft.fft(windowed_signal)[:N // 2]  # Compute FFT
    freqs = np.fft.fftfreq(N, 1/fs)[:N // 2]

    # Compute power correction factor for the window
    window_power_correction = np.sum(hanning_window**2) / N

    # Correct PSD normalization
    psd = (np.abs(fft_values) ** 2) / (fs * N * window_power_correction)  # Convert to µV²/Hz
    
    mask = freqs <= 100
    freqs = freqs[mask]
    psd = psd[mask]

    return freqs, psd

def export_2D(info):
    signals,labels,colors,title,axis = info
    plt.figure()
    plt.title(title)
    plt.xlabel(axis[0])
    plt.ylabel(axis[1])
    for i,signal in enumerate(signals):
        label = labels[i]
        x,y = signal['X'],signal['Y']
        plt.plot(x,y,label=label,color=colors[i])
    plt.legend()
    plt.savefig('Example.png')

def plot_spectrogram(data, channel_params, *args):
    """
    Compute and plot the spectrogram for each channel.

    Parameters:
    data : ndarray
        2D array where each column corresponds to a channel's data.
    channel_params : dict
        Dictionary containing channel parameters with keys:
        - 'Fs': Sampling frequency (Hz).
        - 'nChannels': Number of channels.
        - 'channel_names': List of channel names.
        - 'channel_map': 2D array specifying subplot arrangement.
        - 'time': Array of time values.
    args : tuple
        Optional arguments. Pass 'normalize' to normalize power values.

    Returns:
    spectro_fig : matplotlib.figure.Figure
        The figure object containing the spectrogram plots.
    """
    normalize_power = 'normalize' in args

    # Default spectrogram parameters
    window = int(round(0.5 * 250))  # 0.5 second
    noverlap = int(round(window / 2))
    fmin = 1  # Hz
    fmax = 125  # Hz

    # Initialize figure
    spectro_fig, axes = plt.subplots(
        *channel_params['channel_map'].shape, figsize=(12, 8), squeeze=False
    )
    axes_flat = axes.flatten()

    for ch_id in range(len(data)):
        channel_pos = np.argwhere(channel_params['channel_map'] == ch_id + 1).flatten()
        ax = axes[channel_pos[0], channel_pos[1]]

        # Compute spectrogram
        f, t, Sxx = signal.spectrogram(
            data[:, ch_id],
            fs=channel_params['Fs'],
            window='hann',
            nperseg=window,
            noverlap=noverlap,
            scaling='density',
            mode='psd'
        )

        # Filter frequencies
        freq_mask = (f >= fmin) & (f <= fmax)
        f = f[freq_mask]
        Sxx = Sxx[freq_mask, :]

        # Normalize power if requested
        if normalize_power:
            power_to_plot = 10 * np.log10(Sxx / np.mean(Sxx, axis=1, keepdims=True))
        else:
            power_to_plot = 10 * np.log10(Sxx)

        # Plot spectrogram
        img = ax.imshow(
            power_to_plot,
            aspect='auto',
            extent=[t[0], t[-1], f[0], f[-1]],
            origin='lower',
            cmap='viridis'
        )

        ax.set_title(channel_params['channel_names'][ch_id])
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Frequency (Hz)')
        ax.grid(False)

        # Add colorbar
        cbar = plt.colorbar(img, ax=ax)
        cbar.set_label('Power/Frequency (dB/Hz)')

    # Link axes
    for ax in axes_flat:
        ax.label_outer()
    plt.tight_layout()

    return spectro_fig

def export_plot_old(info, plot_type):
    signals, labels, colors, title, axis = info
    
    plt.figure()
    plt.suptitle(title)

    match plot_type:
        case '2D':
            plt.xlabel(axis[0])
            plt.ylabel(axis[1])
            for i, signal in enumerate(signals):
                label = labels[i]
                x, y = signal['X'], signal['Y']
                plt.plot(x, y, label=label, color=colors[i])
            plt.legend()

        case '3D':
            n_signals = len(signals)
            fig, axs = plt.subplots(
                n_signals, 1,
                figsize=(8, 3 * n_signals),
                constrained_layout=True,
                sharex=True
            )
            
            # If there's only one signal, axs is not iterable
            if n_signals == 1:
                axs = [axs]

            for i, signal in enumerate(signals):
                f, t, sxx = signal
                ax = axs[i]
                pcm = ax.pcolormesh(
                    t, f, sxx,
                    shading='gouraud',
                    cmap='viridis'
                )
                ax.set_ylabel(axis[1])
                ax.set_title(labels[i])
                fig.colorbar(pcm, ax=ax, label=axis[2])

            axs[-1].set_xlabel(axis[0])

            plt.close()
            plt.figure(fig.number)

    plt.savefig('Example.png', bbox_inches='tight', dpi=300)
    plt.show()

import matplotlib.pyplot as plt
import numpy as np

def export_plot(info, plot_type, show=False):
    signals, labels, colors, title, axis = info

    if plot_type == '2D':
        fig, ax = plt.subplots()
        ax.set_title(title)
        ax.set_xlabel(axis[0])
        ax.set_ylabel(axis[1])

        for i, signal in enumerate(signals):
            label = labels[i]
            x, y = signal['X'], signal['Y']
            ax.plot(x, y, label=label, color=colors[i])

        ax.legend()
        fig.tight_layout()

    elif plot_type == '3D':
        n_signals = len(signals)
        fig, axs = plt.subplots(
            n_signals, 1,
            figsize=(8, 3 * n_signals),
            constrained_layout=True,
            sharex=True
        )
        if n_signals == 1:
            axs = [axs]

        fig.suptitle(title)
        for i, signal in enumerate(signals):
            f, t, sxx = signal
            ax = axs[i]
            pcm = ax.pcolormesh(t, f, sxx, shading='gouraud', cmap='viridis')
            fig.colorbar(pcm, ax=ax, label=axis[2])
            ax.set_ylabel(axis[1])
            ax.set_title(labels[i])
        axs[-1].set_xlabel(axis[0])

    fig.savefig('Example.png', bbox_inches='tight', dpi=300)

    if show:
        plt.show()

    plt.close(fig)


def wave(frequency = 10, sampling_rate = 1000, duration = 1, amplitude = 1):
    
    # Generate time vector
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

    # Generate the sine wave signal
    signal = amplitude * np.sin(2 * np.pi * frequency * t)

    return np.array(t), np.array(signal)


#----------- BRAVO ------------------------------------------------------------
def MedtronicPSD(data, fs=250): 

    window = 256 
    packets = [24,38,25,38] 
    maxIndex = 250 
    count = 8 
    nfft = 0 

    while maxIndex < len(data): 
        if maxIndex >= 250: 
            nfft += 1 
        maxIndex += packets[count % 4] 
        count += 1 

    freq = np.arange(window)/window*fs 
    power = np.zeros((len(freq), nfft)) 


    maxIndex = 250 
    hanning_window = np.hanning(250)
    window_power_correction = np.sum(hanning_window**2) / 250  # Energy normalization factor

    for i in range(nfft):  
        windowed_data = np.zeros(window)  
        windowed_data[:250] = data[maxIndex - 250:maxIndex] * hanning_window  
        fft_result = np.fft.fft(windowed_data)  

        power[:, i] = (np.abs(fft_result) ** 2) / (fs * window * window_power_correction)  # Convert to µV²/Hz

        maxIndex += packets[i % 4]  

    return {"Frequency": freq[:100], "Power": np.mean(power[:100],axis=1)} #, "StdErr": stats.sem(power,axis=1)[:100]} 

def getIndices(length, window, overlap):
    return np.array(range(0, length+1-window, window-overlap))

def spectrogram(signal, fs = 250): #incomplete/ should receive the 
    if len(signal) < 5000:
        nperseg = int(min(256, len(signal) / 2))
        noverlap = int(nperseg / 2)
    else:
        nperseg = 1024
        noverlap = nperseg / 2


    frequencies, times, Sxx = spectrogram(signal, fs=fs,nperseg=nperseg, noverlap=noverlap, window='hamming', scaling='density')
    Sxx_log = 10 * np.log10(Sxx + 1e-10)  # Convert to dB scale

    Sxx_log = np.flipud(Sxx_log)

    return frequencies, times, Sxx_log

def autoregressiveSpectrogram(data, window=2.0, overlap=1.0, frequency_resolution=0.5, fs=100, order=50):
    configuration = {"Window": window, "Overlap": overlap}
    window = int(window * fs)
    overlap = int(overlap * fs)
    NFFT = int(fs / frequency_resolution)
    epochs = getIndices(len(data),window,overlap)
    frequency = np.array(pyule(np.array(1),order,NFFT=NFFT, sampling=fs).frequencies())
    spectrum = np.ndarray((len(frequency), len(epochs)))
    for index in range(len(epochs)):
        p = pyule(data[epochs[index]:epochs[index]+window], order, NFFT=NFFT, sampling=fs)
        spectrum[:,index] = p.psd
    time = (epochs + window) / fs
    
    return dict({"Time": time, "Frequency": frequency, "Power": spectrum, "logPower": 10*np.log10(spectrum), "Config": configuration})