
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

M = len(stream['X'])
NW = 3

print(M**2/(M**2+NW))

