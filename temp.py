import DataHandling as DH
import dearpygui.dearpygui as dpg
import utils as utl
import numpy as np
from datetime import datetime
import json
import os

'''
BASE

dpg.create_context()
with dpg.window():

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

# # file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"
file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
# # file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"

'''

# file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
Data = DH.getData(file_path=file)
Streaming = DH.getSignals(Data,'Streaming')


def save_session():
    
    all = dpg.get_all_items()
    all_info = {}
    np = 'new'
    dpg.add_window(label='NewMain',tag=np,show=False)
    for item in all:
        all_info[item] = {'Config': {}, 'Info': {}}
        config = dpg.get_item_configuration(item)
        info = dpg.get_item_info(item)
        all_info[item]['Config'] = {k:config[k] for k in config.keys()}
        all_info[item]['Info'] = {k:info[k] for k in info.keys()}
        try:
            label = dpg.get_item_label(item)
            all_info = {'Label': label} | all_info
        except Exception: continue

    for i in all_info.keys():
        print(f'--------------------- {i} ---------------------')
        try:
            op = all_info[i]['Info']['parent']
            print(op)
            
            if op is None:
                dpg.set_item_alias(i,np)
                print(all_info[i]['Config'])
            else:
                dpg.reorder_items(i,parent=f"{np}_{op}")
            print('\n')
        except Exception: continue

    dpg.configure_item(np,show=True)

def save_all():
    dpg.add_window(tag='new')
    children = dpg.get_item_children('main')[1][0]
    dpg.move_item(item=children,parent='new')
    dpg.delete_item('main')
    dpg.set_primary_window('new',True)
    dpg.save_init_file("dpg.ini")
    
def create(sender,app_data,user_data):
    dpg.add_button(label='Button',parent=user_data)
    with dpg.child_window(parent=user_data):
        dpg.add_text('Another item')

def edit_item(item='Button'):
    
    with dpg.theme() as theme:
        match item:
            case 'Button':
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 12)   # round corners
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (50, 150, 250))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (75, 175, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (40, 130, 220))
            case 'Window':
                with dpg.theme_component(dpg.mvWindowAppItem):
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 12) 

    return theme

def edit_all():
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,10) 
            dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign,0.5)
        with dpg.theme_component(dpg.mvCheckbox):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0)
    return theme


dpg.create_context()

dpg.show_documentation()
dpg.show_style_editor()
dpg.show_debug()
dpg.show_about()
dpg.show_metrics()
dpg.show_font_manager()
dpg.show_item_registry()

with dpg.window(label='Main',tag='main'):
    bt = edit_all()
    dpg.bind_item_theme('main',edit_all())
    with dpg.group(tag='group'):
        with dpg.plot(label='Streaming - All Day',tag = 'plot_tag'):
            dpg.add_plot_legend()
            x_axis = dpg.add_plot_axis(dpg.mvXAxis,label='X')
            y_axis = dpg.add_plot_axis(dpg.mvYAxis,label='Y')
            for stream in Streaming:
                x = stream['X']
                y = stream['Y']
                channel = stream['Channel']
                dpg.add_line_series(x,y,label=channel,parent=y_axis)
        b = dpg.add_button(label='Save Signals into TXT',callback=create,user_data='group')
        dpg.bind_item_theme(b,bt)
        dpg.add_button(label='Save',callback=create,user_data='group')

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
