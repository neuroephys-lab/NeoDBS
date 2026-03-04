import DataHandling as DH
from GUI import *
import dearpygui.dearpygui as dpg
# import Features as ft
from scipy import signal
# from scipy.signal._wavelets import _cwt, _ricker
# import matplotlib.pyplot as plt
import numpy as np
# from scipy.signal import spectrogram
# from datetime import datetime as dt
# import Preprocessing as pre
import utils as utl
'''
BASE

dpg.create_context()
with dpg.window():

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

# # file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"
file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
# # file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"

'''

#file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\File_example.json"
file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

data = DH.getData(file)

streaming = DH.getSignals(data,'Streaming')[0]

x,y = streaming['X'],streaming['Y']

# wavelet =_cwt(y,None,np.atleast_1d(np.asarray([100])))
width = 7 
freqs = np.arange(1, 100, 1)
fs=250

def morlet_wavelet(f, fs, n_cycles=7):
    t = np.arange(-1, 1, 1/fs)
    sigma = n_cycles / (2*np.pi*f)
    wavelet = np.exp(2j*np.pi*f*t) * np.exp(-t**2/(2*sigma**2))
    return wavelet

def wavelet_transform(x, fs, freqs):
    power = []
    for f in freqs:
        w = morlet_wavelet(f, fs)
        conv = np.convolve(x, w, mode='same')
        power.append(np.abs(conv)**2)
    return np.array(power)

fs = 250
freqs = np.arange(1,100)
power = wavelet_transform(y, fs, freqs)
power = np.flipud(10 * np.log10(power)).flatten().tolist()

parameter_values, documentation = fill_params_features('wavelet')
mne_wav = apply_feat('wavelet',parameter_values,y)
tfr = 10 * np.log10(mne_wav)
tfr = np.flipud(tfr[0, 0, :, :])
heatmap_data = tfr.flatten().tolist()

miniii = min(min(heatmap_data),min(power))
maxii = max(max(heatmap_data),max(power))


dpg.create_context()
with dpg.window():
    mother = dpg.add_group(horizontal=True)
    
    dpg.add_colormap_scale(min_scale=miniii,max_scale=maxii,parent=mother,colormap=dpg.mvPlotColormap_Jet)
    parent = dpg.add_group(horizontal=False,parent=mother)
    with dpg.plot(parent=parent,label='MNE',tag='mne'):
        dpg.add_plot_axis(dpg.mvXAxis,label='Time')
        yy = dpg.add_plot_axis(dpg.mvYAxis,label='Frequency')

        dpg.add_heat_series(heatmap_data, rows=tfr.shape[0], cols=tfr.shape[1], 
                                        parent=yy, scale_max=maxii,scale_min=miniii, format="")#, bounds_min=[0,freqs[0]], bounds_max=[int(tfr.shape[1]/250),freqs[-1]])
        dpg.bind_colormap('mne', dpg.mvPlotColormap_Jet)

    with dpg.plot(parent=parent,label='SCIPY',tag='scipy'):
        dpg.add_plot_axis(dpg.mvXAxis,label='Time')
        yy = dpg.add_plot_axis(dpg.mvYAxis,label='Frequency')

        dpg.add_heat_series(power, rows=100, cols=int(len(power)/100), 
                                        parent=yy, scale_max=maxii,scale_min=miniii, format="")#, bounds_min=[0,freqs[0]], bounds_max=[int(tfr.shape[1]/250),freqs[-1]])
        dpg.bind_colormap('scipy', dpg.mvPlotColormap_Jet)

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()



print('')



def deduplicate_packets(raw_ticks, raw_sizes):
    """
    Merges packets that share the same tick (stim OFF behaviour).
    Returns two aligned arrays:
        ticks[i]  -> timestamp in ms
        sizes[i]  -> total bytes received at that tick (sum of all packets sharing it)
    Indices are coherent: ticks[i] always corresponds to sizes[i].
    """
    ticks = []
    sizes = []

    for tick, size in zip(raw_ticks, raw_sizes):
        if ticks and ticks[-1] == tick:
            # Same tick as previous → merge (sum sizes)
            sizes[-1] += size
        else:
            # New tick → append
            ticks.append(tick)
            sizes.append(size)

    return ticks, sizes

def detect_gaps(ticks, expected_interval=250):
    """
    Checks for missing samples between consecutive ticks.
    Returns a list of dicts describing each gap found.
    """
    gaps = []

    for i in range(1, len(ticks)):
        diff = ticks[i] - ticks[i - 1]
        if diff != expected_interval:
            missed = round(diff / expected_interval) - 1
            gaps.append({
                "index": i,
                "from_tick": ticks[i - 1],
                "to_tick": ticks[i],
                "diff_ms": diff,
                "missed_samples": missed,
            })

    return gaps

def CheckMissingPacketsTD(data, mode):
    if mode=='Streaming':
        data = data[mode]['BrainSenseTimeDomain']
    else:
        data[mode]
    for td in data:
        seqs = utl.string2numbers(td['GlobalSequences'])
        sizes = utl.string2numbers(td['GlobalPacketSizes'])
        seqs_diff = np.diff(np.asarray(seqs))

        missing_packets = np.where(seqs_diff!=1)[0]
        theoric_time = np.sum(sizes)/td['SampleRateInHz']
        if theoric_time != len(td['TimeDomainData']):
            first, second = sizes[0], sizes[1]
            for s in sizes:
                if s != [first,second]:
                    print('ghi')

def correct4MissingSamples(LFP, TicksInS, GlobalPacketSizes):
    """
    Replace missing samples with NaNs in LFP data based on received packets and their timestamps.
    
    Parameters:
        LFP: dict with 'Fs' (sampling rate in Hz) and 'data' (numpy array of shape [nChannels, nSamples])
        TicksInS: numpy array of packet timestamps in seconds
        GlobalPacketSizes: list or array of packet sizes (number of samples per packet)
    
    Returns:
        dict: Updated LFP with missing samples replaced by NaNs
    """
    

    Fs = 250  # sampling frequency
    data = LFP['Y']  # shape: (nChannels, nSamples)

    # Create time vector of all samples that should have been received theoretically
    total_samples = int(np.sum(GlobalPacketSizes))
    last_tick = TicksInS[-1] + (GlobalPacketSizes[-1] - 1) / Fs
    time = np.arange(TicksInS[0], last_tick + 1/Fs, 1/Fs)
    time = np.round(time, 3)  # round to ms

    # Create logical vector indicating which samples have been received
    isReceived = np.zeros(len(time))
    nPackets = len(GlobalPacketSizes)

    for packetId in range(nPackets):
        # Find closest index in the time vector
        print('hi')
        timeTicksDistance = np.abs(time - TicksInS[packetId])
        packetIdx = np.argmin(timeTicksDistance)

        # If this index is already received, shift forward
        if isReceived[packetIdx] == 1:
            packetIdx += 1

        # Mark the samples of this packet as received
        endIdx = packetIdx + GlobalPacketSizes[packetId]
        if endIdx > len(isReceived):
            endIdx = len(isReceived)
        isReceived[packetIdx:endIdx] += 1

    # Create corrected data array with NaNs for missing samples
    nChannels = data.shape[0]
    corrected_data = np.full((nChannels, len(time)), np.nan)

    # Fill in received samples
    sample_counter = 0
    for packetId in range(nPackets):
        n_samples = GlobalPacketSizes[packetId]
        for ch in range(nChannels):
            corrected_data[ch, sample_counter:sample_counter+n_samples] = data[ch, sample_counter:sample_counter+n_samples]
        sample_counter += n_samples

    # Update LFP structure
    LFP_corrected = LFP.copy()
    LFP_corrected['Y'] = corrected_data
    LFP_corrected['X'] = time
    print('bye')

    return LFP_corrected

def follows_pattern(lst, pattern=[38, 24, 38, 25]):
    pattern_len = len(pattern)
    deviations = [i for i, val in enumerate(lst) if val != pattern[i % pattern_len]]
    return deviations

def check_stream_data(data, signal=None, expected_tick_step=250):
    """
    Checks a data stream for missing sequences, length mismatches, and irregular tick intervals.
    
    Parameters:
        data (dict): Dictionary containing 'GlobalSequences', 'GlobalPacketSizes', 'TicksInMses'
        expected_tick_step (int): Expected difference between consecutive ticks in milliseconds
    
    Returns:
        dict: Report containing missing sequences, length mismatches, and irregular tick indices
    """
    # Convert strings to lists
    sequences = utl.string2numbers(data['GlobalSequences'])
    packet_sizes = utl.string2numbers(data['GlobalPacketSizes']) 
    ticks = utl.string2numbers(data['TicksInMses'])  

    # ticks, packet_sizes = deduplicate_packets(ticks, packet_sizes)

    new_ticks = [(t - ticks[0])/1000 for t in ticks]
    print(len(new_ticks))
    if max(new_ticks)>=sum(packet_sizes)/250: 
        print('Missing samples: ', int(max(new_ticks)*250-sum(packet_sizes)))
        deviations = follows_pattern(packet_sizes)
        print(deviations)
        

# # Example usage
# streaming = data['Indefinite']['IndefiniteStreaming'] #['BrainSenseTimeDomain']

# indefinite = DH.getSignals(data,'Indefinite')

# for idx, s in enumerate(streaming):
#     result = check_stream_data(s, indefinite[idx])


# import dearpygui.dearpygui as dpg

# dpg.create_context()

# dpg.show_imgui_demo()
# dpg.create_viewport(title="Tooltip vs Popup", width=720, height=480)
# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()


# dpg.create_context()

# tab_label = "this"

# signals,labels,colors = [],[],[]

# # Generate a test signal: sum of two sine waves
# fs = 250  # sampling frequency (Hz)
# # t = np.linspace(0, 15, 2 * fs, endpoint=False)
# # signal = np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 102 * t)
# # signal = 0.5 * np.sin(2 * np.pi * 101 * t)


# signal_info = DH.getSignals(Data,'Streaming')[:1]

# for stream in signal_info:

#     signal = np.array(stream['Y'])
#     # Compute spectrogram
#     t = np.array(stream['X'])
#     f, t_spec, Sxx = spectrogram(signal, fs=fs)

#     signals.append([f, t_spec, Sxx])

# num_plots = len(signals)
# num_cols = 2
# num_rows = (num_plots + 1) // num_cols 
# limits = []
# ploted_signals, labels = [],  []

# def exp(sender,app_data,user_data):
#     info,type = user_data
#     ft.export_plot(info,type)
    

# with dpg.window():
#     with dpg.group(horizontal=True, parent=f"{tab_label}", tag=f"{tab_label}_plot_group"):

#         dpg.add_colormap_scale(tag=f"{tab_label}_colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Jet,
#                                             height=400*num_rows)
        
#         with dpg.subplots(rows=num_rows, columns=num_cols, label="Spectrograms", width=800, height=400*num_rows, tag=f"{tab_label}_subplots"):
#             for _,signal in enumerate(signals):
#                 frequencies, times, Sxx = signal
#                 Sxx_log = 10 * np.log10(Sxx + 1e-10)  # Convert to dB scale
#                 ploted_signals.append([frequencies, times,Sxx_log])
#                 plot_tag = f"{tab_label}_{_}"
#                 with dpg.plot(label='Spectrogram', width=-1, height=-1, tag = plot_tag):
#                     dpg.add_plot_legend()
#                     x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
#                     y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")
#                     Sxx_log = np.flipud(Sxx_log)
#                     t = dpg.add_heat_series(Sxx_log.flatten(), rows=Sxx.shape[0], cols=Sxx.shape[1],
#                                             scale_min=np.min(Sxx_log), scale_max=np.max(Sxx_log), 
#                                             parent=y_axis, format="", bounds_min=[0,0], bounds_max=[times[-1],125])
                                         
#                     dpg.bind_colormap(plot_tag, dpg.mvPlotColormap_Jet)
#                     config = dpg.get_item_configuration(t)
#                     mins = config.get('bounds_min')
#                     maxs = config.get('bounds_max')
#                     xlim = [mins[0],maxs[0]]
#                     ylim = [mins[1],maxs[1]]
#                     density = [config.get('scale_min'),config.get('scale_max')]
#                     limits.append([xlim,ylim,density])
#                     labels.append('Spectrogram')
#                     # plot_limits = [dpg.get_axis_limits(t) for t in [x_axis,y_axis]]
#                     # plot_limits.append([np.min(Sxx_log),np.max(Sxx_log)])
#                     # limits.append(plot_limits)
#                     # print(dpg.get_item_configuration(t))

            

#             title = dpg.get_item_label(plot_tag)
#             axis_labels = [dpg.get_item_label(x_axis),dpg.get_item_label(y_axis), dpg.get_item_label(f"{tab_label}_colormap_scale")]
#             colors = []

#             info = ploted_signals,labels,colors,title,axis_labels, limits
#     dpg.add_button(label='Save',callback=exp,user_data=(info,'3D'),parent=tab_label)
            

# dpg.create_viewport(title='Temporario', width=800, height=600)
# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()

