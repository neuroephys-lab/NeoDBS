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


SESSION_FILE = "session.json"
LAYOUT_FILE = "layout.ini"

def save_session():
    session = {
        "windows": {},
        "groups": {},
        "tabs": {}
    }
    all = dpg.get_all_items()
    print(all)
    for item in dpg.get_all_items():
        info = dpg.get_item_info(item)
        typ = info["type"]

        # Windows and child windows
        if typ in ["mvAppItemType::Window", "mvAppItemType::ChildWindow"]:
            session["windows"][item] = {
                "shown": dpg.is_item_shown(item),
                "pos": list(dpg.get_item_pos(item)),
                "size": [dpg.get_item_width(item), dpg.get_item_height(item)]
            }

        # Groups / collapsing headers
        elif typ in ["mvAppItemType::Group", "mvAppItemType::CollapsingHeader"]:
            session["groups"][item] = {
                "shown": dpg.is_item_shown(item),
                "expanded": dpg.get_item_open(item) if hasattr(dpg, "get_item_open") else True
            }

        # Tabs
        elif typ == "mvAppItemType::TabBar":
            selected = dpg.get_value(item)
            session["tabs"][item] = {"selected_tab": selected}

    # Save JSON
    with open(SESSION_FILE, "w") as f:
        json.dump(session, f, indent=4)

    # Also save main window layout
    dpg.save_init_file("dpg.ini")
    print("Session saved.")

def load_session():
    # Must recreate all windows/groups/tabs in code first
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            session = json.load(f)
        
        # Apply windows
        for item, props in session.get("windows", {}).items():
            if dpg.does_item_exist(item):
                if props["shown"]:
                    dpg.show_item(item)
                else:
                    dpg.hide_item(item)
                dpg.set_item_pos(item, props["pos"])
                dpg.set_item_width(item, props["size"][0])
                dpg.set_item_height(item, props["size"][1])

        # Apply groups / collapsing headers
        for item, props in session.get("groups", {}).items():
            if dpg.does_item_exist(item):
                if props["shown"]:
                    dpg.show_item(item)
                else:
                    dpg.hide_item(item)
                if "expanded" in props:
                    dpg.set_item_open(item, props["expanded"])

        # Apply tabs
        for item, props in session.get("tabs", {}).items():
            if dpg.does_item_exist(item):
                dpg.set_value(item, props["selected_tab"])

    # Restore main window layout
    if os.path.exists(LAYOUT_FILE):
        dpg.load_init_file(LAYOUT_FILE)
    
    print("Session loaded.")


file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
Data = DH.getData(file_path=file)
Streaming = DH.getSignals(Data,'Streaming')


dpg.create_context()

def save_signals(sender,app_data,user_data):
    parent, plot, plot_type = user_data
    file_name = dpg.get_item_label(plot)
    children = dpg.get_item_children(parent)[1]
    limits = dpg.get_axis_limits(dpg.get_item_children(plot)[1][0])
    match plot_type:
        case '2D':
            #only save signals shown in plot
            children = [c for c in children if dpg.get_item_configuration(c)['show'] == True]
            labels = [dpg.get_item_label(tag) for tag in children]
            signals = [dpg.get_value(tag)[1] for tag in children]
            xx = [dpg.get_value(tag)[0] for tag in children]
            lengths = [len(x) for x in xx]
            maxX = xx[lengths.index(max(lengths))] #get the longest array
            
            mini = np.abs(np.array(maxX) - limits[0]).argmin()  # closest index 
            maxi = np.abs(np.array(maxX) - limits[1]).argmin()
            
            info = {'X': maxX[mini:maxi]}
            more = {labels[i]: signals[i][mini:maxi] for i in range(len(signals))}
            info = info | more
    with dpg.child_window(parent='group'):
        dpg.add_text('Loaded all')
    export_signals(info,file_name)
    save_init()

def save_init():
    dpg.save_init_file("dpg.ini")

def export_signals(info,filename):
    
    filename = filename.replace(' - ','_')
    filename = filename.replace(' ','_')
    filename = filename + ".csv"
    with open(filename, "w") as f:
        f.write(",".join(list(info.keys())) + "\n")
        n_lines = len(info['X'])
        for i in range(n_lines):
            row = []
            for column in info.keys():
                try:
                    row.append(str(info[column][i]))
                except:
                    row.append(' ')
            f.write(",".join(row) + "\n")

    print(f"Saved file: {filename}")

dpg.configure_app(init_file="dpg.ini")

with dpg.window():
    dpg.set_exit_callback(save_session)
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
        dpg.add_button(label='Save Signals into TXT',callback=save_signals,user_data=(y_axis,'plot_tag','2D'))
    

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

'''
    for item in dpg.get_all_items():
        info = dpg.get_item_info(item)
        typ = info["type"]

        # Windows and child windows
        if typ in ["mvAppItemType::Window", "mvAppItemType::ChildWindow"]:
            session["windows"][item] = {
                "shown": dpg.is_item_shown(item),
                "pos": list(dpg.get_item_pos(item)),
                "size": [dpg.get_item_width(item), dpg.get_item_height(item)]
            }

        # Groups / collapsing headers
        elif typ in ["mvAppItemType::Group", "mvAppItemType::CollapsingHeader"]:
            session["groups"][item] = {
                "shown": dpg.is_item_shown(item),
                "expanded": dpg.get_item_open(item) if hasattr(dpg, "get_item_open") else True
            }

        # Tabs
        elif typ == "mvAppItemType::TabBar":
            selected = dpg.get_value(item)
            session["tabs"][item] = {"selected_tab": selected}'''

    # Save JSON
    # with open("session.json", "w") as f:
    #     json.dump(session, f, indent=4)

    # Also save main window layout
    # dpg.save_init_file("dpi.ini")
    # print("Session saved.")

