import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
import utils as utl
from pathlib import Path

bands = {
            'Delta': [0.01,4],
            'Theta': [4,8],
            'Alpha': [8,12],
            'Beta': [12,30],
            'Gamma': [30,100]
        }

def peak_power(stream):
    '''
    From stream dictionary, return tuple with peak value and peak position.
    
    :param stream: dict, signal information 'X'/'Frequency' --> x axis; 'Y'/'Power' --> y axis
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
    '''
    Retrives all peak values and positions, in stream, for each band.
    
    :param stream: dict, signal information 'X'/'Frequency' --> x axis; 'Y'/'Power' --> y axis
    :param bands: dict, 'band name': [f0,f1]
    '''
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
   
def std_dev_streams(streams, bands):
    '''
    Calculates and returns a dictionary of band-respective standard deviation
    
    :param stream: dict, signal information 'X'/'Frequency' --> x axis; 'Y'/'Power' --> y axis
    :param bands: dict, 'band name': [f0,f1]
    :return: dict, 'band name': float standard deviation
    '''

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
            std_devs[name] = np.nanstd(stacked_powers)  
        else:
            std_devs[name] = None  # No data for this band

    return std_devs   

def mean_power_band(log,band):
    '''
    Calculates and returns a dictionary of band-respective mean
    
    :param stream: dict, signal information 'X'/'Frequency' --> x axis; 'Y'/'Power' --> y axis
    :param bands: dict, 'band name': [f0,f1]
    :return: np.array, mean power
    '''
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

    return np.nanmean(power) if power else np.nan 

def get_sum_mean_power(p,band=None):
    '''
    Calculates and returns the sum of all band's mean power
    
    :param p: dict, computed PSD ('X' = freqs, 'Y' = psd values)
    :param bands: dict, 'band name': [f0,f1]
    :return: float
    '''
    if band == None: 
        band = bands
    x,y=p['X'],p['Y']
    all = []
    if isinstance(x,list):
        x = np.array(x)
        y = np.array(y)

    for _,v in band.items():
        mask = (x >= v[0]) & (x <= v[1])
        temp = y[mask]
        all.append(np.nanmean(temp))
        
    return np.sum(all)

def extract_psd_features(p, band, bands=None):
    '''
    Extracts features from spectral density, or coherence, methods. Returns dictionary. 

    Features: 
    - Mean Power (mean, std. dev)
    - % Mean Power (mean, std. dev)
    - Sum Power (AUC)
    - % Sum Power (AUC)
    - Peak Power (power, frequency)']
    
    :param p: dict, computed PSD ('X' = freqs, 'Y' = psd values)
    :param band: list, band[0] = str, band name; band[1] = list, [f0,f1]
    :return: dict, {feature: value}
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

    Features:
    - Mean Power (mean, std. dev)
    - Peak Power
    - Peak Time
    - Sensing Freq. (Hz)

    :param p: dict, computed PSD ('X' = time array, 'Y' = lfp timeline values)
    :return: dict, {feature: value}
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
    elif isinstance(time, np.ndarray):
        if np.any(np.isnan(time)):
            return
    elif isinstance(time,float):
        if np.isnan(time):
            return
        peak = str(datetime.fromtimestamp(time).time())
    else: #datetime.datetime object
        peak=str(time.time())

    time = {key: peak}
    info = mean | picos | time
    if 'Sense' in p.keys():
        sense = {'Sensing Freq. (Hz)': [np.round(p['Sense']-2.5,2),np.round(p['Sense']+2.5,2)]}
        info = info| sense

    return info

def mean_power_all_bands(stream, bands):
    '''
    Computes mean power for frequency bands over a stream of events.

    
    :param stream: Description
    :param bands: Description
    :return: dict, {band: mean}
    '''
    
    # Ensure stream is iterable
    if not isinstance(stream, (list, tuple, np.ndarray)):  
        stream = [stream]  # Convert single event to a list

    power_values = {band: [] for band in bands}

    # Process each event
    for event in stream:
        for band, freq_range in bands.items():
            power_values[band].append(mean_power_band(event, freq_range))

    # Compute mean power for each band
    power = {band: np.nanmean(values) if values else 0 for band, values in power_values.items()}

    return power

def export_plot(info, plot_type, size=None, line_types = None,dpi=600):
    '''
    Creates matplolib plot and exports it into png image, according to the prepared info in dearpygui.
    
    If plot_type is '2D' or 'CC' (Timeline/normal PSD or cross-correlation): 
        - signals: list of dicts
        - colors: list, rgba codes

    If plot_type is '3D' or '3DC' (spectrogram or coherogram): 
        - signals: list of tuples.
        - colors: str, name of colormap

    If plot_type is 'Bar' or 'Events' (phase-amplitude coupling or event summary): 
        - signals: list of dicts.
        - colors: list, rgba codes

    If plot_type is 'SMP' (Show Mean Power over time): 
        - signals: dict, 'Y1': signals plotted on left y axis, 'Y2': signals plotted on right y axis.
        - colors: list, rgba codes

    If plot_type is 'Pie' (phase-amplitude coupling or event summary): 
        - signals: single list of values.
        - colors: list, rgba codes
    
    :param info: signals (list), labels (list of signal's labels), colors (list), title (str, name of plot), axis (list, names of axis), limits (list, range of axis)
    :param plot_type: str, type of plot: '2D' (Timeline/PSD), 'CC' (cross-correlation), '3D' (spectrogram), '3DC' (coherogram), 'Bar' (phase-amplitude coupling), 'Events' (event summary), 'Pie' (event summary count)
    :param size: tuple, width and height of original plot. Optional, default to None, width and height are set to default fig sizes of matplotlib
    :param line_types: list, type of line plotted in dpg. Optional, default to None.
    '''

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
                ax.scatter(x,y,label=label,color=colors[i],zorder=len(signals))
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

    elif plot_type == 'SMP':
        fig, ax = plt.subplots(figsize=(size[0],size[1]))

        if axis[-1] != '':
            secay = ax.twinx()
            secay.set_ylabel(axis[3])
            secay.set_ylim(*limits[3])
            secax = ax.twiny()
            secax.set_xlabel(axis[2])
            secax.set_xlim(*limits[2])
        
        for i, signal in enumerate(signals['Y1']):
            key = 'Y1'
            if 'Scatter' in line_types[key][i]:
                ax.scatter(signal['X'],signal['Y'],label=labels[key][i], color=colors[i])
            else:
                ax.plot(signal['X'],signal['Y'],label=labels[key][i],color=colors[i])

        for i, signal in enumerate(signals['Y2']):
            key = 'Y2'
            if 'Scatter' in line_types[key][i]:
                secay.scatter(signal['X'],signal['Y'],label=labels[key][i],color=colors[i+len(signals['Y1'])])
            else:
                secay.plot(signal['X'],signal['Y'],label=labels[key][i],color=colors[i+len(signals['Y1'])],linewidth=3)
        
        ax.set_title(title)
        ax.set_xlabel(axis[0])
        ax.set_ylabel(axis[1])
        ax.set_xlim(*limits[0])
        ax.set_ylim(*limits[1])

        fig.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=False)

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
            labels = [None]*len(signals)

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

    output_path = Path(f"{title}.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(f'{title}.png', bbox_inches='tight',dpi=dpi) #

    plt.close(fig)

def export_signals(info,filename, tfd = False):
    '''
    Writes into "Signals_{filename}.csv" file, signals contained in info dictionary.
    
    :param info: dict, keys are columns
    :param filename: str, name of file
    :param tfd: Optional. Default to False, if True exports 3D signals (spectrogram/coherogram)
    '''
    filename = filename.replace(' - ','_')
    filename = filename + ".csv"
    old_filename = filename
    if tfd:
        for spec in info:
            (plot_title, value), = spec.items()
            filename = old_filename[:-3] + plot_title + ".csv"
            filename = filename.replace(' | ','_')
            filename = filename.replace(':','_')
            with open(filename, "w") as f:
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
