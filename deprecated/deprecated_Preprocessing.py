import numpy as np

def band_normalization(stream, freq_range):
    total_power = np.sum([y for f, y in zip(stream['X'], stream['Y']) if freq_range[0] <= f <= freq_range[1]])
    return [np.round(v / total_power, 2) if total_power > 0 else 0 for v in stream['Y']]

def band_normalization_db(stream, freq_range):
    total_power = np.sum([y**2 for f, y in zip(stream['X'], stream['Y']) if freq_range[0] <= f <= freq_range[1]])
    return [10 * np.log10(v**2 / (total_power + 1e-6)) if total_power > 0 else -np.inf for v in stream['Y']]

def log_normalization(stream):
    log_values = np.log1p(stream['Y'])
    log_min, log_max = min(log_values), max(log_values)
    return [(v - log_min) / (log_max - log_min) for v in log_values]

def log_normalization_db(stream):
    return [10 * np.log10(v + 1e-6) for v in stream['Y']]  # Convert power to dB

def zscore_normalization(stream):
    return (stream['Y'] - np.mean(stream['Y'])) / np.std(stream['Y'])

def zscore_normalization_db(stream):
    z_scored = (stream['Y'] - np.mean(stream['Y'])) / np.std(stream['Y'])
    return [10 * np.log10(v**2 + 1e-6) for v in z_scored]  # Convert z-score to dB

def within_band_normalization(stream, freq_range):
    '''
    Normalize only the values within the frequency band by their own total power.
    Other frequencies remain unchanged.
    '''
    band_indices = [i for i, f in enumerate(stream['X']) if freq_range[0] <= f <= freq_range[1]]
    total_band_power = np.sum([stream['Y'][i] for i in band_indices])

    normalized_Y = stream['Y'].copy()
    for i in band_indices:
        normalized_Y[i] = np.round(stream['Y'][i] / total_band_power, 2) if total_band_power > 0 else 0

    return normalized_Y

def within_band_normalization_db(stream, freq_range):
    band_power = np.sum([y**2 for f, y in zip(stream['X'], stream['Y']) if freq_range[0] <= f <= freq_range[1]])
    return [10 * np.log10(v**2 / (band_power + 1e-6)) if band_power > 0 else -np.inf for v in stream['Y']]
