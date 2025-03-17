import numpy as np
#from spectrum import pyule

def peak_power(stream):
    '''
    Receives a stream with PSD values
    '''
    peak_idx = np.argmax(stream["Y"])
    peak_f = stream["X"][peak_idx]
    peak_power = stream["Y"][peak_idx]

    return [peak_f, peak_power]
    
def mean_power_band(log,band):
    #events
    power = []
    
    fi,ff = band

    temp = []
    freq = log['X']
    pwr = log['Y']
    for idx, f in enumerate(freq):
        if fi<=f<=ff: temp.append(pwr[idx])
    if temp:
        power.append(np.mean(temp))

    return np.mean(power) if power else np.nan 

def mean_power_all_bands(stream):

    d,t,a,b,g = [],[],[],[],[]

    for event in stream:

        delta = mean_power_band(event,[0,4])
        d.append(delta)
        theta = mean_power_band(event,[4,8])
        t.append(theta)
        alpha = mean_power_band(event,[8,12])
        a.append(alpha)
        beta = mean_power_band(event,[12,30])
        b.append(beta)
        gamma = mean_power_band(event,[30,100])
        g.append(gamma)

    power = {
        'Delta': np.mean(d),
        'Theta': np.mean(t),
        'Alpha': np.mean(a),
        'Beta': np.mean(b),
        'Gamma': np.mean(g)
    }

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

def wave(frequency = 10, sampling_rate = 1000, duration = 1, amplitude = 1):
    
    # Generate time vector
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

    # Generate the sine wave signal
    signal = amplitude * np.sin(2 * np.pi * frequency * t)

    return t, signal

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

    return {"Frequency": freq[:100], "Power": np.mean(power,axis=1)[:100]} #, "StdErr": stats.sem(power,axis=1)[:100]} 

def getIndices(length, window, overlap):
    return np.array(range(0, length+1-window, window-overlap))

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