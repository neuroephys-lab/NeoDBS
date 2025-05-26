import dearpygui.dearpygui as dpg
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt,coherence, hilbert, find_peaks
from scipy.signal.windows import dpss 
import DataHandling as DH

selected_channels = []
comparison = []

# === FUNÇÕES DE PROCESSAMENTO ===
def compute_coherence_standard(signal1, signal2, sample_rate, nperseg=None, nfft=None, fmax=100):
    freq, coh = coherence(signal1, signal2,fs=sample_rate,nperseg=nperseg,nfft=nfft)
    mask = freq <= fmax
    return freq[mask], coh[mask]

def compute_coherence_multitaper(signal1, signal2, fs, window_len=1024, step=None, nw=4, fmax=100):
    if step is None:
        step = window_len // 2
    N = min(len(signal1), len(signal2))
    nfft = max(window_len, 512)
    kmax = 2*nw - 1
    tapers = dpss(window_len, NW=nw, Kmax=kmax, sym=True)

    Sxx_sum = np.zeros(nfft//2+1)
    Syy_sum = np.zeros(nfft//2+1)
    Sxy_sum = np.zeros(nfft//2+1, dtype=np.complex128)
    n_windows = 0

    for start in range(0, N - window_len + 1, step):
        xw = signal1[start:start+window_len]
        yw = signal2[start:start+window_len]
        Sxx_tapers, Syy_tapers, Sxy_tapers = [], [], []
        for taper in tapers:
            S1 = np.fft.rfft(xw * taper, n=nfft)
            S2 = np.fft.rfft(yw * taper, n=nfft)
            Sxx_tapers.append(np.abs(S1)**2)
            Syy_tapers.append(np.abs(S2)**2)
            Sxy_tapers.append(S1 * np.conj(S2))
        Sxx_sum += np.mean(Sxx_tapers, axis=0)
        Syy_sum += np.mean(Syy_tapers, axis=0)
        Sxy_sum += np.mean(Sxy_tapers, axis=0)
        n_windows += 1

    Sxx = Sxx_sum / n_windows
    Syy = Syy_sum / n_windows
    Sxy = Sxy_sum / n_windows

    coh = np.abs(Sxy)**2 / (Sxx * Syy)
    freq = np.fft.rfftfreq(nfft, d=1/fs)

    mask = freq <= fmax
    return freq[mask], coh[mask]

def plot_coherence_spectrogram(signal1, signal2, fs,window_len=1024,step=None,nw=4,fmax=100,cmap='viridis'):
    if step is None:
        step = window_len // 2

    nfft = max(window_len, 512)
    N = min(len(signal1), len(signal2))
    signal1, signal2 = signal1[:N], signal2[:N]

    K = int(2*nw - 1)
    tapers = dpss(window_len, NW=nw, Kmax=K, sym=True)

    starts = np.arange(0, N-window_len+1, step)
    times = (starts + window_len/2) / fs

    freqs = np.fft.rfftfreq(nfft, d=1/fs)
    mask = freqs <= fmax
    freqs = freqs[mask]

    matrix = np.zeros((len(freqs), len(starts)))
    for idx, s in enumerate(starts):
        signal1w, signal2w = signal1[s:s+window_len], signal2[s:s+window_len]
        Sxx = Syy = Sxy = 0
        for tap in tapers:
            X = np.fft.rfft(signal1w * tap, n=nfft)
            Y = np.fft.rfft(signal2w * tap, n=nfft)
            Sxx += np.abs(X)**2
            Syy += np.abs(Y)**2
            Sxy += X * np.conj(Y)
        Sxx /= K
        Syy /= K
        Sxy /= K
        coh = np.abs(Sxy)**2 / (Sxx * Syy)
        matrix[:, idx] = coh[mask]
        print(max(coh[mask]))

    plt.figure(figsize=(8, 4))
    plt.pcolormesh(times, freqs, matrix, cmap=cmap)
    plt.colorbar(label='Coherence')
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Coherence Spectogram')
    plt.tight_layout()
    plt.show()

def compute_cross_correlation(signal1, signal2, normalize=True):
    corr = np.correlate(signal1, signal2, mode='full')
    dislocation = np.arange(-len(signal1)+1, len(signal1))

    if normalize:
        corr = corr / np.max(np.abs(corr))
    return dislocation , corr

def bandpass_filter(data, fs, lowcut, highcut, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    y = filtfilt(b, a, data)
    return y

def compute_band_cross_correlation(signal1, signal2, fs=250,
                                   lowcut=4.0, highcut=4.2,
                                   normalize=True, filter_order=4):

    sig1_bp = bandpass_filter(signal1, fs, lowcut, highcut, order=filter_order)
    sig2_bp = bandpass_filter(signal2, fs, lowcut, highcut, order=filter_order)
    
    corr = np.correlate(sig1_bp, sig2_bp, mode='full')
    dislocation = np.arange(-len(signal1) + 1, len(signal1))
    
    if normalize:
        corr = corr / np.max(np.abs(corr))
    return dislocation, corr

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

    plt.figure()
    plt.polar(centers, amp_means)
    plt.title(f'Modulation Index: {mi:.3f}')
    plt.show()

    return mi, centers, amp_means

# === PLOT DE FEATURES ===
def plot_features(channel1, channel2, signal1, signal2, sample_rate):
    min_length = min(len(signal1), len(signal2))
    signal1 = signal1[:min_length]
    signal2 = signal2[:min_length]

    for item in comparison:
        dpg.delete_item(item)
    comparison.clear()

    features_section = dpg.add_collapsing_header(label=f"Comparison: {channel1['Channel']} vs {channel2['Channel']}", parent="main_window")

    # --- Coherence ---
    dpg.add_text(f"Coherence between {channel1['Channel']} and {channel2['Channel']}:", parent=features_section)

    coh_x = f"x_coherence_{channel1['Channel']}_{channel2['Channel']}"
    coh_y = f"y_coherence_{channel1['Channel']}_{channel2['Channel']}"

    freq_std, coh_std = compute_coherence_standard(signal1, signal2, sample_rate)
    freq_mt, coh_mt = compute_coherence_multitaper(signal1, signal2, sample_rate)

    plot_tag = f"plot_coh_{channel1['Channel']}_{channel2['Channel']}"
    with dpg.plot(label="Coherence: Standard vs Multitaper",tag=plot_tag,height=300,width=-1,parent=features_section):
        dpg.add_plot_axis(dpg.mvXAxis, label="Frequency", tag=coh_x)
        with dpg.plot_axis(dpg.mvYAxis, label="Coherence", tag=coh_y):
            dpg.add_line_series(freq_std.tolist(), coh_std.tolist(), label="Standard", parent=coh_y)
            dpg.add_line_series(freq_mt.tolist(), coh_mt.tolist(), label="Multitaper", parent=coh_y)
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)

    plot_coherence_spectrogram(signal1, signal2, sample_rate)

    # --- Cross-correlation ---
    dislocation, corr = compute_band_cross_correlation(signal1, signal2, normalize=True)

    cross_x = f"x_cross_{channel1['Channel']}_{channel2['Channel']}"
    cross_y = f"y_cross_{channel1['Channel']}_{channel2['Channel']}"

    with dpg.plot(label="Cross-correlation", height=300, width=-1, parent=features_section):
        dpg.add_plot_axis(dpg.mvXAxis, label="Samples", tag=cross_x)
        with dpg.plot_axis(dpg.mvYAxis, label="Correlation", tag=cross_y):
            dpg.add_line_series(dislocation .tolist(), corr.tolist(),label="Cross-corr", parent=cross_y)
            dpg.set_axis_limits(cross_x, dislocation [0], dislocation [-1])
            dpg.set_axis_limits(cross_y, np.min(corr), np.max(corr))

    # --- Phase-Amplitude Coupling ---
    mod_index, phase_bins, amp_vals = compute_phase_amplitude(signal1, signal2, sample_rate)

    pac_x = f"x_pac_{channel1['Channel']}_{channel2['Channel']}"
    pac_y = f"y_pac_{channel1['Channel']}_{channel2['Channel']}"

    with dpg.plot(label=f"Phase-Amplitude Coupling (Modulation Index = {mod_index:.4f})", height=300, width=-1, parent=features_section, tag = 'pac'):
        dpg.add_plot_axis(dpg.mvXAxis, label="Phase (rad)", tag=pac_x)
        dpg.add_plot_axis(dpg.mvYAxis, label="Mean Amplitude", tag=pac_y)
        phase = phase_bins.tolist()
        amp = amp_vals.tolist()

        for p,a in zip(phase,amp):
            dpg.add_bar_series([p], [a], parent=pac_y)

        dpg.bind_colormap('pac', dpg.mvPlotColormap_Jet)

    comparison.append(features_section)

# === SELEÇÃO DE CANAIS ===
def select_channels():
    # selected_channels.clear()

    # for signal in signals:
    #     if dpg.get_value(f"checkbox_{signal['Channel']}_{signal['Date']}"):
    #         selected_channels.append(signal)
    selected_channels = signals

    if len(selected_channels) == 2:
        channel1 = selected_channels[0]
        channel2 = selected_channels[1]

        plot_features(channel1, channel2, np.array(channel1['Y']), np.array(channel2['Y']), 250)
    else:
        dpg.add_text("Please select exactly two channels for comparison", parent="main_window")

# file_path = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

Data = DH.getData(file_path)
Streaming = DH.getSignals(Data, 'Streaming')
signals = Streaming[-2], Streaming[-1]

dpg.create_context()
dpg.create_viewport(title="NeoDBS", width=1000, height=600)
dpg.setup_dearpygui()

with dpg.window(tag = 'main_window'):
    select_channels()

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()