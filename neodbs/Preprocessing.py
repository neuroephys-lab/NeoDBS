import DataHandling as DH
import utils as utl
import numpy as np
from datetime import timedelta,datetime
import inspect
from scipy import optimize
from scipy import signal as ss
import scipy.integrate as si
import scipy.signal.windows as ssw
import mne.time_frequency as mtf
#-----------------------------------------NeoDBS-------------------------------------------------

#------------------ Easy Access to Scipy.signal---------------------
'''
Matlab-style IIR filter design
'''
iir_filter_design_functions = ['butter','buttord','cheby1','cheb1ord','cheby2','cheb2ord','ellip',
                               'ellipord','bessel','iirnotch','iirpeak', 'iircomb']


def get_functions(module = 'ss'):
    '''
    Retrieves and saves all functions names and callbacks into a dictionary

    Modules:
        - 'ss': scipy.signal
        - 'mtf': mne.time_frequency
        - 'si': scipy.integrate
        - 'ssw': scipy.signal.windows
        - 'np': numpy
    
    :param module: str

    :return: dict, {func_naame: obj}

    '''

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
    return functions

def extract_params_and_returns(docstring: str) -> str:
    '''
    Extracts the 'Parameters' and 'Returns' sections from a Numpydoc-formatted
    documentation string.

    :param docstring: str, documentation string of a function.

    :return: A string containing only the 'Parameters' and 'Returns' sections.

    '''
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

def call_function2(func_name, *args, **kwargs):
    '''
    Call a function from scipy.signal by name, print its documentation, and handle exceptions.
    If given arguments dont work, function retries with default arguments given by module.

    :param func_name: str, function name
    :param args: dict, required arguments
    :param kwargs: dict, optional keyword arguments

    :return: output of func(*args,**kwargs)

    '''
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
    '''
    Call a function from module by name, print its documentation, and handle exceptions.
    If given arguments dont work, function retries with default arguments given by module.

    Modules:
        - 'ss': scipy.signal
        - 'mtf': mne.time_frequency
        - 'si': scipy.integrate
        - 'ssw': scipy.signal.windows
        - 'np': numpy

    :param func_name: str, function name
    :param param_dict: dict, required and optional arguments
    :param module: str, module name

    :return: output of func(*args,**kwargs)

    '''
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
    '''
    Retrieves required parameters, and default values, from func_name.

    Modules:
        - 'ss': scipy.signal
        - 'mtf': mne.time_frequency
        - 'si': scipy.integrate
        - 'ssw': scipy.signal.windows
        - 'np': numpy
    
    :param func_name: str, function name
    :param module: str, module name. Defaults to ss
    :return: dict
    '''

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
    '''
    Retrieves optional keywords parameters, and default values, from func_name.

    Modules:
        - 'ss': scipy.signal
        - 'mtf': mne.time_frequency
        - 'si': scipy.integrate
        - 'ssw': scipy.signal.windows
        - 'np': numpy
    
    :param func_name: str, function name
    :param module: str, module name. Defaults to ss
    :return: dict
    '''

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

def get_date_from_ts(ts):
    '''
    Returns datetime object correspondant to the given timestamp ts
    
    :param ts: int/float
    :return: datetime.datetime
    '''
    return datetime.fromtimestamp(ts)
#----------------------------- NeoDBS signal processing functions------------------


def MeanSignal(signals, key = 'Y'):
    '''
    Calculates and return mean from specific key in signal dictionary, item of signals list
    
    :param signals: list
        list of dictionaries of signal data.
    :param key: str/int, default to 'Y'
        key of dictionary
    :return: np.array
        computed mean
    '''
    yy=[signal[key] for signal in signals]
    
    mean_signal = np.nanmean(yy, axis=0)
    return mean_signal

def StdDevSignal(signals, key = None):
    '''
    Calculates and return standard deviation from specific key in signal dictionary, item of signals list
    
    :param signals: list, list of dictionaries of signal data.
    :param key: str/int
    :return: np.array
    '''
    if key == None: key = 'Y'
    
    yy=[signal[key] for signal in signals]
    
    mean_signal = np.nanstd(yy, axis=0)
    return mean_signal

#---Power Normalization

def convert_to_db(value):
    '''
    Convert a value to dB scale using 10 * log10.
    
    :param value: int/float
    :return: int/float
    '''
    if isinstance(value, (np.ndarray,tuple)):  # Handle peak values (power, frequency)
        return (round(10 * np.log10(value[0]+1e-6), 2), value[1])
    elif isinstance(value,list): 
        try:
            result = [round(float(10*np.log10(s + 1e-6)),2) for s in value]
            return result
        except Warning:
            print(value)
    elif isinstance(value, (int, float)):
        try:
            result = round(10 * np.log10(value+1e-6), 2)
            return result
        except Warning: print(value)
    return value  # Return unchanged if it's a string or invalid type
 
def convert_from_db(value):
    '''
    Convert a dB value back to linear scale using 10^(dB/10).
    
    :param value: int/float
    :return: int/float
    '''
    
    if isinstance(value, (np.ndarray,tuple)):  # Handle peak values (power, frequency)
        return (round(10**(value[0] / 10), 2) if value[0] != float('-inf') else 0, value[1])
    elif isinstance(value,list):
        return [round(float(10**(s / 10) - 1e-6),2) for s in value]
    elif isinstance(value, (int, float)):
        return round(10**(value / 10), 2) if value != float('-inf') else 0
    return value  # Return unchanged if it's a string or invalid type
# -------------------------------------- BRAVO -------------------------------------

def removeCardiacComponent(raw, band, filterMethod="Fixed Peak Find"):
    '''
    Applies 5th order Butterworth bandpass filter with cardiac artifact removal. With Wiener Filter and scipy.find_peaks, an ECG template is created and subtracted to the filtered signal, removing the cardiac component.
    Adapted from https://github.com/Fixel-Institute/BRAVO_SSR/blob/main/modules/LocalPerceptDatabase.py#L327
    
    :param raw: dict, {'Y': signal values}
    :param band: Description
    :param filterMethod: Description
    :return: filtered signal, signal with only bandpass
    '''

    a,b = band
    if a == 0: a = 0.01
    if b == 0: b = 100

    band = np.array([a,b])

    filtered = raw['Y']
    fs = 250

    [p1,p2] = ss.butter(5, band, 'bp', output='ba',fs=fs)
    

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
    return filtered, buttered
    

