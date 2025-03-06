'''import DataHandling as DH
import matplotlib.pyplot as plt
import utils as utl
import numpy as np
import Preprocessing as pre'''

import DataHandling as DH
import scipy.signal
import Preprocessing as pre

# Set the base directory where JSON files are located
base_directory = "C:\\Users\\OCD\\Desktop\\DATA\\RN"  # Change this to your folder path

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

Data = DH.getData(file_path)

stream = DH.getSignals(Data, 'Streaming')[0]

#information about the eltrodes

functions = pre.get_functions(scipy.signal).keys()

for f in functions: print(f)
