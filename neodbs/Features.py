import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
#from spectrum import pyule

bands = {
            'Delta': [0.01,4],
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

def get_sum_mean_power(p,band=None):
    if band == None: band = bands
    x,y=p['X'],p['Y']
    all = []
    if isinstance(x,list):
        x = np.array(x)
        y = np.array(y)

    for b,v in band.items():
        mask = (x >= v[0]) & (x <= v[1])
        temp = y[mask]
        all.append(np.nanmean(temp))
    return np.sum(all)

def extract_psd_features(p, band, bands=None):
    '''
    Extracts features from spectral density, or coherence, methods. Returned into a dictionary. 
    
    :param p: dict, computed PSD ('X' = freqs, 'Y' = psd values)
    :param band: list, band[0] = str, band name; band[1] = list, [f0,f1]
    '''
    b,v = band
    band = {b: v}
    full_power = np.sum(p['Y'])
    freqs, psd = p['X'], p['Y']
    
    #mean power per band
    pc = mean_power_all_bands(p, band)
    std = std_dev_streams(p, band)
    mean = {'Mean Power (mean, std. dev)': [np.round(pc[b],2), np.round(std[b],2)]}

    #normalized mean power
    sum_mean_power = get_sum_mean_power(p,band=bands)
    # norm_mean = {'% Mean Power (mean, std. dev)': [np.round(pc[b]*100/full_power,2), np.round(std[b],2)]}
    norm_mean = {'% Mean Power (mean, std. dev)': [np.round(pc[b]*100/sum_mean_power,2), np.round(std[b],2)]}

    if isinstance(freqs, list): 
        freqs = np.array(freqs)
        psd = np.array(psd)

    mask = (freqs >= v[0]) & (freqs <= v[1])
    auc = {'Sum Power (AUC)': np.round(np.sum(psd[mask]),2)}

    #normalized auc
    norm_auc = {'% Sum Power (AUC)': f"{np.round(np.sum(psd[mask])/full_power*100,2)}"}

    #peak power
    peak = peak_per_band(p, band)
    picos = {'Peak Power (power, frequency)': p for p in peak.values()}


    info = mean | norm_mean| auc | norm_auc| picos

    return info

def extract_timeline_features(p):
    '''
    Extracts features from timeline recordings, returned into a dictionary. 
    
    :param p: dict, computed PSD ('X' = time array, 'Y' = lfp timeline values)
    '''
    

    freqs, psd = p['X'], p['Y']

    if isinstance(psd, np.ndarray):
        psd = psd.tolist()
    elif psd is None:
        return
    #mean power per band
    pc = np.nanmean(psd)
    std = np.nanstd(psd)
    mean = {'Mean Power (mean, std. dev)': [np.round(pc,2), np.round(std,2)]}
 
    #peak power
    peak = np.nanmax(psd)
    picos = {'Peak Power': peak}

    #peak time
    time = psd.index(peak)
    
    try:
        time = freqs[time]
    except Exception: time = freqs[0]

    key = 'Peak Time'
    if isinstance(time,str):
        peak = str(utl.parse_datetime(time).time())
    elif isinstance(time, (int, float)):
        if np.isnan(time):
            return
    elif isinstance(time, np.ndarray):
        if np.any(np.isnan(time)):
            return
    elif isinstance(time,float):
        peak = str(datetime.fromtimestamp(time).time())
    else: #datetime.datetime object
        peak=str(time.time())

    time = {key: peak}
    info = mean | picos | time
    if 'Sense' in p.keys():
        sense = {'Sensing Freq. (Hz)': p['Sense']}
        info = info| sense

    return info

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

def export_plot(info, plot_type, size=None, line_types = None):

    signals, labels, colors, title, axis, limits  = info

    default_fig = plt.figure()
    width_default, height_default = default_fig.get_size_inches()
    plt.close(default_fig)

    if size:
        size = [(s/100 if (s is not None and s > 0) else None) for s in size]

        width  = size[0] if size[0] is not None else width_default
        height = size[1] if size[1] is not None else height_default
        size = (width,height)
    else:
        size = (width_default,height_default)
    

    if plot_type in ['2D','CC']:
        fig, ax = plt.subplots(figsize=(size[0],size[1]))
        
        
        if 'Timeline' in title: 
            labels = [None for _ in labels]

        for i, signal in enumerate(signals):
            label = labels[i]
            if 'Y1' in signal.keys(): #std.dev or shaded series
                x, y1,y2 = signal['X'], signal['Y1'], signal['Y2']
                ax.fill_between(x,y1,y2,label=label,color=colors[i][:3],alpha=colors[i][-1])
            # elif len(list(signal.keys()))==1: #infinte lines
            elif 'InfLine' in line_types[i]:
                if labels[i] == 'Half Max':
                    ax.hlines(signal['X'],*limits[0],label=label,color=colors[i])
                else: ax.vlines(signal['X'],*limits[1],label=label,color=colors[i])
            elif (label in ['',' ']) or ('Scatter' in line_types[i]):
                x, y = signal['X'], signal['Y']
                ax.scatter(x,y,label=label,color=colors[i-1],zorder=len(signals))
            else: 
                x, y = signal['X'], signal['Y']
                thick = 1
                if label is None:
                    ax.plot(x, y, color=colors[i],linewidth=thick)
                else:
                    if 'mean' in label.lower(): thick = 3
                    ax.plot(x, y, label=label, color=colors[i],linewidth=thick)

        ax.set_title(title)
        ax.set_xlabel(axis[0])
        ax.set_ylabel(axis[1])
        ax.set_xlim(*limits[0])
        ax.set_ylim(*limits[1])

        if 'Timeline' in title or 'Circadian' in title or 'Stimulation' in title:
            ax.set_xlim(*[datetime.fromtimestamp(l) for l in limits[0]])
            fig.autofmt_xdate()

        if any(label is not None for label in labels):
            fig.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=False)
        
        fig.tight_layout()

    elif plot_type in ['3D','3DC']:
        n_signals = len(signals)
        if n_signals>1:
            rows, cols = n_signals//2, 2
        else:
            rows, cols = n_signals, 1

        fig, axs = plt.subplots(
            rows, cols,
            figsize=(size[0]*cols,size[1]*rows),
            constrained_layout=True,
            sharex=True
        )
        if n_signals==1: axs = [axs]

        fig.suptitle(title)
        for i, signal in enumerate(signals):
            f, t, sxx = signal
            ax = axs[i]
            pcm = ax.pcolormesh(t, f, sxx,cmap=colors,vmin=limits[i][2][0],vmax=limits[i][2][1])
            fig.colorbar(pcm, ax=ax, label=axis[2])
            ax.set_ylabel(axis[1])
            ax.set_title(labels[i])
            ax.set_xlim(limits[i][0])
            ax.set_ylim(limits[i][1])
            if n_signals>1:
                ax.set_title(labels[i])
        axs[-1].set_xlabel(axis[0])

    elif plot_type in ['Bar','Events']:
        fig, ax = plt.subplots(figsize=(size[0],size[1]))
        if plot_type=='Events':
            ax.set_xlim(*[datetime.fromtimestamp(l) for l in limits[0]])
            fig.autofmt_xdate()
            
            width = 0.2
            if axis[0] == 'Hours': 
                width = 0.002
        else:
            ax.set_xlim(limits[0])
            width =1
            labels = []*len(signals)
        for i,signal in enumerate(signals):
            x,y = signal['X'], signal['Y']
            ax.bar(x,y,color=colors[i],width=width,label=labels[i])

        if any(label is not None for label in labels):
            fig.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=False)
        
        ax.set_title(title)
        ax.set_xlabel(axis[0])
        ax.set_ylabel(axis[1])
        ax.set_ylim(limits[1])
        if len(axis)>2:
            ax.set_xticks(axis[2][0], labels=axis[2][1])
    
    elif plot_type == 'Pie':
        fig = plt.figure(figsize=(size[0],size[1]))
        plt.pie(signals,labels=labels,colors=colors,
                autopct=lambda pct: f'{signals[int(pct/100*len(signals))]:.1f}', 
                startangle=90)
        plt.title(title)

    fig.savefig(f'{title}.png', bbox_inches='tight',dpi=300) #

    plt.close(fig)

def export_signals(info,filename, tfd = False):
    filename = filename.replace(' - ','_')
    filename = filename.replace(' ','_')
    filename = 'Signals_'+filename + ".csv"
    if tfd:
        with open(filename, "w") as f:
            # f.write(",".join(list(info.keys())) + "\n")
            for spec in info:
                (plot_title, value), = spec.items()
                frequencies,time,sxx = value
                t = ['Freq (Hz)/Time (s)']
                for tp in time: 
                    t.append(str(tp))
                f.write(f"{plot_title} \n")
                f.write(",".join(t) + "\n")
                for line, freq in enumerate(frequencies): 
                    row = []
                    row.append(f"{freq}")
                    for col in range(len(time)):
                        try:
                            row.append(str(sxx[line][col]))
                        except:
                            row.append(' ')
                    f.write(",".join(row) + "\n")

                f.write("--------------------------------\n\n")
        return
    with open(filename, "w") as f:
        f.write(",".join(list(info.keys())) + "\n")
        n = info[list(info.keys())[0]]
        if isinstance(n,(list,np.ndarray)):
            n_lines = len(n)
        else: n_lines=1
        for i in range(n_lines):
            row = []
            for column in info.keys():
                try:
                    row.append(str(info[column][i]))
                except:
                    row.append(' ')
            f.write(",".join(row) + "\n")

def wave(frequency = 10, sampling_rate = 1000, duration = 1, amplitude = 1):
    
    # Generate time vector
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

    # Generate the sine wave signal
    signal = amplitude * np.sin(2 * np.pi * frequency * t)

    return np.array(t), np.array(signal)

def convert_to_db(value):
    """Convert a value to dB scale using 10 * log10.
    :param value: int/float"""
     # if isinstance(value, (list, np.ndarray)):
     #     return [round(10 * np.log10(v +1e-6), 2) for v in value]
    if isinstance(value, (list, np.ndarray,tuple)):  # Handle peak values (power, frequency)
        return (round(10 * np.log10(value[0]+1e-6), 2), value[1])
    elif isinstance(value, (int, float)):
        return round(10 * np.log10(value+1e-6), 2)
    return value  # Return unchanged if it's a string or invalid type
 
def convert_from_db(value):
 
    """Convert a dB value back to linear scale using 10^(dB/10).
    :param value: int/float"""
     # if isinstance(value, (list, np.ndarray,tuple)):  
     #     return [round(10**(v / 10), 2) if v != float('-inf') else 0 for v in value]
 
    if isinstance(value, (list, np.ndarray,tuple)):  # Handle peak values (power, frequency)
        return (round(10**(value[0] / 10), 2) if value[0] != float('-inf') else 0, value[1])
    elif isinstance(value, (int, float)):
        return round(10**(value / 10), 2) if value != float('-inf') else 0
    return value  # Return unchanged if it's a string or invalid type
 

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