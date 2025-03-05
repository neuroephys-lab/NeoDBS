'''import DataHandling as DH
import matplotlib.pyplot as plt
import utils as utl
import numpy as np
import Preprocessing as pre'''
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import DataHandling as DH
import Preprocessing as pre
import utils as utl
from datetime import datetime
import numpy as np
from datetime import timedelta

# Set the base directory where JSON files are located
base_directory = "C:\\Users\\OCD\\Desktop\\DATA\\RN"  # Change this to your folder path

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

Data = DH.getData(file_path)

