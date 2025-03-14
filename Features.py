import numpy as np

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
        delta = mean_power_band(event,[0,3])
        d.append(delta)
        theta = mean_power_band(event,[4,8])
        t.append(theta)
        alpha = mean_power_band(event,[8,12])
        a.append(alpha)
        beta = mean_power_band(event,[12,30])
        b.append(beta)
        gamma = mean_power_band(event,[30,100])
        g.append(gamma)

    print(f"MEAN DELTA: {np.mean(d)}")
    print(f"MEAN THETA: {np.mean(t)}")
    print(f"MEAN ALPHA: {np.mean(a)}")
    print(f"MEAN BETA: {np.mean(b)}")
    print(f"MEAN GAMMA: {np.mean(g)}")

    power = {
        'Delta': np.mean(d),
        'Theta': np.mean(t),
        'Alpha': np.mean(a),
        'Beta': np.mean(b),
        'Gamma': np.mean(g)
    }

    return power

def psd_fft(filtered_eeg):
    # Step 2: Compute the FFT
    fs = 250
    n = len(filtered_eeg)
    fft_values = np.fft.fft(filtered_eeg)
    fft_values = fft_values[:n // 2]  # Only keep the positive frequencies
    freqs = np.fft.fftfreq(n, 1/fs)[:n // 2]

    # Step 3: Compute the Power Spectral Density (PSD)
    psd = np.abs(fft_values) ** 2 / n

    return psd, freqs