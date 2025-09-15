import DataHandling as DH
import utils as utl
import numpy as np
from datetime import timedelta
import inspect
from scipy import optimize
from scipy import signal as ss
import scipy.integrate as si
import scipy.signal.windows as ssw
import mne.time_frequency as mtf
import re
#-----------------------------------------NeoDBS-------------------------------------------------

#------------------ Easy Access to Scipy.signal---------------------
'''
Matlab-style IIR filter design
'''
iir_filter_design_functions = ['butter','buttord','cheby1','cheb1ord','cheby2','cheb2ord','ellip',
                               'ellipord','bessel','iirnotch','iirpeak', 'iircomb']


def get_functions(module = 'ss'):

    match module:
        case 'ss': module = ss
        case 'mtf': module = mtf
        case 'si': module = si
        case 'ssw': module = ssw
        case 'np': module = np

    functions = {}
    for name, obj in inspect.getmembers(module, inspect.isroutine):
        try:
            functions[name] = obj
        except Exception as e:
            print(f"Skipping function {name} due to error: {e}")

    '''"""Retrieve all callable functions from a module, handling errors gracefully."""
    functions = {}
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        try:
            functions[name] = obj  # Attempt to retrieve function
        except Exception as e:
            print(f"Skipping function {name} due to error: {e}")'''
    return functions

def extract_params_and_returns(docstring: str) -> str:
    """
    Extracts the 'Parameters' and 'Returns' sections from a Numpydoc-formatted
    documentation string.

    Args:
        docstring (str): The documentation string of a function.

    Returns:
        str: A string containing only the 'Parameters' and 'Returns' sections.
    """
    lines = docstring.splitlines()

    sections_to_extract = {"Parameters", "Returns"}
    section_content = {section: [] for section in sections_to_extract}
    
    current_section = None
    capture = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Start of a new section
        if stripped in sections_to_extract:
            current_section = stripped
            capture = True
            section_content[current_section].append(line)  # add header
            continue
        elif stripped in {"See Also", "Notes", "Examples"}:
            capture = False
            current_section = None
            continue

        # Capture content under current section
        if capture and current_section:
            # Append blank lines and indented lines (part of parameter/return description)
            if line.strip() or (section_content[current_section] and section_content[current_section][-1].strip()):
                section_content[current_section].append(line)

    # Combine captured sections into final output
    output_lines = []
    for section in ("Parameters", "Returns"):
        if section_content[section]:
            output_lines.extend(section_content[section])
            output_lines.append("")  # spacing between sections

    return "\n".join(output_lines).strip()

def extract_params_and_returns2(docstring: str) -> str:
    """
    Extracts the 'Parameters' and 'Returns' sections from a Numpydoc-formatted
    documentation string.

    Args:
        docstring (str): The documentation string of a function.

    Returns:
        str: A string containing only the 'Parameters' and 'Returns' sections.
    """
    lines = docstring.splitlines()
    
    in_parameters_section = False
    in_returns_section = False
    
    extracted_content = []

    for line in lines:
        stripped_line = line.strip()

        if stripped_line == "Parameters":
            in_parameters_section = True
            in_returns_section = False
            extracted_content.append(line)  # Include the "Parameters" header
            continue
        elif stripped_line == "Returns":
            in_returns_section = True
            in_parameters_section = False
            extracted_content.append(line)  # Include the "Returns" header
            continue
        elif stripped_line == "See Also":
            in_parameters_section = False
            in_returns_section = False
            break  # Stop processing once "See Also" or similar sections are encountered
        elif stripped_line == "Notes":
            in_parameters_section = False
            in_returns_section = False
            break
        elif stripped_line == "Examples":
            in_parameters_section = False
            in_returns_section = False
            break
        
        if in_parameters_section or in_returns_section:
            # Check if the line is part of the current section
            # A common way to check if a line is part of a section in numpydoc
            # is to look for indentation.
            if line.strip() != "": # Exclude empty lines if they break the flow
                 extracted_content.append(line)

    # Clean up by removing leading/trailing whitespace from each line
    # and then joining them back. Also remove any empty lines that might have
    # been appended in between sections.
    cleaned_content = [line.strip() for line in extracted_content if line.strip()]
    
    # Reconstruct with indentation for better readability, if desired.
    # This part can be more complex if you want to preserve exact original indentation.
    # For now, we'll just join them with newlines.
    
    # A simple way to manage indentation is to add a space for subsequent lines
    # that are not headers.
    final_output_lines = []
    current_section_header = None
    
    for line in extracted_content:
        if line.strip() == "Parameters" or line.strip() == "Returns":
            final_output_lines.append(line.strip())
            current_section_header = line.strip()
        elif line.strip(): # if line is not empty
            if current_section_header:
                if current_section_header == "Parameters" and not line.startswith("    "):
                    # This implies it's a parameter name, not its description
                    final_output_lines.append(line.strip())
                elif current_section_header == "Returns" and not line.startswith("    "):
                    # This implies it's a return value name, not its description
                    final_output_lines.append(line.strip())
                else:
                    final_output_lines.append(line)
            else: # If we are not in a recognized section, just add the line
                final_output_lines.append(line)

    return "\n".join(final_output_lines).strip()

def dict_to_arg(param_dict, func_name, module = 'ss'):
    # Convert saved parameters (strings) into appropriate types
    required_params = get_required_params(module,func_name)

    default_kwargs = get_default_kwargs(module,func_name)

    converted_params = {}
    for key, value in param_dict.items():
        if key in required_params or key in default_kwargs:  # Ensure it's a valid argument
            try:
                converted_params[key] = eval(value) if value.strip() else None
            except:
                converted_params[key] = value  # Keep as string if eval fails
    return converted_params

def call_function2(func_name, *args, **kwargs):
    """Call a function from a module by name, print its documentation, and handle exceptions."""
    module = ss
    functions = get_functions()
    
    if func_name not in functions:
        print(f"Function '{func_name}' not found in {module.__name__}")
        return None

    func = functions[func_name]

    
    # Get function signature
    sig = inspect.signature(func)
    
    # Extract required parameters (no defaults)
    required_params = [
        param.name for param in sig.parameters.values()
        if param.default is inspect.Parameter.empty and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY)
    ]
    
    # Extract keyword default parameters
    default_kwargs = {
        param.name: param.default for param in sig.parameters.values()
        if param.default is not inspect.Parameter.empty and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }

    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error calling {func_name}: {e}")

        if args:
            print("Error occurred even with provided arguments. Not retrying.")
            return None  # If the user provided arguments, don't retry

        if required_params:
            print(f"Cannot retry because required positional arguments are missing: {required_params}")
            return None  # Can't call the function without required positional args
        
        if default_kwargs:
            print("Retrying with default keyword arguments...")
            try:
                return func(**default_kwargs)
            except Exception as e2:
                print(f"Error with default parameters as well: {e2}")
                return None
        else:
            print("No default parameters available.")
            return None

def call_function(func_name, param_dict, module = 'ss'):
    """Call a function from a module using saved parameters."""
    match module:
        case 'ss': module = ss
        case 'mtf': module = mtf
        case 'si': module = si
        case 'ssw': module = ssw
        case 'np': module = np

    functions = get_functions(module)
    
    if func_name not in functions:
        print(f"Function '{func_name}' not found in {module.__name__}")
        return None

    func = functions[func_name]
    sig = inspect.signature(func)
    # Extract required positional arguments
    required_params = [
        param.name for param in sig.parameters.values()
        if param.default is inspect.Parameter.empty and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY)
    ]

    # Extract keyword default parameters
    default_kwargs = {
        param.name: param.default for param in sig.parameters.values()
        if param.default is not inspect.Parameter.empty and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }

    # Convert saved parameters (strings) into appropriate types
    converted_params = {}
    for key, value in param_dict.items():
        if key in required_params or key in default_kwargs:  # Ensure it's a valid argument
            try:
                # Ensure empty strings become None, and evaluate only if value is not empty
                if value.strip() == "":
                    converted_params[key] = None
                elif value.lower() == "none":
                    converted_params[key] = None
                elif value.lower() == "inf":
                    converted_params[key] = float("inf")
                else:
                    converted_params[key] = eval(value)  # Convert numbers and lists
            except Exception:
                converted_params[key] = value  # Keep as string if eval fails

    # Split into positional and keyword arguments
    args = [converted_params[param] for param in required_params if param in converted_params]
    kwargs = {k: v for k, v in converted_params.items() if k not in required_params}


    try:
        return func(*args, **kwargs)
    except Exception as e:
        error = f"Error calling {func_name}: {e}"
        return error

def get_required_params(func_name, module = 'ss'):

    match module:
        case 'ss': module = ss
        case 'mtf': module = mtf
        case 'si': module = si
        case 'ssw': module = ssw
        case 'np': module = np
    functions = get_functions(module)
    
    if func_name not in functions:
        print(f"Function '{func_name}' not found in {module.__name__}")
        return None

    func = functions[func_name]
    sig = inspect.signature(func)

    required_params = {}
    
    for name, param in sig.parameters.items():
        if param.default is inspect.Parameter.empty:
            required_params[name] = None  # No default value
        else:
            required_params[name] = param.default  # Default value exists

    return required_params

def get_default_kwargs(func_name,module = 'ss'):

    functions = get_functions(module)

    match module:
        case 'ss': module = ss
        case 'mtf': module = mtf
        case 'si': module = si
        case 'ssw': module = ssw
    
    if func_name not in functions:
        print(f"Function '{func_name}' not found in {module.__name__}")
        return None

    func = functions[func_name]
    sig = inspect.signature(func)
    
    default_kwargs = {
        param.name: param.default for param in sig.parameters.values()
        if param.default is not inspect.Parameter.empty and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }

    return default_kwargs


#----------------------------- NeoDBS signal processing functions------------------

#def MAD based removal
# def wavelet denoising 


def zscoreRemoval(signal,n):
    '''
    Signal - dict with 'X' and 'Y' keys
    returns:
    1. signal with the removed outliers following the z score method
    2. the removed points
    
    '''
    #maybe only return the mask ?? --> apply the mask in GUI

    x = np.array(signal['X'])
    y = np.array(signal['Y'])
    

    threshold = n*np.std(y)
    mask = np.abs(y-np.mean(y)) < threshold
    
    removed_x = x[~mask]  # Values where mask is False
    removed_y = y[~mask]
    

    filtered_x = x[mask]
    filtered_y = y[mask]
    
    cleaned = {'X': filtered_x.tolist(), 'Y': filtered_y.tolist()}
    removed = {'X': removed_x.tolist(), 'Y': removed_y.tolist()}

    return cleaned, removed  # Convert back to lists if needed

def MeanSignal(signals, key = None):
    if key == None: key = 'Y'
    
    yy=[signal[key] for signal in signals]
    
    mean_signal = np.mean(yy, axis=0)
    return mean_signal

def MeanEvents(signals):
    #for events, only mean(y)
    yy = []
    for signal in signals:
        for side in ['Left', 'Right']: #verificar isto para quando se selecionar só um lado
            sign = signal[side]
            yy.append(sign['Y'])

    mean_signal = np.mean(yy, axis=0)
    return mean_signal

def checkMissingData(dictionary):


    '''
    Check missing data in the whole of dictionary, either full json file or just a recording or mode
    Return boolean matrix of missing data and the paths
    '''
    
    GlobalPacketSizes = 0
    Fs = 250

    check = []

    modes = DH.getModes(dictionary)

    for mode in modes:
        if mode== 'Streaming' or mode== 'Indefinite' or mode == 'Survey': #Streaming, Survey
                key_paths = utl.find_key_path(dictionary[mode], 'TicksInMses')

                for path in key_paths:
                    path_parts = utl.parse_path(path)
                    signal = utl.access_by_path(dictionary[mode],path_parts)
                    if 'TicksInMses' in signal.keys() and 'GlobalPacketSizes' in signal.keys() and 'SampleRateInHz' in signal.keys():
                        TickInS = utl.string2numbers(signal['TicksInMses'])
                        GlobalPacketSizes = utl.string2numbers(signal['GlobalPacketSizes'][1:-1]) #take out [ ]
                        Fs = signal['SampleRateInHz']

                        if len(TickInS)!=0:
                            TickInS = (TickInS - TickInS[0])/1000 #convert from ms to s, and start from 0
                            if TickInS[-1]>sum(GlobalPacketSizes)/Fs:
                                #print('WARNING: MISSING PACKETS IN Path: ' + path)
                                check.append(path)
                                Warning(f"Missing packets in {mode}")
                            else: pass                    
                        else: 
                            #print('WARNING: No required keys or data in Path: ' + path)
                            check.append(path)
                            Warning(f"Missing keys or data in {mode}")

                    else: 
                        #print("ERROR: No required keys or data.")
                        check.append(path)
                        Warning(f"Missing keys or data in {mode}")
        
        if mode == 'Timeline':

            key_paths = utl.find_key_path(dictionary[mode],'DateTime')
            new_paths = []
            for path in key_paths: new_paths.append(f"['{mode}']" + path + "['DateTime']")
            
            for i in  range(len(new_paths)-1):
                path1 = utl.parse_path(new_paths[i+1])
                path2 = utl.parse_path(new_paths[i])

                time1 = utl.parse_datetime(utl.access_by_path(dictionary,path1))
                time2 = utl.parse_datetime(utl.access_by_path(dictionary,path2))
                delta = time2-time1
                if delta > timedelta(days=1): 
                    print(time1 , '| ', time2, ' | ', delta)
                    
                minutes = np.round(delta.seconds/60,3)
                remainder = minutes%10
                if minutes >10 and remainder==0: #check if difference in time is bigger than 10 and multiple of ten, meaning lost a packet
                    
                    print(new_paths[i])
                    check.append(new_paths[i])
                    Warning(f"Missing packets in {mode}")

            timelines = DH.getSignals(dictionary,mode)
            for time in timelines:
                date = time['Date']
                path = utl.find_key_path(dictionary,date)

                left = len(time['Left']['X'])
                right = len(time['Right']['X'])
                if left != 144 or right != 144: #24*60/10 = 144 samples per day
                    print('Day not complete')

                    diff = utl.parse_datetime(time['Left']['X'][0]) - utl.parse_datetime(time['Left']['X'][-1])
                    packs = np.round(diff.total_seconds()/600,0)
                    if packs < left:
                        Warning(f'Missing packets in {mode}: {left-packs}')
                        check.append(path)

        if mode == 'Events': print('Still not done')  #check event logs, session date time, and lfpfrequencysnapshots  

    return check

#---Power Normalization

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
    """
    Normalize only the values within the frequency band by their own total power.
    Other frequencies remain unchanged.
    """
    band_indices = [i for i, f in enumerate(stream['X']) if freq_range[0] <= f <= freq_range[1]]
    total_band_power = np.sum([stream['Y'][i] for i in band_indices])

    normalized_Y = stream['Y'].copy()
    for i in band_indices:
        normalized_Y[i] = np.round(stream['Y'][i] / total_band_power, 2) if total_band_power > 0 else 0

    return normalized_Y

def within_band_normalization_db(stream, freq_range):
    band_power = np.sum([y**2 for f, y in zip(stream['X'], stream['Y']) if freq_range[0] <= f <= freq_range[1]])
    return [10 * np.log10(v**2 / (band_power + 1e-6)) if band_power > 0 else -np.inf for v in stream['Y']]


# -------------------------------------- BRAVO -------------------------------------

def rangeSelection(array, minMax, type="exclusive"):
    if type=="exclusive":
        return np.bitwise_and(array < minMax[1], array > minMax[0])
    else:
        return np.bitwise_and(array <= minMax[1], array >= minMax[0])

def removeOutlier(data, method="zscore", zlim=3):
    if method == "zscore":
        return data[rangeSelection(data, [np.mean(data)-np.std(data)*zlim,np.mean(data)+np.std(data)*zlim])]

def removeCardiacComponent(raw, band, filterMethod="Fixed Peak Find"):

    a,b = band
    if a == 0: a = 0.5
    if b == 0: b = 100

    band = np.array([a,b])

    filtered = raw['Y']
    fs = 250
    #Filtrar bandpass butter
    # [b,a] = ss.butter(5, band*2/fs, 'bp', output='ba')
    # filtered = ss.filtfilt(b, a, stream)
    # buttered = filtered.copy()

    #filterMethod = "Kurtosis"

    [p1,p2] = ss.butter(5, band*2/fs, 'bp', output='ba')
    

    PredictedSignal = ss.wiener(filtered, mysize=125)
    filtered -= PredictedSignal

    if filterMethod == "Fixed Peak Find":
        # Cardiac Filter
        peaks = []
        posPeaks,_ = ss.find_peaks(filtered, prominence=[10,200], distance=fs*0.5)
        PosCardiacVariability = np.std(np.diff(posPeaks))
        negPeaks,_ = ss.find_peaks(-filtered, prominence=[10,200], distance=fs*0.5)
        NegCardiacVariability = np.std(np.diff(negPeaks))

        if PosCardiacVariability < NegCardiacVariability:
            peaks = posPeaks
        else:
            peaks = negPeaks

        if len(peaks)>1:
            if None in peaks: print('None')
            CardiacRate = int(np.mean(np.diff(peaks)))

            PrePeak = int(CardiacRate*0.25)
            PostPeak = int(CardiacRate*0.65)
            EKGMatrix = np.zeros((len(peaks)-2,PrePeak+PostPeak))
            for j in range(1,len(peaks)-1):
                if peaks[j]+PostPeak < len(filtered) and peaks[j]-PrePeak > 0:
                    EKGMatrix[j-1,:] = filtered[peaks[j]-PrePeak:peaks[j]+PostPeak]

            EKGTemplate = np.mean(EKGMatrix,axis=0)
            EKGTemplate = EKGTemplate / (np.max(EKGTemplate)-np.min(EKGTemplate))

            def EKGTemplateFunc(xdata, amplitude, offset):
                return EKGTemplate * amplitude + offset

            for j in range(len(peaks)):
                if peaks[j]-PrePeak < 0:
                    pass
                elif peaks[j]+PostPeak >= len(filtered) :
                    pass
                else:
                    sliceSelection = np.arange(peaks[j]-PrePeak,peaks[j]+PostPeak)
                    params, covmat = optimize.curve_fit(EKGTemplateFunc, sliceSelection, filtered[sliceSelection])
                    filtered[sliceSelection] = filtered[sliceSelection] - EKGTemplateFunc(sliceSelection, *params)
                    ecg = EKGTemplateFunc(sliceSelection, *params)

        
        filtered = ss.filtfilt(p1, p2, filtered)
        buttered = ss.filtfilt(p1, p2, raw['Y'])
        # buttered = None

        #wavelet = waveletTimeFrequency(filtered, freq=np.arange(0.5,100.5,0.5), ma=int(fs/2), fs=fs)
        #sfft = defaultSpectrogram(stream, window=1.0, overlap=0.5, frequency_resolution=0.5, fs=fs)

        return filtered, buttered
    

