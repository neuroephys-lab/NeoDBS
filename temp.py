
import matplotlib.pyplot as plt    
import DataHandling as DH
import Preprocessing as pre
import numpy as np
                                                                                          
'''nSamples = 1000                                                                           
win_size = nSamples // 4                                                                  
# create a slepian sequence of 6 orthogonal tapers                                        
slepians = windows.dpss(win_size, NW=2, Kmax=6)                                           
signal = randn(nSamples)                                                                  
                                                                                          
nSamples = 1000
t = np.linspace(0, 1000, nSamples, endpoint=False)
sig = ss.square(2 * np.pi * 5 * t)

'''

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"
Data = DH.getData(file_path)
stream = DH.getSignals(Data, 'Streaming')[0]

def fill_params(func, replace, module):


    params = pre.get_required_params(func, module)

    parameters = {}
    for name, param in params.items():            
        if param == None:
            value = ""
        
        else:
            value = param

        parameters[name] =value

    if func == 'dpss':
        parameters['NW'] = 3
        parameters['Kmax'] = int(parameters['NW'])*2 -1
        parameters['M'] = len(stream['X'])
        

    if replace != {}:
        for name, value in replace.items():
            parameters[name] = value
    
    return parameters

parameters = fill_params('dpss',{}, module='ssw')


windows = pre.call_function('dpss',param_dict=parameters,module='ssw')

power_combined = []
for order, taper in enumerate(windows):
    
    replace = {
        'x': stream['Y'],
        'fs': 250, 
        'window': taper,
        'nperseg': len(stream['Y'])
    }
    welch_params = fill_params('welch',replace, module='ss')

    freq, psd = pre.call_function('welch',param_dict=welch_params,module='ss')
    power_combined.append(psd)
    power_sum = np.abs(psd).mean()


power_combined = np.mean(power_combined, axis=-2)
params = {
    'x': stream['Y'],
    'fs': 250
}

rep = {
    'x': np.array(stream['Y']),
    'sfreq': 250
}

multi_params = fill_params('psd_array_multitaper',replace=rep, module='mtf')

multitaper, freqs = pre.call_function('psd_array_multitaper', multi_params, module='mtf')


plt.figure()

mask1 = freqs <= 100
mask2 = freq <= 100

multitaper = np.array([m*100/np.max(multitaper[mask1]) for m in multitaper])
power_combined = np.array([m*100/np.max(power_combined[mask2]) for m in power_combined])

plt.plot(freqs[mask1], multitaper[mask1], label = 'multitaper mne')
plt.plot(freq[mask2], power_combined[mask2], label="welch_dpss")

plt.legend()
plt.show()