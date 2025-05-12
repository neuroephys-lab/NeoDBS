import DataHandling as DH
import utils as utl
import dearpygui.dearpygui as dpg
import matplotlib.pyplot as plt

base_directory = "C:\\Users\\OCD\\Desktop\\DATA\\RN"  # Change this to your folder path

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

new_names = {
    'ZERO_TWO_LEFT': 'MAIN',
    'ZERO_TWO_RIGHT': 'Right'
}

string = 'ZERO_TWO_LEFT'

print(new_names[string])