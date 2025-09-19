import DataHandling as DH
import utils as utl
import matplotlib.pyplot as plt
import numpy as np
import dearpygui.dearpygui as dpg

filepath = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
Data = DH.getData(file_path=filepath)

dpg.create_context()

dpg.show_implot_demo()

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

        


