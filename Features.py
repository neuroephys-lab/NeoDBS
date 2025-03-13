import numpy as np

def peak_power(stream):
    '''
    Receives a stream with PSD values
    '''
    peak_idx = np.argmax(stream["Y"])
    peak_f = stream["X"][peak_idx]
    peak_power = stream["Y"][peak_idx]

    return [peak_f, peak_power]
    
def mean_power_band(stream,band):
    #events
    power = []
    
    fi,ff = band
    for side in ['Left', 'Right']:
        temp = []
        log = stream[side]
        freq = log['X']
        pwr = log['Y']
        for idx, f in enumerate(freq):
            if fi<=f<=ff: temp.append(pwr[idx])
        if temp:
            power.append(np.mean(temp))

    return np.mean(power) if power else np.nan 