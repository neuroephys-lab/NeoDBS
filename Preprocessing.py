import DataHandling as DH
import utils as utl
import numpy as np
from datetime import datetime, timedelta
import inspect

#-----------------------------------------NeoDBS-------------------------------------------------

#------------------ Easy Access to Scipy.signal---------------------
'''
Matlab-style IIR filter design
'''
iir_filter_design_functions = ['butter','buttord','cheby1','cheb1ord','cheby2','cheb2ord','ellip',
                               'ellipord','bessel','iirnotch','iirpeak', 'iircomb']


def get_functions(module):
    """Retrieve all callable functions from a module."""

    functions = {name: obj for name, obj in inspect.getmembers(module, inspect.isfunction)}
    return functions

def dict_to_arg(param_dict, module, func_name):
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

def call_function2(module, func_name, *args, **kwargs):
    """Call a function from a module by name, print its documentation, and handle exceptions."""
    functions = get_functions(module)
    
    if func_name not in functions:
        print(f"Function '{func_name}' not found in {module.__name__}")
        return None

    func = functions[func_name]

    # Print function documentation
    print(f"\nDocumentation for '{func_name}':\n")
    #print(func.__doc__ if func.__doc__ else "No documentation available.")
    print("\n" + "="*80 + "\n")

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

def call_function(module, func_name, param_dict):
    """Call a function from a module using saved parameters."""
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
                converted_params[key] = eval(value) if value.strip() else None
            except:
                converted_params[key] = value  # Keep as string if eval fails

    # Split into positional and keyword arguments
    args = [converted_params[param] for param in required_params if param in converted_params]
    kwargs = {k: v for k, v in converted_params.items() if k not in required_params}

    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error calling {func_name}: {e}")
        return None

def get_required_params(module,func_name):
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

def get_default_kwargs(module,func_name):

    functions = get_functions(module)
    
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

def MeanSignal(signals):
    yy=[signal['Y'] for signal in signals]
    
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


# -------------------------------------- BRAVO -------------------------------------

def rangeSelection(array, minMax, type="exclusive"):
    if type=="exclusive":
        return np.bitwise_and(array < minMax[1], array > minMax[0])
    else:
        return np.bitwise_and(array <= minMax[1], array >= minMax[0])

def removeOutlier(data, method="zscore", zlim=3):
    if method == "zscore":
        return data[rangeSelection(data, [np.mean(data)-np.std(data)*zlim,np.mean(data)+np.std(data)*zlim])]
