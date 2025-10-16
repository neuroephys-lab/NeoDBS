import subprocess
import sys
import importlib
import os
import re

def is_package_installed(package_name):
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def parse_package_name(requirement_line):
    # Extract package name from line like "numpy>=1.20" or "dearpygui_ext==1.0.0"
    return re.split(r'[<>=]', requirement_line.strip())[0]

def install_requirements_if_needed(requirements_file="requirements.txt"):
    if not os.path.exists(requirements_file):
        print(f"{requirements_file} not found.")
        return

    with open(requirements_file, "r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    missing = []
    for line in lines:
        package = parse_package_name(line)
        if not is_package_installed(package):
            missing.append(line)

    if missing:
        print("Installing missing packages:", missing)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("All missing requirements installed successfully.")
        except subprocess.CalledProcessError as e:
            print("Failed to install some requirements:", e)
    else:
        print("All required packages are already installed.")

# --- Run before your imports ---
install_requirements_if_needed()

from datetime import timedelta, datetime
import dearpygui.dearpygui as dpg
from dearpygui_ext import themes as themes
import numpy as np 
import DataHandling as DH # type: ignore
import utils as utl
import Preprocessing as pre
import Features as ft
import time
import csv

#----------------------------------------GLOBAL-----------------------------
global_bands = ft.bands
electrodes_names, unchecked_channels = {}, {}
app_state = {"windows": {}}
colors = [
        (0, 0, 255, 255),      # blue
        (255, 0, 0, 255),      # red
        (0,0,0,0),              # black
        (0, 255, 0, 255),      # green
        (255, 165, 0, 255),    # orange
        (255, 255, 0, 255),    # yellow
        (255, 51, 255, 255), #pink
        (102, 0, 204, 255), #purple
        (0, 255, 255, 255), #cian
    ]
#-----------------------------------------UTILS----------------------------------------

def print_me(sender, app_data):
    print(f"Menu item {sender} clicked!")

def add_band(sender, app_data, user_data):
    tab_tag = user_data
    old = getBandsByTab(tab_tag)
    min = dpg.get_value(f"{tab_tag}_band_min")
    max = dpg.get_value(f"{tab_tag}_band_max")
    new = {f'Band {min}-{max}': [min,max]}
    t_bands = old | new
    window_id = extract_window_id(tab_tag)
    app_state['windows'][window_id]['Bands'] = t_bands

def sanitize_filename(filename):
    """Removes or replaces invalid characters from filenames."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)  # Replace invalid characters with '_'

def save_table_to_file(sender, app_data, user_data):
    """Saves DPG table data to a .csv or .txt file"""
    table_id, file_type = user_data  # Unpack table ID and file type

    # Get table columns (headers)
    column_children = dpg.get_item_children(table_id, slot=0)
    headers = [dpg.get_item_label(col) for col in column_children] if column_children else []

    # Get table rows (data)
    rows = []
    row_children = dpg.get_item_children(table_id, slot=1)
    if row_children:
        for row in row_children:
            cell_children = dpg.get_item_children(row, slot=1)
            if cell_children:
                row_data = [dpg.get_value(cell) for cell in cell_children]
                rows.append(row_data)

    # **Sanitize filename**
    filename = sanitize_filename(f"{table_id}.{file_type}")

    # Save to CSV or TXT
    if file_type == "csv":
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            if headers:
                writer.writerow(headers)
            writer.writerows(rows)
    else:
        with open(filename, mode="w") as file:
            if headers:
                file.write("\t".join(headers) + "\n")
            for row in rows:
                file.write("\t".join(map(str, row)) + "\n")

    print(f"Table saved as {filename}")

#--- Add common buttons
def add_filters_buttons(tab_tag,signal_tags):
  
    if dpg.does_item_exist(tab_tag):
        with dpg.group(parent=tab_tag, horizontal=True, width=600):
            with dpg.collapsing_header(label="Filters", default_open=False, parent=tab_tag, tag = f"{tab_tag}_filters"):
                with dpg.group(horizontal=True):
                    dpg.add_input_intx(label='Frequencies',size=2,min_value=1,max_value=100,default_value=[0,100], max_clamped=True, min_clamped=True, tag = f"{tab_tag}_default_wn")
                    dpg.add_button(label="Default Filtering",callback=DefaultFilter, user_data=(tab_tag,signal_tags), tag = f"{tab_tag}_default_filter")

                with dpg.tooltip(f"{tab_tag}_default_filter"):
                    dpg.add_text("5th Order Butterworth Filter and Removal of Cardiac Component")

                dpg.add_button(label="Custom Filtering",width=-1, callback=add_combo_filters, user_data=(tab_tag,signal_tags))
    else:
        print(f"Tab {tab_tag} does not exist yet.")

def add_features_buttons(tab_tag, signal_tags):
    if dpg.does_item_exist(tab_tag):
        with dpg.group(parent=tab_tag, horizontal=True, width=600,tag=f"{tab_tag}_features_group"):
            # "Features" menu simulation
            with dpg.collapsing_header(label="Features", default_open=False, parent=tab_tag,tag = f"{tab_tag}_features"):
                add_combo_df_features(tab_tag,signal_tags)
                add_combo_features(tab_tag,signal_tags)
                with dpg.group(horizontal=True):
                    dpg.add_input_int(label='Hz', tag=f"{tab_tag}_band_min", width=90, default_value=0, callback=enforce_min_max, user_data=(f"{tab_tag}_band_min", f"{tab_tag}_band_max", 2))
                    dpg.add_input_int(label='Hz', tag=f"{tab_tag}_band_max", width=90, default_value=100, callback=enforce_min_max, user_data=(f"{tab_tag}_band_min", f"{tab_tag}_band_max", 2))
                    dpg.add_button(label='Insert Band of Interest', show=True, callback=add_band,user_data=(tab_tag))
    else:
        print(f"Tab {tab_tag} does not exist yet.")

def add_timeline_features_buttons(tab_tag, signal_tags):
    if dpg.does_item_exist(tab_tag):
        with dpg.group(parent=tab_tag, horizontal=True, width=600,tag=f"{tab_tag}_features_group"):
            # "Features" menu simulation
            with dpg.collapsing_header(label="Features", default_open=False, parent=tab_tag,tag = f"{tab_tag}_features"):
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Circadian Rhythm', callback=circadian_rhythm, user_data=(tab_tag, signal_tags, tab_tag))
                    dpg.add_button(label='Stimulation',callback=stimulation_timeline, user_data=(tab_tag, signal_tags, tab_tag))
    else:
        print(f"Tab {tab_tag} does not exist yet.")

def add_correlation_buttons(tab_tag):
    print('')
    # if dpg.does_item_exist(tab_tag):
    #     with dpg.group(parent=tab_tag, horizontal=True, width=600):
    #         # "Correlation" menu simulation
    #         with dpg.collapsing_header(label="Correlation", default_open=False, parent=tab_tag):
    #             dpg.add_button(label="Statistical Analysis",width=-1)
    #             dpg.add_button(label="Machine Learning Analysis",width=-1)
    # else:
    #     print(f"Tab {tab_tag} does not exist yet.")

def add_menu_bar(tab_tag):
    if dpg.does_item_exist(tab_tag):
        with dpg.group(parent=tab_tag, horizontal=True, width=600):

            with dpg.collapsing_header(label="Filters", default_open=False, parent=tab_tag):
                dpg.add_button(label="Default Filtering",width=-1)
                dpg.add_button(label="Personalized Filtering",width=-1)

            # "Features" menu simulation
            with dpg.collapsing_header(label="Features", default_open=False, parent=tab_tag):
                dpg.add_button(label="Default Feature Extraction",width=-1)
                dpg.add_button(label="Personalized Feature Extraction",width=-1)

            # "Correlation" menu simulation
            with dpg.collapsing_header(label="Correlation", default_open=False, parent=tab_tag):
                dpg.add_button(label="Statistical Analysis",width=-1)
                dpg.add_button(label="Machine Learning Analysis",width=-1)
    else:
        print(f"Tab {tab_tag} does not exist yet.")

def add_combo_filters(sender, app_data, user_data):
    tab_tag,signal_tags = user_data

    filters = ['butter','cheby1','cheby2','ellip',
                'bessel','iirnotch','iirpeak']

    dpg.add_spacer(parent=f"{tab_tag}_filters")
    with dpg.group(horizontal=True,parent=f"{tab_tag}_filters"):
        dpg.add_combo(label='IIR Filters',callback = CustomFilter, user_data=(tab_tag,signal_tags),items = filters, parent=f"{tab_tag}_filters", tag = f"{tab_tag}_combo_filters",width=200)

def add_combo_features(tab_tag,signal_tags):

    features = ['periodogram','welch','spectrogram', 'dpss', 'wavelet', 'coherence', 'multitaper coherence','cross-correlation','PAC']

    dpg.add_spacer(parent=f"{tab_tag}_features")
    with dpg.group(parent=f"{tab_tag}_features", tag = f"{tab_tag}_custom_features"):
        dpg.add_combo(label='Spectral Personalized Analysis',callback = CustomFeatures, user_data=(tab_tag,signal_tags),items = features, parent=f"{tab_tag}_custom_features", tag = f"{tab_tag}_combo_features",width=200)

def add_combo_df_features(tab_tag,signal_tags):

    features = ['periodogram','welch','spectrogram', 'multitaper', 'dpss', 'wavelet', 'coherence', 'multitaper coherence', 'cross-correlation', 'PAC']

    dpg.add_spacer(parent=f"{tab_tag}_features")
    with dpg.group(parent=f"{tab_tag}_features", tag = f"{tab_tag}_df_features"):
        dpg.add_combo(label='Spectral Default Analysis',callback = DefaultFeatures, user_data=(tab_tag,signal_tags),items = features, parent=f"{tab_tag}_df_features", tag = f"{tab_tag}_combo_df_features",width=200)

#--- Toggle buttons
def toggleVisibility(signal_tags, parent, group, user_data):
    # Create a group for visibility controls
    window_id = user_data
    tab_tag = parent
    with dpg.group(parent=group):
        dpg.add_text("Choose signals:")
        checkboxes = {}
            
        def toggle_all(sender, app_data):

            for tag, checkbox in checkboxes.items():
                dpg.set_value(checkbox, app_data)
                dpg.configure_item(tag, show=app_data)

                if dpg.does_item_exist(f"{tab_tag}_mean"): #only in events for now
                    mean_power, std_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
                    minus, plus = mean_power-std_power, mean_power+ std_power
                    dpg.configure_item(f"{tab_tag}_std", y1=minus,y2=plus)
                    current = dpg.get_value(f"{tab_tag}_mean")
                    dpg.set_value(f"{tab_tag}_mean", [current[0], mean_power])

        dpg.add_checkbox(label="Select All", default_value=True, callback=toggle_all, tag = f"{tab_tag}_all")

        with dpg.child_window(autosize_x=True, height=100, border=True):
            
            # Create checkboxes for each plot
            for series_tag, visible in signal_tags.items():
                series_config = dpg.get_item_configuration(series_tag)
                label = series_config.get('label', series_tag.split('_')[-1])

                def toggle_visibility(sender, app_data, user_data):
                    if dpg.does_item_exist(f"{tab_tag}_hide"):
                        if dpg.get_value(f"{tab_tag}_hide"):
                            hide(sender, False, (signal_tags, [None]))
                            dpg.set_value(f"{tab_tag}_hide",False)
                    dpg.configure_item(user_data, show=app_data)
                    item_id = f"{parent}_select_all"
                    if dpg.does_item_exist(item_id):  # Check if the item exists
                        dpg.set_value(item_id, False)
                        
                    else:
                        pass
                    mode = extract_mode(tab_tag)
                    if mode == 'Events':
                        mean_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
                        current = dpg.get_value(f"{tab_tag}_mean")
                        dpg.set_value(f"{tab_tag}_mean", [current[0], mean_power])
                    

                checkbox = dpg.add_checkbox(label=label, default_value=visible,
                                            callback=toggle_visibility, user_data=series_tag)
                checkboxes[series_tag] = checkbox

def toggleType2(signal_tags, parent, user_data):
    type_filter, window_id, tab_tag = user_data  # Extract relevant info

    # Initialize storage for this type if not already present
    if type_filter not in unchecked_channels:
        unchecked_channels[type_filter] = set()

    with dpg.group(parent=parent):
        # Toggle all channels matching the type
        def toggle_filtered_series(sender, app_data):
            for series_tag in signal_tags:
                series_label = str(dpg.get_item_label(series_tag))

                if type_filter.lower() in series_label.lower():  # Match type
                    if app_data:  # Checking type box: Show only non-manually-unchecked
                        if series_tag not in unchecked_channels[type_filter]:
                            dpg.configure_item(series_tag, show=True)
                            dpg.set_value(f"{series_tag}_checkbox", True)  # Sync checkbox
                    else:  # Unchecking type box: Hide all
                        dpg.configure_item(series_tag, show=False)
                        unchecked_channels[type_filter].add(series_tag)  # Mark as manually unchecked
                        dpg.set_value(f"{series_tag}_checkbox", False)  # Sync checkbox

            # Update the mean power calculation if applicable
            if dpg.does_item_exist(f"{tab_tag}_mean"):
                mean_power, std_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
                minus, plus = mean_power-std_power, mean_power+ std_power
                dpg.configure_item(f"{tab_tag}_std", y1=minus,y2=plus)
                current = dpg.get_value(f"{tab_tag}_mean")
                dpg.set_value(f"{tab_tag}_mean", [current[0], mean_power])

        # Add type-level checkbox
        dpg.add_checkbox(label=f"{type_filter}", default_value=True, callback=toggle_filtered_series, tag=f"{tab_tag}_{type_filter}_checkbox")

def toggleType(signal_tags, parent, user_data, orientation = False):
    type_filter, window_id, tab_tag = user_data  


    def toggle_filtered_series(sender, app_data, user_data):

        if dpg.does_item_exist(f"{tab_tag}_hide"):
            if dpg.get_value(f"{tab_tag}_hide"):
                hide(sender, False, (signal_tags, [None]))
                dpg.set_value(f"{tab_tag}_hide",False)

        window_id = extract_window_id(tab_tag)
        for series_tag in signal_tags:
            series_label = str(dpg.get_item_label(series_tag))

            if type_filter.lower() in series_label.lower():  # Check if the label contains the type
                dpg.configure_item(series_tag, show=app_data)
                    
        if dpg.does_item_exist(f"{tab_tag}_mean"):
            mean_power, std_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
            minus, plus = mean_power-std_power, mean_power+ std_power
            current = dpg.get_value(f"{tab_tag}_mean")
            dpg.configure_item(f"{tab_tag}_std", y1=minus,y2=plus)

            dpg.set_value(f"{tab_tag}_mean", [current[0], mean_power])
            
    
    dpg.add_checkbox(label=f"{type_filter}", default_value=True, callback=toggle_filtered_series,tag = f"{tab_tag}_{type_filter}_checkbox", parent=parent)

def toggleDisplay(signals, signal_tags, window_id, tab_tag):

    '''
    Documentation
    '''    
    signals = getActiveSignals(tab_tag,signal_tags)

    days, hours = [], [] #by date
    for signal in signals: 
        date = signal['Date']
        hour = f"{date.hour:02d}:{date.minute:02d}"
        hours.append(hour)
        day = f"{date.year}-{date.month:02d}-{date.day:02d}"
        days.append(day)
        
    days = np.unique(days).tolist()
    hours = np.unique(hours).tolist()

    channels = []
    for signal in signals: # by channel
        # channels.append(extract_channel_from_series_tag(signal['Channel']).upper())
        ch = signal['Channel']
        if ch in electrodes_names.keys():
            ch = electrodes_names[ch]
        else:
            electrodes_names[ch] = ch
        channels.append(extract_channel_from_series_tag(ch))
    channels = np.unique(channels).tolist()
    channels = [ch.upper() for ch in channels]

    sides = ['Left','Right']
    
    with dpg.group(label=f"{tab_tag}_buttons"):

        # Ensure toggleVisibility is inside a vertical group
        with dpg.group(parent=f"{tab_tag}_buttons", tag = f"{tab_tag}_all_streams"):
            toggleVisibility(signal_tags, tab_tag, group=f"{tab_tag}_buttons", user_data=window_id)

        dpg.add_spacer(height=10)

        with dpg.group(horizontal=True, parent=f"{tab_tag}_buttons", tag=f"{tab_tag}_types"):
            with dpg.group():
                if len(hours) > 1:
                    with dpg.child_window(tag=f"{tab_tag}_buttons_hours", width=120, height=120):
                        dpg.add_text('By recording:')
                        for day in hours:
                            toggleType(signal_tags, parent=f"{tab_tag}_buttons_hours", user_data=(day, window_id, tab_tag))

                if len(days) > 1:
                    dpg.add_child_window(tag=f"{tab_tag}_buttons_day", height=120, width=120)
                    dpg.add_text('By day:', parent=f"{tab_tag}_buttons_day")
                    for day in days:
                        toggleType(signal_tags, parent=f"{tab_tag}_buttons_day", user_data=(day, window_id, tab_tag))
            with dpg.group():   
                if len(channels) > 1:
                    with dpg.child_window(tag=f"{tab_tag}_buttons_channel", height=120, width=120):
                        dpg.add_text('By channel:')
                        for day in channels:
                            toggleType(signal_tags, parent=f"{tab_tag}_buttons_channel", user_data=(day, window_id, tab_tag))

                
                if len(sides) > 1:
                    with dpg.child_window(tag=f"{tab_tag}_buttons_side", height=120, width=120):
                        dpg.add_text('By hemisphere:')
                        for day in sides:
                            toggleType(signal_tags, parent=f"{tab_tag}_buttons_side", user_data=(day, window_id, tab_tag))

            # with dpg.child_window(tag=f"{tab_tag}_buttons_events"): pass
        
        segment_signal(tab_tag, signal_tags)

def toggleDisplay2(signals, signal_tags, window_id, tab_tag):
    events = [signal['EventName'] for signal in signals]
    dates = []
    for signal in signals: 
        date = utl.parse_datetime(signal['DateInitial'])
        date = f"day {date.day:02d}/{date.month:02d}"
        dates.append(date)

    dates = np.unique(dates).tolist()
    events = np.unique(events).tolist()
    sides = ['Left', 'Right']
    def show_mean(sender,app_data):
        dpg.configure_item(f"{tab_tag}_mean",show=app_data)
        dpg.configure_item(f"{tab_tag}_std",show=app_data)

    with dpg.group(label = f"{tab_tag}_buttons"):
        toggleVisibility(signal_tags, tab_tag, group = f"{tab_tag}_buttons",user_data=window_id)
        dpg.add_spacer(parent=f"{tab_tag}_buttons")
        with dpg.group(horizontal=True, parent=f"{tab_tag}_buttons"):
            #check days
            if len(dates)>1:
                with dpg.child_window(width=120, height=150):
                    dpg.add_text('By days:')
                    for day in dates:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons_day", user_data=(day, window_id, tab_tag)) 

            #check channels
            if len(events)>1:
                with dpg.child_window(label = f"{tab_tag}_buttons_events",width=120, height=150):
                    dpg.add_text('By events:')
                    for day in events:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons_events", user_data=(day, window_id, tab_tag)) 

            #check sides
            if len(sides)>1:
                with dpg.child_window(label = f"{tab_tag}_buttons_side",width=120, height=150):
                    dpg.add_text('By hemisphere:')
                    for day in sides:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons_side", user_data=(day, window_id, tab_tag))

        dpg.add_checkbox(label='Change to dB',callback=Volt2dB, user_data=(signal_tags,tab_tag, "", "", ""),parent=f"{tab_tag}_buttons",default_value=False)
        if extract_mode(tab_tag) == 'Events': 
            dpg.add_button(label='Recalculate Mean Metrics', callback=recalculateMeanMetrics, user_data=tab_tag, parent=f"{tab_tag}_buttons")
            dpg.add_checkbox(label='Mean Visibility', default_value=True, callback=show_mean, parent=f"{tab_tag}_buttons")
            dpg.add_checkbox(label='Hide Events', default_value=False,callback=hide,parent=f"{tab_tag}_buttons",user_data=(signal_tags,[None]), tag=f"{tab_tag}_hide")

def recalculateMeanMetrics(sender, app_data, user_data):
    tab_tag = user_data
    bands = getBandsByTab(tab_tag)
    if dpg.does_item_exist(f"{tab_tag}_mean"):
        x,y =  dpg.get_value(f"{tab_tag}_mean")
        mean_power = {'X': x, 'Y': y}     
        dpg.delete_item(f"{tab_tag}_mean_metric", children_only=True)
        for band in bands.items():
            info = extract_psd_features(mean_power, band)
            create_table(f"{tab_tag}_mean_metric",f"{tab_tag}_mean_metric_table", info, trial_label=band[0])

def hide(sender,app_data,user_data):
    streams, checkboxes = user_data
    if checkboxes != [None]:

        if app_data == False:
            for c in checkboxes:
                dpg.set_value(c,True)
                callback = dpg.get_item_callback(c)
                if callback:
                    callback(c, True, dpg.get_item_user_data(c))
   
    for s in streams:
        bol = not app_data
        dpg.configure_item(s, show=bol)

#--- Visualization functions
def plot_td(signals, parent, tab_tag, signal_tags, files = None, events = False, count = []):
    '''
    Plot Time Domain signals (Streaming, Indefinite, Setup, Survey)
    '''
    #extra =  len(signal_tags)
    window_id = extract_window_id(tab_tag)
    if events:
        event_types = [signal['Type'] for signal in signals]
        event_types = np.unique(event_types).tolist()
    if count != []: fdx = files
    for idx, signal in enumerate(signals):
        if count != []:
            files = fdx[idx]
            idx = count[idx]
            
        series_tag = f"{tab_tag}_series_{idx}" #+extra
        combined_tag = f"{tab_tag}_file_{files}_series_{idx}"
        

        if events == False:
            x = signal['X']
            y = np.ascontiguousarray(signal['Y'])
            date = signal['Date']
            channel = signal['Channel']

            if channel in electrodes_names.keys():
                channel = electrodes_names[channel]
            else:
                electrodes_names[channel] = channel
            
            if 'Data' in app_state['windows'][window_id].keys():
                if not dpg.does_item_exist(series_tag):
                    dpg.add_line_series(x, y, label=f"{channel} ({date})", parent=parent, tag=series_tag)
                    signal_tags[series_tag] = True  # Track visibility
                    app_state['windows'][window_id]['Data'][tab_tag]['Signals'].append(signal)
                else:
                    print(f"Skipping duplicate series: {series_tag}")
            elif not dpg.does_item_exist(combined_tag):
                dpg.add_line_series(x, y, label=f"{channel} ({date})", parent=parent, tag=combined_tag)
                signal_tags[combined_tag] = True 
                app_state['windows'][window_id]['Files'][files]['Data'][tab_tag]['Signals'].append(signal)
                
            else:
                print(f"Skipping duplicate series: {combined_tag}")

        elif events == True:
            old_channel = signal['Channel']
            if old_channel in electrodes_names.keys():
                old_channel = electrodes_names[old_channel]
            else:
                electrodes_names[old_channel] = old_channel

            x, y, type_event, channel, serie_idx = signal['X'],signal['Y'], signal['Type'], old_channel, signal['Serie']
            if extract_type_window(window_id) == 'Combined':
                segment_tag = f"{tab_tag}_file_{files}_series_{serie_idx}_{type_event}_{idx}"
            else:
                segment_tag = f"{tab_tag}_series_{serie_idx}_{type_event}_{idx}"
            
            if not dpg.does_item_exist(segment_tag):
                dpg.add_line_series(x, y, label=f"{type_event} {signal['Date']} ({channel})", parent=parent, tag=segment_tag)
                dpg.bind_item_theme(segment_tag,change_inf_line_color(event_types.index(type_event)))
                signal_tags[segment_tag] = True 
            else:
                print(f"Skipping duplicate series: {combined_tag}")


def plot_fd(signals, parent, tab_tag, signal_tags, files = None, events = False):
    '''
    Plot Frequency Domain signals (Streaming, Indefinite, Setup, Survey)
    '''
    #extra =  len(signal_tags)
    window_id = extract_window_id(tab_tag)
    
    for idx, signal in enumerate(signals):
        series_tag = f"{tab_tag}_series_{idx}" #+extra
        combined_tag = f"{tab_tag}_file_{files}_series_{idx}"
        

        if events == False:
            x = signal['X']
            y = np.ascontiguousarray(signal['Y'])
            date = signal['Date']
            channel = signal['Channel']

            if channel in electrodes_names.keys():
                channel = electrodes_names[channel]
            else:
                electrodes_names[channel] = channel
            
            if 'Data' in app_state['windows'][window_id].keys():
                if not dpg.does_item_exist(series_tag):
                    dpg.add_line_series(x, y, label=f"{channel} ({date})", parent=parent, tag=series_tag)
                    signal_tags[series_tag] = True  # Track visibility
                    app_state['windows'][window_id]['Data'][tab_tag]['Signals'].append(signal)
                else:
                    print(f"Skipping duplicate series: {series_tag}")
            elif not dpg.does_item_exist(combined_tag):
                dpg.add_line_series(x, y, label=f"{channel} ({date})", parent=parent, tag=combined_tag)
                signal_tags[combined_tag] = True 
                app_state['windows'][window_id]['Files'][files]['Data'][tab_tag]['Signals'].append(signal)
            else:
                print(f"Skipping duplicate series: {combined_tag}")

        elif events == True:
            old_channel = signal['Channel']
            if old_channel in electrodes_names.keys():
                old_channel = electrodes_names[old_channel]
            else:
                electrodes_names[old_channel] = old_channel

            x, y, type_event, channel, serie_idx = signal['X'],signal['Y'],signal['Type'], old_channel, signal['Serie']
            if extract_type_window(window_id) == 'Combined':
                segment_tag = f"{tab_tag}_file_{files}_series_{serie_idx}_{type_event}_{idx}"
            else:
                segment_tag = f"{tab_tag}_series_{serie_idx}_{type_event}_{idx}"
            if not dpg.does_item_exist(segment_tag):
                dpg.add_line_series(x, y, label=f"{type_event} {signal['Date']} ({channel})", parent=parent, tag=segment_tag)
                signal_tags[segment_tag] = True 
            else:
                print(f"Skipping duplicate series: {combined_tag}")

def update_plot_td(tab_tag, signal_tags, title = None, signal_mode = None):
    active_series = getActiveSeries(signal_tags)
    window_id = extract_window_id(tab_tag)
    mode = extract_mode(tab_tag)
    plot_tag = f"plot_{tab_tag}"

    previous = dpg.get_item_label(item=plot_tag)
    if title != None: dpg.set_item_label(item=plot_tag,label=f"{previous} - {title}")

    for i,serie in enumerate(active_series):
        if mode == 'Events':
            signal = getSignalbyIdxSide(window_id,tab_tag,serie)
        elif signal_mode == None:
            signal = getSignalbyIdx(window_id,tab_tag,serie)
        else:
            signal = getSignalbyIdx(window_id,tab_tag,serie, mode='segment')
        x = signal['X']
        y = signal['Y']
        if dpg.does_item_exist(serie):
            dpg.set_value(serie, [x, y])  # Update existing series data
        else:
            #dpg.add_line_series(x, y, label=f"{series}", parent=f"y_axis_{tab_tag}", tag=serie)
            print('No existing series: ', serie)
        if isinstance(signal_tags, (list, np.ndarray)):
            signal_tags[i] = True  # Track visibility
        if isinstance(signal_tags, dict):
            signal_tags[serie] = True
    dpg.set_axis_limits_auto(f"x_axis_{tab_tag}")

def update_plot_fd(tab_tag, signal_tags, title = None):
    active_series = getActiveSeries(signal_tags)
    window_id = extract_window_id(tab_tag)
    plot_tag = f"plot_{tab_tag}"

    previous = dpg.get_item_label(item=plot_tag)
    if title != None: dpg.set_item_label(item=plot_tag,label=f"{previous} - {title}")

    for serie in active_series:
        signal = getSignalbyIdxSide(window_id,tab_tag,serie)
        x = signal['X']
        y = signal['Y']
        if dpg.does_item_exist(serie):
            dpg.set_value(serie, [x, y])  # Update existing series data
        else:
            #dpg.add_line_series(x, y, label=f"{series}", parent=f"y_axis_{tab_tag}", tag=serie)
            print('No existing series: ', serie)
        signal_tags[serie] = True  # Track visibility
    dpg.set_axis_limits_auto(f"x_axis_{tab_tag}")
    dpg.set_axis_limits_auto(f"y_axis_{tab_tag}")

def update_plot_feature(tab_tag, tab_label, signal_tags, func, identifier, type, events = False, mode = None):

    active_series = getActiveSeries(signal_tags)
    window_id = extract_window_id(tab_tag)
    plot_tag = f"{identifier}_y_axis"

    if dpg.does_item_exist(plot_tag):
        dpg.delete_item(plot_tag, children_only=True)

    mean = []

    for serie in active_series:
        signal = getSignalbyIdx(window_id,tab_tag,serie, mode)[func]
        label = dpg.get_item_configuration(serie)['label']
        dpg.add_line_series(signal['X'], signal[type], label = label, parent=plot_tag, tag = f"{tab_label}_{label}_{func}")
        mean.append(signal[type])
    
    mean = np.mean(mean,axis=0)
    m = dpg.add_line_series(signal['X'], mean, label = "Mean Power", parent=plot_tag, tag = f"{tab_label}_mean")
    dpg.bind_item_theme(m,change_line_thickness(3))
   

    dpg.set_axis_limits_auto(plot_tag)

def create_table(tab_label,table_tag,features, trial_label = "New Trial"):

    def add_row():
        with dpg.table_row(parent=table_tag):
            dpg.add_input_text(default_value=trial_label, width=-1)                          
            for _, value in features.items():
                
                if isinstance(value, (list, np.ndarray, tuple)):  # Check if value is a list or NumPy array
                    if len(value) == 1:  # Single-element array
                        dpg.add_input_text(default_value=f"{float(value[0]):.2f}",readonly=True)  # Convert to float for clean display
                    else:  # Multiple values
                        rounded_values = [float(v) for v in np.round(value, 2)]  # Convert each np.float64 to float
                        dpg.add_input_text(default_value=f"{rounded_values}",readonly=True)  # Display clean list
                elif isinstance(value, str):
                    dpg.add_input_text(default_value=value,readonly=True)
                else:  # Single number case
                    dpg.add_input_text(default_value=f"{float(value):.2f}",readonly=True)  # Ensure it's a clean float

    with dpg.group(parent=tab_label):
                        
        if not dpg.does_item_exist(table_tag):
            with dpg.table(header_row=True, borders_innerH=True, borders_innerV=True, borders_outerH=True, borders_outerV=True, tag=table_tag,label='Relative Band Power'):
                dpg.add_table_column(label="Trial", width=100)                          
                for band in features.keys():
                    dpg.add_table_column(label=band, width=100)
        add_row()
        if not dpg.does_item_exist(f"{table_tag}_save"):
            dpg.add_button(label='Save table', tag = f"{table_tag}_save", callback=save_table_to_file, user_data=(table_tag, 'csv'), parent=tab_label)
           
def fill_params_features(app_data):
    match app_data:
        case 'correlate':
            params = pre.get_required_params(app_data,module='np')
            functions = pre.get_functions(module='np')
            doc = functions[app_data].__doc__ if functions[app_data].__doc__ else "No documentation available"
    
        case 'dpss':
            windows = pre.get_required_params(app_data, module = 'ssw')
            welch = pre.get_required_params('welch')
            params = windows | welch #join dictionaries  
            replace = {
                'x': '---',
                'M': '---',
                'fs': 250,
                'window': 'skip',
                'NW': 3, #min1
                'Kmax': 5
            }     
            params.update(replace)  
            functions = pre.get_functions('ssw')
            doc1 = functions[app_data].__doc__ if functions[app_data].__doc__ else "No documentation available"
            functions = pre.get_functions()
            doc2 = functions['welch'].__doc__ if functions['welch'].__doc__ else "No documentation available"
            doc = doc1 + doc2

        case 'wavelet':
            app_data = 'tfr_array_morlet'
            params = pre.get_required_params(app_data, module='mtf')
            rep = {'freqs':100,'n_cycles': 3,'sfreq':250, 'output':'power'}
            params.update(rep)
            functions = pre.get_functions('mtf')
            doc = functions['tfr_array_morlet'].__doc__ if functions['tfr_array_morlet'].__doc__ else "No documentation available"

        case 'multitaper':
            app_data = 'psd_array_multitaper'
            params = pre.get_required_params(app_data, module='mtf')
            functions = pre.get_functions('mtf')
            doc = functions['psd_array_multitaper'].__doc__ if functions['psd_array_multitaper'].__doc__ else "No documentation available"
        case _: 
            
            params = pre.get_required_params(app_data)
            functions = pre.get_functions()
            doc = functions[app_data].__doc__ if functions[app_data].__doc__ else "No documentation available"
    
    return params, doc

def replace_params(original,replace):
    return original.update(replace)

def apply_feat(func, parameter_values, raw):
    signal = None
    
    for param in parameter_values.keys():
        if param == 'fs' or param =='sfreq':
            parameter_values[param] = 250
        if param == 'x' or param =='data':
            parameter_values[param] = np.array(raw)
    
    match func:

        case 'multitaper': 
            func = 'psd_array_multitaper'
            signal = pre.call_function(func, parameter_values, module='mtf')
            return signal
        case 'dpss':
            if not isinstance(raw,float):
                parameter_values['M'] = len(np.array(raw))
            try:
                nfft = int(parameter_values['nfft'])
                window_len = nfft
            except Exception: 
                window_len = 512
                step = window_len // 4
                nfft = window_len
                kmax = 2*parameter_values['NW'] - 1
                parameter_values['Kmax'] = kmax
                parameter_values['M'] = window_len

            windows = pre.call_function(func, parameter_values, module = 'ssw')
            Sxx_sum = np.zeros(nfft//2+1)
            n_windows = 0

            for start in range(0, len(raw) - window_len + 1, step):
                xw = raw[start:start+window_len]
                Sxx_tapers = []
                for taper in windows:
                    S1 = np.fft.rfft(xw * taper, n=nfft)
                    scale = 1 / (250 * np.sum(taper**2))
                    psd = (np.abs(S1)**2) * scale
                    Sxx_tapers.append(psd)
                Sxx_sum += np.mean(Sxx_tapers, axis=0)
                n_windows += 1

            Sxx = Sxx_sum / n_windows

            freq = np.fft.rfftfreq(nfft, d=1/250)
            signal = freq, Sxx
            return signal
            # for order, taper in enumerate(windows):
                #     X = np.fft.rfft(raw * taper, n=nfft)
                #     psd = (np.abs(X)**2)/( 250 * np.array(X))
                #     power_combined.append(psd)
                #     # parameter_values['window'] = taper
                #     # try: 
                #     #     freq, psd = pre.call_function('welch', parameter_values,module='ss')
                #     # except Exception as e: print(e)
                #     # power_combined.append(psd)
                #     #power_sum = np.abs(psd).mean()
                # freq = np.fft.rfftfreq(nfft,d=1/250)
                # signal = freq, np.mean(power_combined, axis=0)
        case 'wavelet':
            func = 'tfr_array_morlet'
            a = np.array(raw)
            
            try:
                #older version was 'data' and not 'epoch_data' --> 10.06.2025 - changed again to prior name: this way it has acess to both values
                parameter_values['data'] = a[np.newaxis, np.newaxis, :]
                parameter_values['epoch_data'] = a[np.newaxis, np.newaxis, :]
                # parameter_values['epoch_data'] = parameter_values['data']

                if isinstance(parameter_values['freqs'], str):
                    parameter_values['freqs'] = int(parameter_values['freqs'])
                
                if isinstance(parameter_values['n_cycles'], str):    
                    parameter_values['n_cycles'] = float(parameter_values['n_cycles'])
                
                if isinstance(parameter_values['n_cycles'],(int, float)):
                    parameter_values['freqs'] = np.arange(1,parameter_values['freqs']+1, 1)
                    parameter_values['n_cycles'] = parameter_values['freqs'] / parameter_values['n_cycles']

                signal = pre.call_function(func, parameter_values, module = 'mtf')
                return signal
            except Exception as e: print(e)

        case _: 
            try: 
                signal = pre.call_function(func, parameter_values)
            except Exception as e: 
                return str(e) 

    return signal

def display_error(tab_tag,e):
    doc_container = f"{tab_tag}_ft_doc"
    if dpg.does_item_exist(doc_container):
        v = dpg.get_value(f"{doc_container}_doc")
        dpg.delete_item(doc_container,children_only=True)
        ee = dpg.add_text(e, parent=doc_container)
        dpg.add_separator(parent=doc_container)
        dpg.add_text(v, parent=doc_container, tag = f"{doc_container}_doc")
        dpg.bind_item_theme(ee, change_text_color(1))

def plot_filtered_signal(signal_tags, tab_label, func, tab_tag, parameter_values, mode = None):
    #tab_label = f"{tab_tag}_{func}"
    window_id = extract_window_id(tab_tag)
    tags = getActiveSeries(signal_tags)
    tables, events_tags, events_names, channels, ploted_tags, days = [], [], [], [], [], []
    comparing = False
    if dpg.does_item_exist(f"{tab_label}_bva"): 
        comparing = dpg.get_value(f"{tab_label}_bva")
    bands = getBandsByTab(tab_tag)
    dpg.delete_item(f"{tab_label}_plot_group")

    units = 'µV^2/Hz'
    if 'scaling' in parameter_values and parameter_values['scaling'] == 'spectrum':
        units = 'µV^2'

    if not 'Data' in app_state['windows'][window_id]:
        for j in app_state['windows'][window_id]['Files']:
            if isinstance(j['Data'][tab_tag], dict) and 'Events' in j['Data'][tab_tag].keys():
                mode = 'segment'
                break
        # for j in app_state['windows'][window_id]['Files']:
        #     if 'Events' in j['Data'][tab_tag].keys():
        #         signal_mode = plot_mode = 'segment'
        #         if config['scale'] == 1: #if were plotting in datetime (signal w marked events) and not seconds (cutted events)
        #             signal_mode = plot_mode = None
        #         break
        else: mode = None
    else: mode = None

    deviation_type = 'Standard Deviation'

    with dpg.group(horizontal=True, parent = tab_label,tag=f"{tab_label}_plot_group"):
        with dpg.plot(label=f"Spectral Analysis - {func}", height=400, width=600, tag = f"{tab_label}_plot"):
            dpg.bind_colormap(f"{tab_label}_plot", 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)") #tag=f"{tab_label}_x_axis"
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label=f"LFP Power ({units})", tag= f"{tab_label}_y_axis")

            def contiguous_array(signal, func):
                if func == 'multitaper': 
                    mask = signal[1] <= 100
                    psd = np.ascontiguousarray(signal[0][mask])
                    freqs = np.ascontiguousarray(signal[1][mask])
                else:
                    mask = signal[0] <= 100
                    freqs = np.ascontiguousarray(signal[0][mask])
                    psd = np.ascontiguousarray(signal[1][mask])

                p = {'X': freqs, 'Y': psd}
                return p
            
            power = []
            max_p = 0
            for i,tag in enumerate(tags):
                if mode:
                    stream=getSignalbyIdx(window_id,tab_tag,tag,mode='segment')
                else: stream = getSignalbyIdx(window_id,tab_tag,tag)

                days.append(stream['Date'])
                series_label = dpg.get_item_configuration(tag)['label']
                channel, side = extract_channel_hemisphere(stream['Channel'])
                channels.append(channel)

    	        #BEFORE AND AFTER PSD
                if comparing == True:
                    temp = []
                    zero = [i for i,x in enumerate(stream['X']) if x == 0.0][0]
                    pre_event = stream['Y'][:zero]
                    post_event = stream['Y'][zero:]
                    pre_event = apply_feat(func,parameter_values,pre_event)
                    post_event = apply_feat(func,parameter_values,post_event)
                    
                    #BEFORE-------------------------------------------------
                    p = contiguous_array(pre_event, func)      
                    b_label = 'Before ' + series_label              
                    dpg.add_line_series(p['X'],p['Y'], label=b_label, parent=y_axis, tag = f"{tab_label}_{b_label}_{func}_pre")
                    events_tags.append(f"{tab_label}_{b_label}_{func}_pre")
                    power.append(p)
                    temp.append(p)

                    #AFTER-------------------------------------------------
                    p = contiguous_array(post_event, func)      
                    a_label = 'After ' + series_label              
                    dpg.add_line_series(p['X'],p['Y'], label=a_label, parent=y_axis, tag = f"{tab_label}_{a_label}_{func}_post")
                    events_tags.append(f"{tab_label}_{a_label}_{func}_post")
                    power.append(p)
                    temp.append(p)
                    max_p = max(max_p,np.max(p['Y']))

                    events_names.append(f"{stream['Type']} {i}")
                    states = ['Before', 'After']
                    #TABLE CONTENT
                    full_power = np.sum(p['Y'])

                    if not dpg.does_item_exist(f"{tab_label}_{series_label}"):
                        dpg.add_collapsing_header(label = f'{series_label}', tag =f"{tab_label}_{series_label}", parent = tab_label)
                    else:
                        dpg.delete_item(f"{tab_label}_{series_label}", children_only=True)
                    for i,p in enumerate(temp):
                        freqs, psd = p['X'], p['Y']
                        for b, v in bands.items():
                            band = {b: v}
                            #mean power per band
                            pc = ft.mean_power_all_bands(p, band)
                            std = ft.std_dev_streams(p, band)
                            mean = {'Mean Power (mean, std. dev)': [np.round(pc[b],2), np.round(std[b],2)]}

                            #normalized mean power
                            norm_mean = {'% Mean Power (mean, std. dev)': [np.round(pc[b]*100/full_power,2), np.round(std[b],2)]}

                            #auc
                            params = pre.get_required_params('simpson', module='si')
                            param_auc = {}
                            for name, param in params.items(): param_auc[name] = param
                            mask = (freqs >= v[0]) & (freqs <= v[1])
                            param_auc['y'] = psd[mask]
                            simpson = pre.call_function('simpson', param_dict=param_auc, module='si')
                            auc = {'Sum Power (AUC)': f"{np.round(simpson,2)}"}

                            #normalized auc
                            norm_auc = {'% Sum Power (AUC)': f"{np.round(simpson*100/full_power,2)}"}

                            #peak power
                            peak = ft.peak_per_band(p, band)
                            picos = {'Peak Power (power, frequency)': p for p in peak.values()}


                            info = mean | norm_mean| auc | norm_auc| picos

                            if not dpg.does_item_exist(f"{tab_label}_{series_label}_{states[i]}"): dpg.add_text(f"{states[i]}", parent=f"{tab_label}_{series_label}", tag = f"{tab_label}_{series_label}_{states[i]}")
                            create_table(f"{tab_label}_{series_label}",f"{tab_label}_{series_label}_table_{states[i]}", info, trial_label=b)

                        tables.append(f"{tab_label}_{series_label}_table_{states[i]}")


                #NORMAL PSD
                if comparing == False:
                    y = stream['Y']
                    try:
                        signal = apply_feat(func,parameter_values,y)
                        if isinstance(signal, str): 
                            display_error(tab_tag, signal)
                            return
                        p = contiguous_array(signal, func)
                        max_p = max(max_p,np.max(p['Y']))         
                        dpg.add_line_series(p['X'],p['Y'], label=series_label, parent=y_axis, tag = f"{tab_label}_{series_label}_{func}")
                    except Exception as e: 
                        display_error(tab_tag,e)
                        return
                    
                    power.append(p) 
                    freqs, psd = p['X'], p['Y']      
                    ploted_tags.append(f"{tab_label}_{series_label}_{func}")


                    if not dpg.does_item_exist(f"{tab_label}_hemisphere"):
                                dpg.add_tree_node(tag=f"{tab_label}_hemisphere",
                                    label="By Hemisphere",
                                    parent=tab_label,
                                    default_open=False
                                )

                    if not dpg.does_item_exist(f"{tab_label}_channel"):
                                dpg.add_tree_node(tag=f"{tab_label}_channel",
                                    label="By Channel",
                                    parent=tab_label,
                                    default_open=False
                                )

                    if not dpg.does_item_exist(f"{tab_label}_individual"):
                                dpg.add_tree_node(tag=f"{tab_label}_individual",
                                    label="Individual Streams",
                                    parent=tab_label,
                                    default_open=False
                                )

                    if not dpg.does_item_exist(f"{tab_label}_{side}"):
                        dpg.add_collapsing_header(label = f'{side} HEMISPHERE', tag =f"{tab_label}_{side}", parent = f"{tab_label}_hemisphere")

                    if not dpg.does_item_exist(f"{tab_label}_{stream['Channel']}"):
                        dpg.add_collapsing_header(label = f'{stream['Channel']}', tag =f"{tab_label}_{stream['Channel']}", parent = f"{tab_label}_channel")

                    if not dpg.does_item_exist(f"{tab_label}_{series_label}"):
                        dpg.add_collapsing_header(label = f'{series_label}', tag =f"{tab_label}_{series_label}", parent = f"{tab_label}_individual")
                    else:
                        dpg.delete_item(f"{tab_label}_{series_label}", children_only=True)

                    #TABLE CONTENT
                    for band in bands.items():
                        info = extract_psd_features(p, band)
                        create_table(f"{tab_label}_{series_label}",f"{tab_label}_{series_label}_table", info, trial_label=band[0])
                        create_table(f"{tab_label}_{stream['Channel']}",f"{tab_label}_{stream['Channel']}_table", info, trial_label=f"{band[0]} | {series_label}")
                        create_table(f"{tab_label}_{side}",f"{tab_label}_{side}_table", info, trial_label=f"{band[0]} | {series_label}")

                    tables.append(f"{tab_label}_{series_label}_table")
                    tables.append(f"{tab_label}_{stream['Channel']}_table")
                    tables.append(f"{tab_label}_{side}_table")

                    updateSignalbyIdx(p,tab_tag,tag,func, mode=mode)
                    
                freqs, psd = p['X'], p['Y']
            
            if len(power)>1:
                
                flag = False
                for i in range(len(power)-1):
                    if len(power[i]['Y']) != len(power[i+1]['Y']): 
                        flag = True
                
                if flag == True: #checks if they DON'T have the same len

                    # Define 1-Hz bin edges from 0 to 125 Hz
                    bin_edges = np.arange(0, 100, 1)  # 0–1, 1–2, ..., 124–125
                    bin_centers = bin_edges[:-1] + 0.5

                    # Collect all binned PSDs
                    binned_psds = []

                    for p in power:
                        freqs = p['X']
                        psd = p['Y']
                        
                        binned = []
                        for i in range(len(bin_edges) - 1):
                            fmin, fmax = bin_edges[i], bin_edges[i+1]
                            mask = (freqs >= fmin) & (freqs < fmax)
                            if np.any(mask):
                                binned.append(np.mean(psd[mask]))
                            else:
                                binned.append(np.nan)  # No data in this bin

                        binned_psds.append(binned)

                    # Convert to NumPy array
                    binned_psds = np.array(binned_psds)
                    
                    # Compute mean PSD across trials (ignoring NaNs)
                    all_mean = np.nanmean(binned_psds, axis=0)
                    all_std = np.nanstd(binned_psds, axis=0)
                    freqs = np.arange(0,len(all_mean),1)
                
                else: 
                    all_mean = np.nanmean([p['Y'] for p in power], axis=0)
                    all_std = np.nanstd([p['Y'] for p in power], axis=0)

                minus = all_mean - all_std
                plus = all_mean + all_std

                mean_power = {
                    'Y': all_mean,
                    'X': freqs
                }

                if not dpg.does_item_exist(f"{tab_label}_mean_metric"):
                    dpg.add_collapsing_header(label = 'MEAN POWER', tag =f"{tab_label}_mean_metric", parent = tab_label)
                else:
                    dpg.delete_item(f"{tab_label}_mean_metric", children_only=True)

                for band in bands.items():
                    info = extract_psd_features(mean_power, band)
                    create_table(f"{tab_label}_mean_metric",f"{tab_label}_mean_metric_table", info, trial_label=band[0])

                tables.append(f"{tab_label}_mean_metric_table")

                
                freqs = np.asarray(freqs, dtype=np.float32)
                all_mean = np.asarray(all_mean, dtype=np.float32)
                
                s = dpg.add_shade_series(freqs.tolist(),y1=minus.tolist(),y2=plus.tolist(),label = 'Std. Dev', tag=f"{tab_label}_std", parent=y_axis)
                dpg.bind_item_theme(s, create_alpha_theme())
                m = dpg.add_line_series(freqs.tolist(), all_mean.tolist(), label="Mean Power", parent=y_axis, tag=f"{tab_label}_mean")
                dpg.bind_item_theme(m,change_line_thickness(3))

            dpg.set_axis_limits(x_axis,min(freqs),max(freqs))
            dpg.set_axis_limits(y_axis,min(psd),max(psd))

        def choose_toggle(sender, app_data, user_data):
            if dpg.does_item_exist(f"{tab_label}_bva"): 
                comparing = dpg.get_value(f"{tab_label}_bva")

                if comparing: toggle(sender,app_data,user_data)
                else: toggle2(sender,app_data,user_data)
            else: toggle2(sender,app_data,user_data)

        def toggle(sender,app_data,user_data):
            axis = user_data
            power_temp = []
            if dpg.get_value(f"{tab_label}_hide") == True:
                callback = dpg.get_item_callback(f"{tab_label}_hide")
                dpg.set_value(f"{tab_label}_hide",False)
                if callback:
                    callback(f"{tab_label}_hide", None, dpg.get_item_user_data(f"{tab_label}_hide"))

            for i, tag in enumerate(events_tags):
                key = str(dpg.get_item_label(sender))
                if axis!=None:
                    key = key.split(' ')[axis]
                if key in tag:
                    dpg.configure_item(tag,show=app_data)

                visibility = dpg.get_item_configuration(tag)['show']
                if visibility==True:
                    power_temp.append(power[i])

            mean_temp = np.mean([p['Y'] for p in power_temp], axis=0)
            std = np.std([p['Y'] for p in power_temp], axis=0)
            times = dpg.get_value(f"{tab_label}_radio")
            if times == '95% Confidence Interval':
                times = 2
            else: times = 1

            minus = mean_temp - times*std
            plus = mean_temp + times*std
            dpg.configure_item(f"{tab_label}_mean",y=mean_temp)
            dpg.configure_item(f"{tab_label}_std",y1=minus, y2=plus)
   
        def toggle2(sender,app_data,user_data):
            if dpg.get_value(f"{tab_label}_hide") == True:
                callback = dpg.get_item_callback(f"{tab_label}_hide")
                dpg.set_value(f"{tab_label}_hide",False)
                if callback:
                    callback(f"{tab_label}_hide", None, dpg.get_item_user_data(f"{tab_label}_hide"))

            _ = []
            ch = dpg.get_item_label(sender)
            for tag in ploted_tags:
                if ch in tag:
                    dpg.configure_item(tag, show=app_data)
                flag = dpg.get_item_configuration(tag)['show']
                if flag:
                    _.append(tag)

            array = [dpg.get_value(t)[1] for t in _]
            mean = np.mean(array, axis=0)
            dpg.configure_item(f"{tab_label}_mean",y=mean)

            std = np.std(array, axis=0)
            times = dpg.get_value(f"{tab_label}_radio")
            if times == '95% Confidence Interval':
                times = 2
            else: times = 1

            minus = mean - times*std
            plus = mean + times*std
            dpg.configure_item(f"{tab_label}_mean",y=mean)
            dpg.configure_item(f"{tab_label}_std",y1=minus, y2=plus)

        def deviation(sender, app_data, user_data):
            if app_data!=user_data:
                media = np.array(dpg.get_value(f"{tab_label}_mean")[1])
                std_dev = np.array(dpg.get_value(f"{tab_label}_std")[1])

                if app_data == '95% Confidence Interval':
                    dev = (std_dev - media) * -2
                else:
                    dev = (std_dev - media) * -0.5

                minus = media - dev
                plus = media + dev  
                dpg.configure_item(f"{tab_label}_std", y1=minus.tolist(), y2=plus.tolist())
                dpg.configure_item(f"{tab_label}_radio",user_data=app_data)

        checkboxes = []
        with dpg.group(parent=f"{tab_tag}_buttons"):
            # dpg.add_checkbox(label='Change to dB',callback=Volt2dB, user_data=(signal_tags,tab_tag,func, tab_label, tables), tag = f"{tab_label}_2db")
            dpg.add_checkbox(label='Change to dB',callback=Volt2dB, user_data=(y_axis, tab_label, ploted_tags, tables), tag = f"{tab_label}_2db")
            if mode == 'segment': 
                dpg.add_checkbox(label='Before vs. After',callback=before_vs_after, user_data=(signal_tags,tab_label,func,tab_tag,parameter_values), tag = f"{tab_label}_bva", default_value=comparing)
            if comparing== True:
                
                dpg.add_separator()
                dpg.add_text('Toggle Streams')
                with dpg.group(parent=f"{tab_tag}_buttons", horizontal=True):   
                    with dpg.group(): #Before and After
                        dpg.add_text('When:')
                        cc = dpg.add_checkbox(label='Before', default_value=True, callback=toggle, user_data=-1)
                        c = dpg.add_checkbox(label='After', default_value=True, callback=toggle, user_data=-1)
                        checkboxes.append(cc)
                        checkboxes.append(c)
                    
                    with dpg.group(): #Per Type of Event
                        events_type = [name.split(' ')[0] for name in events_names]
                        events_type = np.unique(events_type)
                        dpg.add_text('What:')
                        for i, etype in enumerate(events_type):
                            c = dpg.add_checkbox(label=etype, callback=toggle, default_value=True)
                            checkboxes.append(c)

                dpg.set_item_user_data(f"{tab_label}_hide",(ploted_tags, checkboxes))
            channels = np.unique(channels)
            days = np.unique(days)
            with dpg.group(parent=f"{tab_tag}_buttons", horizontal=True):  
                if len(channels)>1: 
                    with dpg.group(): #channels
                        dpg.add_text('Channels: ')
                        for ch in channels:
                            c = dpg.add_checkbox(label=ch, callback=choose_toggle, default_value=True)
                            checkboxes.append(c)
                if len(days)>1:
                    with dpg.group(): #days
                        dpg.add_text('Recordings: ')
                        for d in days:
                            c = dpg.add_checkbox(label=d, callback=choose_toggle, default_value=True)
                            checkboxes.append(c)
                with dpg.group(): #side
                    dpg.add_text('Hemisphere: ')
                    sides = ['LEFT', 'RIGHT']
                    for d in sides:
                        c = dpg.add_checkbox(label=d, callback=choose_toggle, default_value=True)
                        checkboxes.append(c)
            dpg.add_separator()
            dpg.add_checkbox(label='Hide signals', callback=hide, tag = f"{tab_label}_hide", user_data=(ploted_tags, checkboxes))
            dpg.add_separator()
            dpg.add_text('Shaded Area')
            dpg.add_radio_button(['Standard Deviation', '95% Confidence Interval'], horizontal=False, callback=deviation, tag = f"{tab_label}_radio",user_data=deviation_type)
            
    time.sleep(0.2)
    dpg.set_axis_limits_auto(x_axis)
    dpg.set_axis_limits_auto(y_axis)

def plot_spectrogram_joined(tags, tab_label, func, tab_tag, parameter_values, mode = None):
    window_id = extract_window_id(tab_tag)
    wt = extract_type_window(window_id)
    
    new_signal, identifiers = {}, {}
    for tag in tags:
        signal = getSignalbyIdx(window_id,tab_tag,tag)
        ch = signal['Channel']
        if ch in electrodes_names.keys():
            ch = electrodes_names[ch]
        else:
            electrodes_names[ch] = ch

        if func in signal.keys(): signal.pop(func)
        temp = {key: np.array([]) for key in signal.keys()}
        temp['dX'] = []
        if ch not in new_signal.keys(): new_signal[ch] = temp
        else: new_signal[ch] = new_signal[ch] | temp
 
    current_start, prev_end_time = {}, {}
    for tag in tags:
        signal = getSignalbyIdx(window_id,tab_tag,tag)
        '''X = signal['X']
        arr = np.array(X)
        if np.issubdtype(arr.dtype, np.number):
            valid = arr[~np.isnan(arr)]
            if len(valid) > 0:# and np.round(valid[0]) == 0:
                # 'X' is in seconds
                signal['dX'] = [signal['Date'] + timedelta(seconds=val) for val in X]
        else:
            # 'X' is in Unix timestamp
            signal['dX'] = [datetime.fromtimestamp(val) for val in X]
       
        ch = signal['Channel']
        for key in signal.keys():
            if key == 'dX' or key == 'Y':
                new_signal[ch][key] = np.append(new_signal[ch][key], np.array(signal[key]))
                identifiers[ch] = len(signal[key])
            else:
               new_signal[ch][key] = np.append(new_signal[ch][key], signal[key])'''
        
        '''Good version - For individual and combined?'''
        X = signal['X']
        arr = np.array(X)
        

        if np.issubdtype(arr.dtype, np.number):
            valid = arr[~np.isnan(arr)]
            if len(valid) > 0:# and np.round(valid[0]) == 0:
                # 'X' is in seconds
                signal['dX'] = [signal['Date'] + timedelta(seconds=val) for val in X]
        else:
            # 'X' is in Unix timestamp
            signal['dX'] = [datetime.fromtimestamp(val) for val in X]
        ch = signal['Channel']
        if ch in electrodes_names.keys():
            ch = electrodes_names[ch]
        else:
            electrodes_names[ch] = ch
        prev = len(new_signal[ch]['dX'])

        current_start[ch] = signal['dX'][0]
    
        # Insert zero gap if there's a time difference
        if ch in prev_end_time:
            gap = current_start[ch] - prev_end_time[ch]
            
            if gap.total_seconds() > 0:
                # Limit the gap to 10 min
                gap = min(gap, timedelta(minutes=1))
                
                # Determine how many points to fill (based on sampling rate)
                sample_rate = 250
                n_fill = int(gap.total_seconds() * sample_rate)
                
                if n_fill > 0:
                    # Generate filler time and zero signal
                    filler_dX = [prev_end_time[ch] + timedelta(seconds=i / sample_rate) for i in range(n_fill)]
                    filler_Y = np.zeros(n_fill)
                    
                    # Append the filler
                    new_signal[ch]['dX'] = np.append(new_signal[ch]['dX'], filler_dX)
                    new_signal[ch]['Y'] = np.append(new_signal[ch]['Y'], filler_Y)

        else: prev_end_time[ch] = None

        for key in signal.keys():
            if key == 'dX' or key == 'Y':
                new_signal[ch][key] = np.append(new_signal[ch][key], np.array(signal[key]))
                identifiers[ch] = len(signal[key])
            elif key == 'Events':
                for e in signal[key]:
                    e['Idx'] = e['Idx'] + prev
                new_signal[ch][key] = np.append(new_signal[ch][key], signal[key])
            else:
                new_signal[ch][key] = np.append(new_signal[ch][key], signal[key])
            
        prev_end_time[ch] = signal['dX'][-1]

    num_plots = len(new_signal.keys())
    num_cols = 1
    num_rows = num_plots
    global_min, global_max = 0,0



    per_tag = {}
    
    with dpg.group(horizontal=True, parent=f"{tab_label}", tag=f"{tab_label}_plot_group"):

        with dpg.subplots(rows=num_rows, columns=num_cols, label="Spectrograms", width=800, height=400*num_rows, tag = f"{tab_label}_subplots"):

            for channel in new_signal:

                title =f"Joined Spectrogram - {channel}"
                subplot_tag = f"{tab_label}_joined_{channel}"
                # titles.append(channel)

                with dpg.plot(label=title, width=500, height=400, tag=subplot_tag, parent=f"{tab_label}_subplots"):
                    x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (DateTime)", scale= dpg.mvPlotScale_Time)
                    y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

                    y = new_signal[channel]['Y']
                    if current_start == {}:
                        x = new_signal[channel]['dX']
                        if isinstance(x[0], (int, float)): x = [datetime.fromtimestamp(val) for val in x]
                        x = [(xx + timedelta(hours=1)).timestamp() for xx in x]
                    else:
                        x = np.arange(0,len(y)/250,1)
                        dpg.configure_item(x_axis, scale = dpg.mvPlotScale_Linear)

                    
                    try: events = new_signal[channel]['Events']
                    except Exception as e: 
                        events = 'None'
                        print(e)

                    parameter_values['x'] = np.array(y)
                    signal = pre.call_function(func, parameter_values)

                    frequencies, times, Sxx = signal
                    Sxx_log = 10 * np.log10(Sxx + 1e-10)  # Convert to dB scale
                    Sxx_log = np.flipud(Sxx_log)

                    # channels.append(Sxx_log)

                    per_tag[channel] = [Sxx_log,subplot_tag, title, events,x]
                    global_min = min(global_min, Sxx_log.min())
                    global_max = max(global_max, Sxx_log.max())  

                    dpg.add_heat_series(Sxx_log.flatten(), rows=Sxx_log.shape[0], cols=Sxx_log.shape[1],
                                    scale_min=global_min, scale_max=global_max,
                                    parent=y_axis, format="",bounds_min=[x[0],0], bounds_max=[x[-1],125])
                    dpg.bind_colormap(subplot_tag, dpg.mvPlotColormap_Jet)  

                    if not isinstance(events,str):
                        for event in events:
                            # stamp = (event['Date'] + timedelta(hours=1) + timedelta(seconds=(event['Idx']/250))).timestamp() #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                            stamp = event['Idx']/250 #axis is seconds, not datetime
                            type = event['Type']
                            dpg.add_plot_legend()
                            dpg.add_inf_line_series(x=[stamp],label=f'{type}',parent=y_axis)

        dpg.add_colormap_scale(tag=f"{tab_label}_colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Jet,
                                            min_scale = global_min, max_scale=global_max, height=400*num_rows)
        
        def link(sender, app_data):
            dpg.configure_item(f"{tab_label}_subplots", link_all_x=app_data, link_all_y=app_data)

        def mean(sender,app_data):
            mean_Sxx = np.mean(np.stack(channels), axis=0)
            with dpg.plot(label='Mean Spectrogram', width=-1, height=400, tag=f"{tab_label}_join_mean", parent=f"{tab_label}_merged"):
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

                if mode and wt=='Combined':
                    emin = -int(dpg.get_value(f"{tab_tag}_emin"))
                    emax = int(dpg.get_value(f"{tab_tag}_emax"))
                else:
                    emin, emax = 0, len(times)

                dpg.add_heat_series(mean_Sxx.flatten(), rows=mean_Sxx.shape[0], cols=mean_Sxx.shape[1],
                                    scale_min=global_min, scale_max=global_max,
                                    parent=y_axis, format="", bounds_min=[emin,0], bounds_max=[emax,125])
                dpg.bind_colormap(f"{tab_label}_join_mean", dpg.mvPlotColormap_Jet)

                if not isinstance(events,str):
                    for event in events:
                        stamp = event['Idx']/250 #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                        type = event['Type']
                        dpg.add_plot_legend()
                        dpg.add_inf_line_series(x=[stamp],label=f'{type}',parent=y_axis)
    
        def merge_spectrograms(sender,app_data,user_data):
            bands = getBandsByTab(tab_tag)
            if dpg.does_item_exist(f"{tab_label}_merged"): dpg.delete_item(f"{tab_label}_merged")

            with dpg.group(parent=tab_label, tag = f"{tab_label}_merged"): 

                alpha_theme = create_alpha_theme()
                
                dpg.add_text('Band Power over Time', parent=f"{tab_label}_merged")
                dpg.add_separator(parent=f"{tab_label}_merged")
                for _, value in per_tag.items():
                    sxx, plot_tag, plot_label, stream_events, time = value
                    header_tag = f"{plot_tag}_header"
                    if dpg.does_item_exist(header_tag): dpg.delete_item(header_tag, children_only=True)

                    with dpg.collapsing_header(tag=header_tag, parent=f"{tab_label}_merged", label=plot_label):

                        with dpg.plot(label=plot_label, width=-1):
                            dpg.add_plot_legend()
                            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Power (dB)")

                            for b,v in bands.items():
                                mask = (frequencies*125 >= v[0]) & (frequencies*125 < v[1])
                                if np.any(mask):
                                    # power = np.mean(sxx[mask, :],axis=0)  # mean across freqs -> shape: (time,)
                                    power = sxx[mask, :]
                                    std = np.std(sxx[mask, :], axis=0)
                                    min_std = power-std
                                    max_std = power+std                                    
                                    
                                    dpg.add_shade_series(time,min_std,y2=max_std,label = f"{b} Std. Deviation", tag=f"{plot_tag}_{b}_std", parent=y_axis)
                                    dpg.bind_item_theme(f"{plot_tag}_{b}_std", alpha_theme)
                                    dpg.add_line_series(time,power,label = f"{b} Power", tag=f"{plot_tag}_{b}_mean", parent=y_axis)

                            if not isinstance(stream_events,str) and wt == 'Individual':
                                for event in stream_events:
                                    # stamp = [event['Idx']/(len(times)*250)] #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                                    stamp = [event['Idx']/250]
                                    type = event['Type']
                                    if stamp[0] <= time[-1]:
                                        dpg.add_plot_legend()
                                        dpg.add_inf_line_series(x=stamp,label=f'{type}',parent=y_axis)
            
        with dpg.group(horizontal=False):
            dpg.add_checkbox(label='Synchronize Axis', callback=link) 
            dpg.add_button(label='Band Power over Time', callback=merge_spectrograms)     

def plot_df_coherence(parameter_values,tab_tag,tags):
    labels = [dpg.get_item_label(tag) for tag in tags]
    tab_label = f"{tab_tag}_df_coherence"
    window_id = extract_window_id(tab_tag)

    def plot():
        labs = []
        for no in ['0','1']:
            tag = f"{tab_label}_s{no}"
            lab = dpg.get_value(tag)
            idx = labels.index(lab)
            signal = getSignalbyIdx(window_id,tab_tag,tags[idx])
            if no =='0': parameter_values['x'] = signal
            else: parameter_values['y'] = signal
            labs.append(lab)
            
        if labs[0]==labs[1]:return
        plot_coherence(parameter_values,tab_label)
        
    combos = {}
    with dpg.group(horizontal=True,parent=tab_label):
        for i,s in enumerate(['Signal 1','Signal 2']):
            input_id = dpg.add_combo(
                    label=s,
                    items=labels,  # <-- customize your options
                    default_value='---',
                    callback=different_combo,
                    user_data=(tab_label, combos),
                    tag = f"{tab_label}_s{i}",
                    width=200
                )
            combos[s] = input_id
        dpg.add_button(label='Plot coherence', callback=plot,width=200)

def plot_coherence(parameter_values, tab_label):

    if not dpg.does_item_exist(f"{tab_label}_clean"): 
        dpg.add_checkbox(label = 'Clean Previous Plot', parent=tab_label,default_value=True,tag=f"{tab_label}_clean")

    signal1 = parameter_values['x']
    signal2 = parameter_values['y']
    parameter_values['x'] = signal1['Y']
    parameter_values['y'] = signal2['Y']
    parameter_values['fs'] = 250

    clean = dpg.get_value(f"{tab_label}_clean")
    if clean==True: 
        dpg.delete_item(f"{tab_label}_plot_group")

    freq, coh = pre.call_function('coherence', parameter_values)
    mask = freq <= 100
    freq, coh = freq[mask], coh[mask]

    # parameter_values['nfft'] = 512
    p2 = parameter_values.copy()
    _, pxy = pre.call_function('csd',parameter_values)
    _, pxx = pre.call_function('welch',parameter_values)
    p2['x'] = parameter_values['y']
    _, pyy = pre.call_function('welch', p2)

    im = pxy/np.sqrt(pxx*pyy)
    ab = np.abs(im)[mask]
    IMcoh = np.abs(np.imag(im)[mask])

    if clean:
        with dpg.group(parent=tab_label, tag=f"{tab_label}_plot_group"):
            with dpg.group(parent=f"{tab_label}_plot_group", tag = f"{tab_label}_plot_group_text"):
                dpg.add_text(f"Signal 1: {signal1['Channel']} - {signal1['Date']}")
                dpg.add_text(f"Signal 2: {signal2['Channel']} - {signal2['Date']}")
            with dpg.plot(label = 'Coherence', width=-1, height=400, tag=f"{tab_label}_plot"):
                dpg.bind_colormap(f"{tab_label}_plot", 0)
                dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)") #tag=f"{tab_label}_x_axis"
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Coherence", tag= f"{tab_label}_y_axis")
    else:
        dpg.delete_item(f"{tab_label}_plot_group_text")
        with dpg.group(parent=f"{tab_label}_plot_group", tag = f"{tab_label}_plot_group_text"):
            dpg.add_text(f"Signal 1: {signal1['Channel']} - {signal1['Date']}")
            dpg.add_text(f"Signal 2: {signal2['Channel']} - {signal2['Date']}")

  
    dpg.add_line_series(freq.tolist(), coh.tolist(), label=f"Coherence | {signal1['Channel']}-{signal2['Channel']}", parent=f"{tab_label}_y_axis")
    dpg.add_line_series(freq.tolist(), IMcoh.tolist(), label=f"Imaginary Coherence | {signal1['Channel']}-{signal2['Channel']}", parent=f"{tab_label}_y_axis")
    
    dpg.set_axis_limits(f"{tab_label}_y_axis",ymin=0,ymax=1)
    bands = getBandsByTab(tab_label)
    for b,band in bands.items():
        mask2 = (freq >= band[0]) & (freq <= band[1])
        p = {'X': freq[mask2], 'Y':list(coh[mask2])}
        info = extract_timeline_features(p,coh, coherence=True)
        create_table(tab_label,f"{tab_label}_table", info, trial_label=f"{b} | {signal1['Channel']}-{signal2['Channel']}")


    time.sleep(0.2)
    dpg.set_axis_limits_auto(f"{tab_label}_y_axis")

def plot_multitaper_coherence(parameter_values,tab_tag,tags,flag=None):
    labels = [dpg.get_item_label(tag) for tag in tags]
    if flag == None:
        tab_label = f"{tab_tag}_df_multitaper coherence"
    else: tab_label = f"{tab_tag}_multitaper coherence"
    window_id = extract_window_id(tab_tag)
    wt = extract_type_window(window_id)
    bands = getBandsByTab(tab_tag)

    def calculate():
        if dpg.does_item_exist(f"{tab_label}_plot_group"): 
            dpg.delete_item(f"{tab_label}_plot_group")

        if dpg.does_item_exist(f"{tab_label}_spec_group"): 
            dpg.delete_item(f"{tab_label}_spec_group")
            dpg.delete_item(f"{tab_label}_progress_bar")

        if flag==None:
            for no in ['0','1']:
                tag = f"{tab_label}_s{no}"
                lab = dpg.get_value(tag)
                idx = labels.index(lab)
                signal = getSignalbyIdx(window_id,tab_tag,tags[idx])
                if no =='0': signal1 = signal
                else: signal2 = signal
        else:
            for s in ['x','y']:
                idx = labels.index(parameter_values[s])
                signal = getSignalbyIdx(window_id,tab_tag,tags[idx])
                if s == 'x':
                    signal1 = signal
                else: signal2= signal

        if len(signal1['Y'])>len(signal2['Y']):
            raw=signal2['Y']
        else: raw = signal1['Y']

        window_len = 512
        if flag==None:
            step = window_len // 8
            nfft = window_len
            kmax = 2*parameter_values['NW'] - 1
            parameter_values['Kmax'] = kmax
            parameter_values['M'] = window_len
        else:
            step = int(parameter_values['step'])
            nfft = parameter_values['nfft']
            if step == ' ': step =2
            if nfft == ' ': nfft = 256
            parameter_values['step'] = window_len//step
            parameter_values['nfft'] = max(window_len,int(nfft))
            parameter_values['M'] = window_len

        tapers = pre.call_function('dpss', parameter_values, module = 'ssw')

        Sxx_sum = np.zeros(nfft//2+1, dtype=np.complex128)
        Syy_sum = np.zeros(nfft//2+1, dtype=np.complex128)
        Sxy_sum = np.zeros(nfft//2+1, dtype=np.complex128)
        n_windows = 0
        coh_segments,imcoh_segments = [], []
        for start in range(0, len(raw) - window_len + 1, step):
            xw = signal1['Y'][start:start+window_len]
            yw = signal2['Y'][start:start+window_len]
            Sxx_tapers, Syy_tapers, Sxy_tapers = [], [], []
            for taper in tapers:
                S1 = np.fft.rfft(xw * taper, n=nfft)
                S2 = np.fft.rfft(yw * taper, n=nfft)
                # Sxx_tapers.append(np.abs(S1)**2)
                # Syy_tapers.append(np.abs(S2)**2)
                Sxx_tapers.append(S1*np.conj(S1))
                Syy_tapers.append(S2*np.conj(S2))
                Sxy_tapers.append(S1 * np.conj(S2))
            Sxx_sum += np.mean(Sxx_tapers, axis=0)
            Syy_sum += np.mean(Syy_tapers, axis=0)
            Sxy_sum += np.mean(Sxy_tapers, axis=0)
            n_windows += 1

            coh_seg = np.abs(Sxy_sum)**2 / (Sxx_sum.real * Syy_sum.real)
            imcoh_seg = np.abs(np.imag(Sxy_sum) / np.sqrt(Sxx_sum.real * Syy_sum.real))

            coh_segments.append(coh_seg)
            imcoh_segments.append(imcoh_seg)

        Sxx = Sxx_sum.real / n_windows
        Syy = Syy_sum.real / n_windows
        Sxy = Sxy_sum / n_windows

        # coh = np.abs(Sxy)**2 / (Sxx * Syy)

        #3rd
        coh = np.mean(coh_segments, axis=0)


        freq = np.fft.rfftfreq(nfft, d=1/250)
        mask = freq <= 100
        freq, coh = freq[mask], coh[mask]

        #1st
        # im = Sxy/np.sqrt(Sxx*Syy)
        # imcoh = np.abs(np.imag(im)[mask])
        # ab = np.abs(im)[mask]

        #2nd
        # imcoh = np.abs(np.imag(Sxy) / np.sqrt(Sxx * Syy))
        
        #3rd
        imcoh = np.mean(imcoh_segments, axis=0)
        
        imcoh = imcoh[mask]
        label=f"{signal1['Channel']}-{signal2['Channel']}"
        plot(signal1,signal2,freq,coh,imcoh, label)

        if not dpg.does_item_exist(f"{tab_label}_coh_spec"):
            dpg.add_button(label = 'Plot Coherence Spectrogram',width=-1,tag=f"{tab_label}_coh_spec", callback=spectrogram, user_data = (signal1,signal2, tapers, freq, mask), parent=tab_label)
        else:
            dpg.set_item_user_data(f"{tab_label}_coh_spec", user_data=(signal1,signal2, tapers, freq, mask))

    def plot(signal1,signal2,freq,coh,imcoh,label):
        with dpg.group(parent=tab_label, tag=f"{tab_label}_plot_group"):
            dpg.add_text(f"Signal 1: {signal1['Channel']} - {signal1['Date']}")
            dpg.add_text(f"Signal 2: {signal2['Channel']} - {signal2['Date']}")
            with dpg.plot(label = 'Multitaper Coherence', width=-1, height=400, tag=f"{tab_label}_plot"):
                dpg.bind_colormap(f"{tab_label}_plot", 0)
                dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)") #tag=f"{tab_label}_x_axis"
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Coherence", tag= f"{tab_label}_y_axis")


                # freq, coh = freq.tolist(), coh.tolist()
                dpg.add_line_series(freq.tolist(), coh.tolist(), label=f'Multitaper Coherence | {label}', parent=y_axis)
                dpg.add_line_series(freq.tolist(), imcoh.tolist(), label=f'Imaginary Multitaper Coherence | {label}', parent=y_axis)
                dpg.set_axis_limits(y_axis,ymin=0,ymax=1)

                for b,band in bands.items():
                    mask2 = (freq >= band[0]) & (freq <= band[1])
                    p = {'X': freq[mask2], 'Y':list(coh[mask2])}
                    info = extract_timeline_features(p,coh, coherence=True)
                    create_table(tab_label,f"{tab_label}_table", info, trial_label=f"{b} | {signal1['Channel']}-{signal2['Channel']}")

        time.sleep(0.2)
        dpg.set_axis_limits_auto(y_axis)

    def spectrogram(sender,app_data,user_data):
        signal1,signal2, tapers, freqs, mask = user_data
        
        if dpg.does_item_exist(f"{tab_label}_progress_bar"): 
            dpg.set_value(f"{tab_label}_progress_bar",0.0)
        else: dpg.add_progress_bar(parent=tab_label, default_value=0.0, overlay='Coherogram Loading', tag = f"{tab_label}_progress_bar",width=-1)

        if len(signal1['Y'])>len(signal2['Y']):
            raw=signal2['Y']
        else: raw = signal1['Y']
        window_len = parameter_values['M']
        if 'step' not in parameter_values.keys():
            step = 8
            nfft = max(window_len, 512)
            step = window_len // step
        else: 
            step = parameter_values['step']
            nfft = int(parameter_values['nfft'])
        freqs = np.fft.rfftfreq(nfft, d=1/250)
        mask = freqs <= 100
        freqs = freqs[mask]
        
        K = int(parameter_values['Kmax'])
        starts = np.arange(0, len(raw)-window_len+1, step)
        matrix = np.zeros((len(freqs), len(starts)))
        for idx, s in enumerate(starts):
            signal1w, signal2w = signal1['Y'][s:s+window_len], signal2['Y'][s:s+window_len]
            Sxx = Syy = Sxy = 0
            for tap in tapers:
                X = np.fft.rfft(signal1w * tap, n=nfft)
                Y = np.fft.rfft(signal2w * tap, n=nfft)
                Sxx += np.abs(X)**2
                Syy += np.abs(Y)**2
                Sxy += X * np.conj(Y)

            total = len(starts)
            progress = (idx+1)/total
            dpg.set_value(f"{tab_label}_progress_bar",np.round(progress,2))
            Sxx /= K
            Syy /= K
            Sxy /= K
            coh = np.abs(Sxy)**2 / (Sxx * Syy)
            matrix[:, idx] = coh[mask]
        
        matrix = np.flipud(np.array(matrix))
        times = (starts + window_len/2) / 250
        header_tag = f"{tab_label}_cot"
        with dpg.group(parent=tab_label, tag=f"{tab_label}_spec_group", horizontal=True):
            dpg.add_colormap_scale(tag=f"{tab_label}_colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Viridis,
                                            min_scale = 0, max_scale=1, height=400)

            with dpg.plot(label='Coherogram', width=-1, height=400, tag=f"{tab_label}_spec"):
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

                dpg.add_heat_series(matrix.flatten(), rows=len(freqs), cols=len(times),
                                            scale_min=0, scale_max=1, 
                                            parent=y_axis, format="",bounds_min=[0,0], bounds_max=[int(len(signal1['Y'])/250),100])
                                            
                    
                dpg.bind_colormap(f"{tab_label}_spec", dpg.mvPlotColormap_Viridis)

            if dpg.does_item_exist(header_tag): dpg.delete_item(header_tag, children_only=True)

            with dpg.collapsing_header(tag=header_tag, parent=tab_label, label='Coherence over time'):

                alpha_theme = create_alpha_theme()

                with dpg.plot(label='Coherence over time', width=-1):
                    dpg.add_plot_legend()
                    x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                    y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Power (dB)")
                    
                    for b,v in bands.items():
                        mask = (freqs >= v[0]) & (freqs < v[1])
                        if np.any(mask):
                            power = np.flipud(matrix)[mask, :]
                            std = np.std(matrix[mask, :], axis=0)
                            min_std = power-std
                            max_std = power+std

                            c = dpg.add_shade_series(times,min_std,y2=max_std,label = f"{b} Std. Deviation", parent=y_axis)
                            dpg.bind_item_theme(c, alpha_theme)
                            l = dpg.add_line_series(times,power,label = f"{b} Power", parent=y_axis)
                            dpg.bind_item_theme(l, change_line_thickness(3))
                  
    combos = {}
    if flag == None:
        with dpg.group(horizontal=True,parent=tab_label):
            for i,s in enumerate(['Signal 1','Signal 2']):
                input_id = dpg.add_combo(
                        label=s,
                        items=labels,  # <-- customize your options
                        default_value='---',
                        callback=different_combo,
                        user_data=(tab_label, combos),
                        tag = f"{tab_label}_s{i}",
                        width=200
                    )
                combos[s] = input_id
            dpg.add_button(label='Plot Coherence', callback=calculate,width=200,tag=f"{tab_label}_coh")
    else:
        calculate()
    
def plot_cross_correlation(parameter_values,tab_tag,tags, mode = None):
    if mode:
        tab_label = f"{tab_tag}_df_cross-correlation"
    else: tab_label = f"{tab_tag}_cross-correlation"

    labels = [dpg.get_item_label(tag) for tag in tags]
    window_id = extract_window_id(tab_tag)
    toggle_tags = []

    def toggle(sender,app_data,user_data):
        # print(toggle_tags)
        labs = [dpg.get_item_label(tag) for tag in toggle_tags]
        name_band = dpg.get_item_label(sender)
        for idx,l in enumerate(labs):
            if name_band in l:
                dpg.configure_item(toggle_tags[idx], show=app_data)

    def plot():
        nonlocal toggle_tags
        plot_mode = dpg.get_value(f"{tab_label}_band")
        signal1, signal2 = None, None
        if mode:
            for i,key in enumerate(['a','v']):
                lab = dpg.get_value(f"{tab_label}_s{i}")
                index = labels.index(lab)
                signal = getSignalbyIdx(window_id,tab_tag,tags[index])
                parameter_values[key] = signal['Y']
                if key == 'a': signal1 = signal
                else: signal2 = signal
        else: 
            for key in ['a','v']:
                lab = parameter_values[key]
                index = labels.index(lab)
                signal = getSignalbyIdx(window_id,tab_tag,tags[index])
                parameter_values[key] = signal['Y']
                if key == 'a': signal1 = signal
                else: signal2 = signal

        if dpg.does_item_exist(f"{tab_label}_size_warning"): dpg.delete_item(f"{tab_label}_size_warning")
        # parameter_values['method'] = 'direct'
        s1, s2 = parameter_values['a'], parameter_values['v']
        if len(s1) == len(s2) and parameter_values['mode'] == 'valid':
            parameter_values['mode'] = 'full'
            dpg.add_text("Mode changed to 'full' because signals have the same length!", parent=tab_label, tag = f"{tab_label}_size_warning")

        if dpg.does_item_exist(f"{tab_label}_cc"): 
            dpg.delete_item(f"{tab_label}_text")
            dpg.delete_item(f"{tab_label}_cc",children_only=True)
        else: 
            dpg.add_group(tag=f"{tab_label}_cc", parent=tab_label, horizontal=True)

        with dpg.group(tag=f"{tab_label}_text", parent=tab_label):
            dpg.add_text(f"Signal 1: {signal1['Channel']} - {signal1['Date']}",parent=f"{tab_label}_text")
            dpg.add_text(f"Signal 2: {signal2['Channel']} - {signal2['Date']}",parent=f"{tab_label}_text")
        with dpg.plot(label="Cross-correlation", height=300, width=800, parent=f"{tab_label}_cc"):
            dpg.add_plot_legend()
            cross_x = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
            cross_y = dpg.add_plot_axis(dpg.mvYAxis, label="Lfp µV^2")

        if plot_mode:
            bands = getBandsByTab(tab_tag)
        else:
            bands = {'Bands': 'b'}

        d = parameter_values['dislocation']
        if d == ' ' or d == '': d = 1
        else: d = int(d)
        shape = parameter_values['mode']
        normalize = parameter_values['normalization']
        if normalize == ' ' or normalize == '': normalize = 'False'
            
        for b, band in bands.items():
            for key in ['a','v']:
                if not isinstance(band,str):
                    param_filter = {'N': '4', 'Wn': band,'btype':'band','fs': '250'}
                    args = pre.call_function('butter', param_filter) 
                    parameter_values[key] = pre.call_function2('filtfilt', *args, parameter_values[key])

            correlation =pre.call_function('correlate', parameter_values, module='np')
            N, D = len(signal1['Y']), len(signal2['Y'])
            match shape:
                case 'full': 
                    dislocation = np.arange(-(D-1), N) / 250
                    # dislocation = np.arange((-len(signal1['Y'])+d)/250,(len(signal1['Y'])/250),1/250)
                case 'same': dislocation = (np.arange(N) - D//2) / 250
                case 'valid': dislocation = np.arange(N-D+1) / 250
            if normalize == 'True':
                correlation = correlation / np.max(np.abs(correlation))

            if plot_mode: 
                label = f"{b} Cross-Correlatation"
                info_mode = b
                if not dpg.does_item_exist(f"{tab_label}_cc_buttons"):
                    dpg.add_group(tag=f"{tab_label}_cc_buttons", parent = f"{tab_label}_cc", horizontal=False)
                dpg.add_checkbox(label=b,parent=f"{tab_label}_cc_buttons",default_value=True,callback=toggle)
            else: 
                label = "Cross-correlation"
                info_mode = None

            dpg.add_line_series(dislocation.tolist(), correlation.tolist(),label=label, parent=cross_y,tag=f"{tab_label}_{label}")
            toggle_tags.append(f"{tab_label}_{label}")

            p = {'Y': correlation.tolist(),'X':dislocation.tolist()}
            info, line_tags = extract_cc_features(p,cross_y,tab_label,info_mode)
            label = f"{signal1['Channel']} - {signal2['Channel']}"

            toggle_tags = toggle_tags + line_tags
            

            if not dpg.does_item_exist(f"{tab_label}_header"): 
                dpg.add_collapsing_header(tag = f"{tab_label}_header", parent=tab_label, label=label)

            create_table(f"{tab_label}_header",f"{tab_label}_table",info,b)


    if not dpg.does_item_exist(f"{tab_label}_band"): 
        dpg.add_checkbox(label='Band Cross-Correlation', parent=tab_label, tag = f"{tab_label}_band")

    if mode==None:
        plot()
    else:
        combos = {}
        with dpg.group(horizontal=True,parent=tab_label):
            parameter_values['mode'] = 'full'
            parameter_values['dislocation'] = '1'
            parameter_values['normalization'] = 'True'

            for i,s in enumerate(['Signal 1','Signal 2']):
                input_id = dpg.add_combo(
                        label=s,
                        items=labels,  # <-- customize your options
                        default_value='---',
                        tag = f"{tab_label}_s{i}",
                        width=200
                        # callback=different_combo,
                        # user_data=(tab_label, combos),
                    )
                combos[s] = input_id
            dpg.add_button(label='Plot Cross-Correlation', callback=plot,width=200)      

def plot_spectrogram_og(tags, tab_label, func, tab_tag, parameter_values, mode = 'segment'):
    window_id = extract_window_id(tab_tag)
    wt = extract_type_window(window_id)
    if wt == 'Individual': mode = None
    
    
    num_plots = len(tags)
    num_cols = 2
    num_rows = (num_plots + 1) // num_cols 

    global_min = 0
    global_max = 1

    Merge = []
    per_file = {}
    per_tag = {}
    parameter_values['fs'] = 250

    for i, tag in enumerate(tags):
        file = extract_file_from_series_tag(tag)
        per_file[file] = []

    with dpg.group(horizontal=True, parent=f"{tab_label}", tag=f"{tab_label}_plot_group"):

        dpg.add_colormap_scale(tag=f"{tab_label}_colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Jet,
                                            min_scale = global_min, max_scale=global_max, height=400*num_rows)
        
        with dpg.subplots(rows=num_rows, columns=num_cols, label="Spectrograms", width=800, height=400*num_rows, tag=f"{tab_label}_subplots"):
            for i,tag in enumerate(tags):
                stream = getSignalbyIdx(window_id, tab_tag, tag, mode=mode)
                stream_events = getEventsbyTag(tab_tag,tag)
                if stream_events!=[]: all_events = stream_events
                file = extract_file_from_series_tag(tag)
                y = stream['Y']
                channel = stream['Channel']
                date = stream['Date']
                parameter_values['x'] = np.array(y)
                signal = pre.call_function(func, parameter_values)
                per_file[file].append(signal)

                Merge.append(signal)

                frequencies, times, Sxx = signal
                Sxx_log = 10 * np.log10(Sxx + 1e-10)  # Convert to dB scale
                Sxx_log = np.flipud(Sxx_log)

                global_min = min(global_min, Sxx_log.min())
                global_max = max(global_max, Sxx_log.max())

                # Create a new subplot for each heat series
                if mode and wt == 'Combined':
                    plot_label = f"{channel} | {stream['Type']} - {date}"
                    plot_tag = f"{tab_label}_{channel}_{stream['Type']}_{i}"
                else:
                    plot_label = f"{channel} | {date}"
                    plot_tag = f"{tab_label}_{channel}_{date}"
                
                with dpg.plot(label=plot_label, width=-1, height=-1, tag = plot_tag):
                    dpg.add_plot_legend()
                    x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                    y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

                    if mode and wt== 'Combined':
                        emin = -int(dpg.get_value(f"{tab_tag}_emin"))
                        emax = int(dpg.get_value(f"{tab_tag}_emax"))
                    else:
                        emin = 0
                        emax = len(y)/250

                    per_tag[tag] = [Sxx_log,plot_tag, plot_label, stream_events, (emin, emax)]
                        
                    dpg.add_heat_series(Sxx_log.flatten(), rows=Sxx_log.shape[0], cols=Sxx_log.shape[1],
                                            scale_min=global_min, scale_max=global_max, 
                                            parent=y_axis, format="", bounds_min=[emin,0], bounds_max=[emax,125])
                                            
                    
                    dpg.bind_colormap(plot_tag, dpg.mvPlotColormap_Jet)

                    if stream_events != None and wt == 'Individual':
                        mode = 'segment' #why??
                        for colorIdx, event in enumerate(stream_events):
                            # stamp = [event['Idx']/(len(times)*250)] #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                            stamp = [event['Idx']/250]
                            type = event['Type']
                            if stamp[0] <= Sxx_log.shape[1]:
                                dpg.add_plot_legend()
                                inf = dpg.add_inf_line_series(x=stamp,label=f'{type}',parent=y_axis)
                                color = change_inf_line_color(colorIdx)
                                dpg.bind_item_theme(inf, color)

        dpg.configure_item(item=f"{tab_label}_colormap_scale", min_scale=global_min, max_scale=global_max)

        def link(sender, app_data):
            dpg.configure_item(f"{tab_label}_subplots", link_all_x=app_data, link_all_y=app_data)
       
        def merge_spectrograms(sender,app_data,user_data):
            bands = getBandsByTab(tab_tag)
            if dpg.does_item_exist(f"{tab_label}_merged"): dpg.delete_item(f"{tab_label}_merged")

            with dpg.group(parent=tab_label, tag = f"{tab_label}_merged"): 

                alpha_theme = create_alpha_theme()
                
                dpg.add_text('Band Power over Time', parent=f"{tab_label}_merged")
                dpg.add_separator(parent=f"{tab_label}_merged")

                for _, value in per_tag.items():
                    sxx, plot_tag, plot_label, stream_events, time = value
                    header_tag = f"{plot_tag}_header"
                    if dpg.does_item_exist(header_tag): dpg.delete_item(header_tag, children_only=True)

                    with dpg.collapsing_header(tag=header_tag, parent=f"{tab_label}_merged", label=plot_label):

                        with dpg.plot(label=plot_label, width=-1):
                            dpg.add_plot_legend()
                            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Power (dB)")
                            
                            for b,v in bands.items():
                                mask = (frequencies >= v[0]) & (frequencies < v[1])
                                if np.any(mask):
                    
                                    power = np.flipud(sxx)[mask, :]
                                    std = np.std(sxx[mask, :], axis=0)
                                    min_std = power-std
                                    max_std = power+std

                                    emin, emax = time
                                    time_array = np.linspace(emin,emax,int(-emin+emax+1))
                                    dpg.add_shade_series(time_array,min_std,y2=max_std,label = f"{b} Std. Deviation", tag=f"{plot_tag}_{b}_std", parent=y_axis)
                                    dpg.bind_item_theme(f"{plot_tag}_{b}_std", alpha_theme)
                                    l = dpg.add_line_series(time_array,power,label = f"{b} Power", tag=f"{plot_tag}_{b}_mean", parent=y_axis)
                                    dpg.bind_item_theme(l, change_line_thickness(3))

                            if stream_events != None and wt == 'Individual':
                                for event in stream_events:
                                    # stamp = [event['Idx']/(len(times)*250)] #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                                    stamp = [event['Idx']/250]
                                    type = event['Type']
                                    if stamp[0] <= Sxx_log.shape[1]:
                                        dpg.add_plot_legend()
                                        dpg.add_inf_line_series(x=stamp,label=f'{type}',parent=y_axis)
                  
        def mean_spectrogram(sender,app_data,user_data):
            all_Sxx = user_data
            all_Sxx = [s[2] for s in all_Sxx] 
            shapes = [s.shape for s in all_Sxx]
            if not all(shape == shapes[0] for shape in shapes):
                e = "All spectrograms must have the same time length to compute the mean."
                dpg.add_text(e, parent=f"{tab_label}_plot_group")
                raise ValueError(e)

            # Compute the mean spectrogram (linear scale)
            mean_Sxx = np.mean(np.stack(all_Sxx), axis=0)

            # Convert to dB
            mean_Sxx_log = 10 * np.log10(mean_Sxx + 1e-10)
            mean_Sxx_log = np.flipud(mean_Sxx_log)
            
            title = "Mean Spectrogram"
            subplot_tag = f"{tab_label}_mean"

            with dpg.collapsing_header(label='Mean Spectrogram', parent=tab_label):
                with dpg.plot(label=title, width=500, height=400, tag=subplot_tag):
                    x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                    y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

                    if mode and wt== 'Combined':
                        emin = -int(dpg.get_value(f"{tab_tag}_emin"))
                        emax = int(dpg.get_value(f"{tab_tag}_emax"))
                    else:
                        emin = 0
                        emax = len(y)/250

                    dpg.add_heat_series(mean_Sxx_log.flatten(), rows=mean_Sxx_log.shape[0], cols=mean_Sxx_log.shape[1],
                                        scale_min=global_min, scale_max=global_max,
                                        parent=y_axis, format="", bounds_min=[emin,0], bounds_max=[emax,125])
                    dpg.bind_colormap(subplot_tag, dpg.mvPlotColormap_Jet)

        with dpg.group(horizontal=False):
            dpg.add_checkbox(label='Synchronize Axis', callback=link)      
            dpg.add_button(label='Band Power over Time', callback=merge_spectrograms)
            dpg.add_button(label='Mean Spectrogram', callback=mean_spectrogram, user_data=Merge)
       
def choose(sender,app_data,user_data):
    tags, tab_label, func, tab_tag, parameter_values, mode = user_data
    window_id = extract_window_id(tab_tag)
    wt = extract_type_window(window_id)
    continue_flag = True
    #Mode to get signal - if event or full signal
    # print(mode)
    if wt == 'Individual': mode = None
    elif mode == None: 
        # with dpg.child_window(parent=tab_label):
        #     dpg.add_text(f"{func} only available in Combined Analysis for Event-lock based signals", show= True)
        continue_flag = True

    if continue_flag == True:
        events = [getEventsbyTag(tab_tag,serie) for serie in tags]
        if all(e is None for e in events): mode = None 
        else: mode = 'segment'

        #Mode to plot: joined or separate
        plot_mode = app_data
        if plot_mode == 'Join Recordings': plot_mode = 'join'
        else: plot_mode = 'separate'

        #erase group if it already exists
        if dpg.does_item_exist(f"{tab_label}_plot_group"): dpg.delete_item(f"{tab_label}_plot_group")
        if dpg.does_item_exist(f"{tab_label}_merged"): dpg.delete_item(f"{tab_label}_merged")
        

        if plot_mode == 'join':
            #plot per recording + possibility of merge all
            if func == 'spectrogram': plot_spectrogram_joined(tags, tab_label, func, tab_tag, parameter_values, mode)
            else: plot_wavelet_joined(tags, tab_label, func, tab_tag, parameter_values, mode)
        else: 
            #plot per channel
            if func == 'spectrogram': plot_spectrogram_og(tags, tab_label, func, tab_tag, parameter_values, mode)
            else: plot_wavelet(tags, tab_label, func, tab_tag, parameter_values, mode)

def plot_wavelet_joined(tags, tab_label, func, tab_tag, parameter_values, mode = None):
    window_id = extract_window_id(tab_tag)
    wt = extract_type_window(window_id)

    new_signal, identifiers = {}, {}

    '''Initializing new signal dictionary'''
    for tag in tags:
        signal = getSignalbyIdx(window_id,tab_tag,tag)
        ch = signal['Channel']
        if ch in electrodes_names.keys():
            ch = electrodes_names[ch]
        else:
            electrodes_names[ch] = ch

        if func in signal.keys(): signal.pop(func)
        temp = {key: np.array([]) for key in signal.keys()}
        temp['dX'] = []
        if ch not in new_signal.keys(): new_signal[ch] = temp
        else: new_signal[ch] = new_signal[ch] | temp

    '''Filling new signal dictionary'''
    prev_end_time = {}
    current_start = {}
    for i,tag in enumerate(tags):
        signal = getSignalbyIdx(window_id,tab_tag,tag)

        '''Good version - For individual and combined?'''
        X = signal['X']

        arr = np.array(X)
        if np.issubdtype(arr.dtype, np.number):
            valid = arr[~np.isnan(arr)]
            if len(valid) > 0:# and np.round(valid[0]) == 0:
                # 'X' is in seconds
                signal['dX'] = [signal['Date'] + timedelta(seconds=val) for val in X]
        else:
            # 'X' is in Unix timestamp
            signal['dX'] = [datetime.fromtimestamp(val) for val in X]
        ch = signal['Channel']
        if ch in electrodes_names.keys():
            ch = electrodes_names[ch]
        else:
            electrodes_names[ch] = ch

        current_start[ch] = signal['dX'][0]
    
        # Insert zero gap if there's a time difference
        if ch in prev_end_time:
            gap = current_start[ch] - prev_end_time[ch]
            
            if gap.total_seconds() > 0:
                # Limit the gap to 10 min
                gap = min(gap, timedelta(seconds = 20))
                
                # Determine how many points to fill (based on sampling rate)
                sample_rate = 250
                n_fill = int(gap.total_seconds() * sample_rate)
                
                if n_fill > 0:
                    # Generate filler time and zero signal
                    filler_dX = [prev_end_time[ch] + timedelta(seconds=i / sample_rate) for i in range(n_fill)]
                    filler_Y = np.zeros(n_fill)
                    
                    # Append the filler
                    new_signal[ch]['dX'] = np.append(new_signal[ch]['dX'], filler_dX)
                    new_signal[ch]['Y'] = np.append(new_signal[ch]['Y'], filler_Y)
        else: prev_end_time[ch] = None

        for key in signal.keys():
            if key == 'dX' or key == 'Y':
                new_signal[ch][key] = np.append(new_signal[ch][key], np.array(signal[key]))
                identifiers[ch] = len(signal[key])
            else:
               new_signal[ch][key] = np.append(new_signal[ch][key], signal[key])

        prev_end_time[ch] = signal['dX'][-1]

    num_plots = len(new_signal.keys())
    num_cols = 1
    num_rows = num_plots
    global_min, global_max = 0,0   
    per_tag = {}
    bands = getBandsByTab(tab_tag)

    with dpg.group(horizontal=True, parent=f"{tab_label}", tag=f"{tab_label}_plot_group"):

        with dpg.subplots(rows=num_rows, columns=num_cols, label="Wavelet", width=800, height=400*num_rows, tag = f"{tab_label}_subplots"):

            for channel in new_signal:
                title =f"Joined Wavelet - {channel}"
                subplot_tag = f"{tab_label}_joined_{channel}"
                with dpg.plot(label=title, width=500, height=400, tag=subplot_tag, parent=f"{tab_label}_subplots"):
                    x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (DateTime)", scale= dpg.mvPlotScale_Time)
                    y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

                    y = new_signal[channel]['Y']

                    if current_start == {}:
                        x = new_signal[channel]['dX']
                        if isinstance(x[0], (int, float)): x = [datetime.fromtimestamp(val) for val in x]
                        x = [(xx + timedelta(hours=1)).timestamp() for xx in x]
                    else:
                        x = np.arange(0,len(y)/250,1)
                        dpg.configure_item(x_axis, scale = dpg.mvPlotScale_Linear)
                    
                    try: events = new_signal[channel]['Events']
                    except Exception as e: events = 'None'
                    signal = None
                    try:
                        signal = apply_feat(func,parameter_values,y)
                        updateSignalbyIdx(signal,tab_tag,tag,func)
                    except Exception as e: print(e)

                    tfr = 10 * np.log10(signal + 1e-8)

                    tfr = np.flipud(tfr[0, 0, :, :])
                    downsampled_tfr = tfr[:, ::5]
                    heatmap_data = downsampled_tfr.flatten().tolist()

                    per_tag[channel] = [downsampled_tfr,subplot_tag, title, events, x]

                    global_min = np.min(downsampled_tfr)
                    global_max = np.max(downsampled_tfr) 

                    dpg.add_heat_series(heatmap_data, rows=downsampled_tfr.shape[0], cols=downsampled_tfr.shape[1],
                                    scale_min=global_min, scale_max=global_max,
                                    parent=y_axis, format="",bounds_min=[x[0],0], bounds_max=[x[-1],100])
                    dpg.bind_colormap(subplot_tag, dpg.mvPlotColormap_Jet)  

                    if not isinstance(events,str):
                        for event in events:
                            if current_start == {}:
                                stamp = (event['Date'] + timedelta(hours=1) + timedelta(seconds=(event['Idx']/250))).timestamp() #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                            else: stamp = event['Idx']/250
                            if stamp <= x[-1]:
                                type = event['Type']
                                dpg.add_plot_legend()
                                dpg.add_inf_line_series(x=[stamp],label=f'{type}',parent=y_axis)

        dpg.add_colormap_scale(tag=f"{tab_label}_colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Jet,
                                            min_scale = global_min, max_scale=global_max, height=400*num_rows)
        
        def link(sender, app_data):
            dpg.configure_item(f"{tab_label}_subplots", link_all_x=app_data, link_all_y=app_data)

        def mean_wavelet(channels):
            # mean_Sxx = np.mean(np.stack(channels), axis=0)
            
            max_time = max(ch.shape[1] for ch in channels)
            num_freqs = channels[0].shape[0]

            for i,ch in enumerate(channels):
                pad_width = max_time - ch.shape[1]
                if pad_width > 0:
                    pad_array = np.full((num_freqs, pad_width), np.nan)
                    channels[i] = np.hstack([ch, pad_array])
                
            stacked = np.stack(channels, axis=0)  # shape: (channels, freqs, time)
            mean_Sxx = np.nanmean(stacked, axis=0)
            
            with dpg.plot(label='Mean Wavelet', width=-1, height=400, tag=f"{tab_label}_join_mean", parent=f"{tab_label}_merged"):
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

                if mode and wt=='Combined':
                    emin = -int(dpg.get_value(f"{tab_tag}_emin"))
                    emax = int(dpg.get_value(f"{tab_tag}_emax"))
                else:
                    emin, emax = 0, len(x)*5/250 #5 is downsampling factor, 250 is fs

                dpg.add_heat_series(mean_Sxx.flatten(), rows=mean_Sxx.shape[0], cols=mean_Sxx.shape[1],
                                    scale_min=global_min, scale_max=global_max,
                                    parent=y_axis, format="", bounds_min=[emin,0], bounds_max=[emax,num_freqs])
                dpg.bind_colormap(f"{tab_label}_join_mean", dpg.mvPlotColormap_Jet)

                if not isinstance(events,str):
                    for event in events:
                        stamp = event['Idx']/250 #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                        if stamp <= emax:
                            type = event['Type']
                            dpg.add_plot_legend()
                            dpg.add_inf_line_series(x=[stamp],label=f'{type}',parent=y_axis)

        def merge_wavelet():
            if dpg.does_item_exist(f"{tab_label}_merged"): dpg.delete_item(f"{tab_label}_merged")

            with dpg.group(parent=tab_label, tag = f"{tab_label}_merged"): 
          
                for _, value in per_tag.items():
                    sxx, plot_tag, plot_label, events, time = value   
                    header_tag = f"{plot_tag}_header"

                    if dpg.does_item_exist(header_tag): dpg.delete_item(header_tag, children_only=True)

                    with dpg.collapsing_header(tag=header_tag, parent=f"{tab_label}_merged", label=plot_label):

                        with dpg.plot(label= f"Bands Power over Time - {_}",width=-1):
                            dpg.add_plot_legend()
                            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Power (dB)")

                            alpha_theme = create_alpha_theme()

                            for b,v in bands.items():
                                frequencies = parameter_values['freqs']
                                mask = (frequencies >= v[0]) & (frequencies < v[1])
                                if np.any(mask):
                                    power = np.mean(sxx[mask, :],axis=0)  # mean across freqs -> shape: (time,)std = np.std(sxx[mask, :], axis=0)
                                    std = np.std(sxx[mask, :],axis=0)
                                    min_std = power-std
                                    max_std = power+std
                                    
                                    dpg.add_shade_series(time,min_std,y2=max_std,label = f"{b} Std. Deviation", tag=f"{plot_tag}_{b}_std", parent=y_axis)
                                    dpg.bind_item_theme(f"{plot_tag}_{b}_std", alpha_theme)
                                    dpg.add_line_series(time,power,label = f"{b} Mean", tag=f"{plot_tag}_{b}_mean", parent=y_axis)

                                    if not isinstance(events,str):
                                        for event in events:
                                            stamp = event['Idx']/250 #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                                            # type = event['Type'] #--> for label
                                            if stamp <= time[-1]: dpg.add_inf_line_series(x=[stamp],parent=y_axis)

        with dpg.group(horizontal=False):
            dpg.add_checkbox(label='Synchronize Axis', callback=link) 
            dpg.add_button(label='Band Power over Time', callback=merge_wavelet)

def plot_wavelet(tags, tab_label, func, tab_tag, parameter_values, mode = None):
    window_id = extract_window_id(tab_tag)
    wt = extract_type_window(window_id)
    num_plots = len(tags)
    num_cols = 2
    num_rows = (num_plots + 1) // num_cols
    events = None
    per_tag = {}
    bands = getBandsByTab(tab_tag)

    with dpg.group(horizontal=True,tag = f"{tab_label}_plot_group", parent=tab_label):
        with dpg.subplots(rows=num_rows, columns=num_cols, label=f"Wavelet", width=800, height=400*num_rows, tag=f"{tab_label}_subplots"):
            
            for tag in tags:
                stream = getSignalbyIdx(window_id,tab_tag,tag,mode=mode)

                if mode == None: #else the stream is the event
                    try:
                        events = getEventsbyTag(tab_tag, tag)
                    except Exception as e: events = 'None'
                
                y = stream['Y']
                channel = stream['Channel']
                
                date = stream['Date']
                signal = None
                try:
                    signal = apply_feat(func,parameter_values,y)
                except Exception as e: print(parameter_values['epoch_data'])

                if mode and wt=='Combined': #Plotting the events
                    date = date + timedelta(seconds=int(stream['Idx']/250))
                    plot_label = f"{channel} - {stream['Type']} - {date}"
                    plot_tag = f"{tab_label}_{channel}_{stream['Type']}"
                else:
                    plot_label = f"{channel} | {date}"
                    plot_tag = f"{tab_label}_{channel}_{date}"

                
                with dpg.plot(label = plot_label, width=-1, height=-1, tag =plot_tag):
                
                    x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                    y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

                    freqs = parameter_values['freqs']
                    tfr = signal

                    # tfr = (tfr * 100) / np.max(tfr)
                    tfr = 10 * np.log10(tfr)

                    tfr = np.flipud(tfr[0, 0, :, :])

                    if mode and wt== 'Combined':
                        emin = -int(dpg.get_value(f"{tab_tag}_emin"))
                        emax = int(dpg.get_value(f"{tab_tag}_emax"))
                    else:
                        emin = 0
                        emax = len(y)/250

                    downsampled_tfr = tfr[:, ::2]
                    per_tag[tag] = [downsampled_tfr,plot_tag, plot_label, events, (emin,emax)]
                    heatmap_data = downsampled_tfr.flatten().tolist()

                    global_min = np.min(downsampled_tfr)
                    global_max = np.max(downsampled_tfr)

                    # Add downsampled heatmap series
                    dpg.add_heat_series(heatmap_data, rows=downsampled_tfr.shape[0], cols=downsampled_tfr.shape[1], 
                                        parent=y_axis, scale_min=global_min, scale_max=global_max, format="", bounds_min=[emin,freqs[0]], bounds_max=[emax,freqs[-1]])

                    dpg.bind_colormap(plot_tag, dpg.mvPlotColormap_Jet)

                    if isinstance(events,list):
                        for event in events:
                            # stamp = (event['Date'] + timedelta(hours=1) + timedelta(seconds=(event['Idx']/250))).timestamp() #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                            stamp = [event['Idx']/250]
                            type = event['Type']
                            if stamp[0] <= downsampled_tfr.shape[1] and event['Channel'] == channel:
                                dpg.add_plot_legend()
                                dpg.add_inf_line_series(x=stamp,label=f'{type}',parent=y_axis)

        dpg.add_colormap_scale(tag=f"{tab_label}_colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Jet,
                            min_scale=global_min, max_scale=global_max, height=400*num_rows)

        def link(sender, app_data):
            dpg.configure_item(f"{tab_label}_subplots", link_all_x=app_data, link_all_y=app_data)
        
        def merge_wavelet():
            if dpg.does_item_exist(f"{tab_label}_merged"): dpg.delete_item(f"{tab_label}_merged")

            with dpg.group(parent=tab_label, tag = f"{tab_label}_merged"):
                for _, value in per_tag.items():
                    sxx, plot_tag, plot_label, events, time = value   
                    header_tag = f"{plot_tag}_header"

                    if dpg.does_item_exist(header_tag): dpg.delete_item(header_tag, children_only=True)

                    with dpg.collapsing_header(tag=header_tag, parent=f"{tab_label}_merged", label=plot_label):

                        with dpg.plot(label= f"Bands Power over Time - {_}",width=-1): 
                            dpg.add_plot_legend()
                            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Power (dB)")

                            alpha_theme = create_alpha_theme()

                            sxx = np.flipud(sxx)
                            for b,v in bands.items():
                                frequencies = parameter_values['freqs']
                                mask = (frequencies >= v[0]) & (frequencies < v[1])
                                if np.any(mask):
                                    power = np.mean(sxx[mask, :],axis=0)  # mean across freqs -> shape: (time,)std = np.std(sxx[mask, :], axis=0)
                                    std = np.std(sxx[mask, :],axis=0)
                                    min_std = power-std
                                    max_std = power+std
                                    
                                    emin, emax = time

                                    time_array = np.linspace(emin,emax,sxx.shape[1])
                                    dpg.add_shade_series(time_array,min_std,y2=max_std,label = f"{b} Std. Deviation", tag=f"{plot_tag}_{b}_std", parent=y_axis)
                                    dpg.bind_item_theme(f"{plot_tag}_{b}_std", alpha_theme)
                                    dpg.add_line_series(time_array,power,label = f"{b} Mean", tag=f"{plot_tag}_{b}_mean", parent=y_axis)

                                    if isinstance(events,list):
                                        for event in events:
                                            stamp = event['Idx']/250 #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                                            # type = event['Type'] #--> for label
                                            if stamp <= emax: dpg.add_inf_line_series(x=[stamp],parent=y_axis)

        with dpg.group(horizontal=False):
            dpg.add_checkbox(label='Synchronize Axis', callback=link) 
            dpg.add_button(label='Band Power over Time', callback=merge_wavelet)

def plot_pac(tags,tab_tag,parameter_values,mode=None):
    window_id = extract_window_id(tab_tag)
    labels = [dpg.get_item_label(tag) for tag in tags]
    bands = getBandsByTab(tab_tag)

    if mode: #if default
        tab_label = f"{tab_tag}_df_PAC"
    else: 
        tab_label = f"{tab_tag}_PAC"

    def plot():

        for b in ['s','b']:
            for s in  ['1','2']:
                label = dpg.get_value(f"{tab_label}_{b}{s}")
                if b == 's':
                    idx = labels.index(label)
                    signal = getSignalbyIdx(window_id,tab_tag,tags[idx])
                    parameter_values[f'{b}{s}'] = signal['Y']
                    if s == '1':
                        signal1 = signal
                    else: 
                        signal2 = signal
                else:
                    parameter_values[f'{b}{s}'] = bands[label]
                        

        #1st: Filter signals
        if len(parameter_values['s1']) != (parameter_values['s2']):
            t = dpg.add_text('Signals with different lengths!',parent=tab_label)
            dpg.bind_item_theme(t,change_text_color(1))
            return
        for s in ['1','2']:
            band = parameter_values[f'b{s}']
            param_filter = {'N': '4', 'Wn': band,'btype':'band','fs': '250'}
            args = pre.call_function('butter', param_filter) 
            filtered = pre.call_function2('filtfilt', *args, parameter_values[f's{s}'])
            param_hilbert = {'x': filtered}
            hilbert = pre.call_function('hilbert',param_hilbert)
            if s == '1': 
                phase_data = np.angle(hilbert)
            else: amp_data = np.abs(hilbert)

        #4th: create bins
        if 'n_bins' in parameter_values.keys(): 
            n_bins = parameter_values['n_bins']
            if n_bins =='' or n_bins==' ': n_bins = 18
            else: n_bins = int(n_bins)
        else: n_bins = 18 

        edges = np.linspace(-np.pi, np.pi, n_bins+1)
        centers = (edges[:-1] + edges[1:]) / 2
        digitized = np.digitize(phase_data, edges) - 1 #assign each time point to each bin (phase)

        amp_means = np.zeros(n_bins)
        for i in range(n_bins):
            sel = amp_data[digitized==i]
            amp_means[i] = np.mean(sel) if sel.size>0 else 0 #get the mean amp from the binned values

        # Normaliza
        amp_dist = amp_means / np.sum(amp_means + 1e-16)
        entropy = -np.sum(amp_dist * np.log(amp_dist + 1e-16)) #shannon entropy
        mi = (np.log(n_bins) - entropy) / np.log(n_bins) #modulation index

        if dpg.does_item_exist(f"{tab_label}_pac"): dpg.delete_item(f"{tab_label}_pac")

        with dpg.group(tag=f"{tab_label}_pac", parent=tab_label):
            dpg.add_text(f"Phase Signal: {signal1['Channel']} - {signal1['Date']} | Phase Band: {parameter_values['b1']}")
            dpg.add_text(f"Amplitude Signal: {signal2['Channel']} - {signal2['Date']} | Phase Band: {parameter_values['b2']}")
            dpg.add_text('Modulation Index (MI): 0 = NO coupling | 1 = STRONG coupling ')
            with dpg.plot(label=f"Phase-Amplitude Coupling - MI: {mi}", height=300, width=-1,tag=f"{tab_label}_plot"):
                dpg.add_plot_legend()
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Phase (rad)")
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Amplitude (microV)")
                phase = centers.tolist()
                amp = amp_means.tolist()
                # for p,a in zip(phase,amp):
                #     dpg.add_bar_series([p], [a], parent=y_axis)
                dpg.add_bar_series(phase,amp,parent=y_axis)
                # dpg.bind_colormap(f"{tab_label}_plot", dpg.mvPlotColormap_Jet)

        peak_a = max(amp)
        peak_p = phase[amp.index(peak_a)]
        bandwidth = 360/n_bins
        peak_d = peak_p*180/np.pi
        peak_d = [np.round(peak_d-bandwidth/2,2),np.round(peak_d+bandwidth/2,2)]
        info = {'Modulation of Index': str(mi), 'Peak Phase (Rad)':peak_p, 'Peak Band (Degrees)': peak_d ,'Peak Amplitude': peak_a}
        if not dpg.does_item_exist(f"{tab_label}_header"): dpg.add_collapsing_header(label='Metrics', parent=tab_label, tag=f"{tab_label}_header")
        create_table(f"{tab_label}_header",f"{tab_label}_table",info,trial_label=f"{signal1['Channel']} - {signal2['Channel']}")

    if mode:
        combos = {}
        with dpg.group(horizontal=True,parent=tab_label):
            for i,s in enumerate(['Signal 1','Signal 2']):
                input_id = dpg.add_combo(
                        label=s,
                        items=labels,  # <-- customize your options
                        default_value='---',
                        # callback=different_combo,
                        # user_data=(tab_label, combos),
                        tag = f"{tab_label}_s{i+1}",
                        width=200
                    )
                combos[s] = input_id
        
        with dpg.group(horizontal=True,parent=tab_label):

            bands_labels = list(getBandsByTab(tab_tag).keys())
            for i,s in enumerate(['Band 1','Band 2']):
                input_id = dpg.add_combo(
                        label=s,
                        items=bands_labels,  # <-- customize your options
                        default_value='---',
                        callback=different_combo,
                        user_data=(tab_label, combos),
                        tag = f"{tab_label}_b{i+1}",
                        width=200
                    )
                combos[s] = input_id

        dpg.add_button(label='Plot Phase-Amplitude Coupling', callback=plot,width=-1, parent=tab_label)
    else: plot()

def convert_to_db(value):
    """Convert a value to dB scale using 10 * log10."""
     # if isinstance(value, (list, np.ndarray)):
     #     return [round(10 * np.log10(v +1e-6), 2) for v in value]
    if isinstance(value, (list, np.ndarray,tuple)):  # Handle peak values (power, frequency)
        return (round(10 * np.log10(value[0]+1e-6), 2), value[1])
    elif isinstance(value, (int, float)):
        return round(10 * np.log10(value+1e-6), 2)
    return value  # Return unchanged if it's a string or invalid type
 
def convert_from_db(value):
 
    """Convert a dB value back to linear scale using 10^(dB/10)."""
     # if isinstance(value, (list, np.ndarray,tuple)):  
     #     return [round(10**(v / 10), 2) if v != float('-inf') else 0 for v in value]
 
    if isinstance(value, (list, np.ndarray,tuple)):  # Handle peak values (power, frequency)
        return (round(10**(value[0] / 10), 2) if value[0] != float('-inf') else 0, value[1])
    elif isinstance(value, (int, float)):
        return round(10**(value / 10), 2) if value != float('-inf') else 0
    return value  # Return unchanged if it's a string or invalid type
 
def update_table(table_tag, type):
    """Update the table by replacing values with their dB equivalents."""

    if not dpg.does_item_exist(table_tag):
        print(f"Table {table_tag} does not exist!")
        return
 
    children = dpg.get_item_children(table_tag, slot=1)  # Get table rows
 
    if not children:
        print(f"No rows found in {table_tag}.")
 
        return
    
    for row_id in children:  # Iterate through rows
        row_children = dpg.get_item_children(row_id, slot=1)  # Get row items
 
        for i in range(1, len(row_children)):  # Skip first column (Trial)

            value = eval(dpg.get_value(row_children[i]))
            if type == 'dB':
                db_value = convert_to_db(value)
            else: db_value = convert_from_db(value)
          
            if isinstance(db_value, list):  # List case
                dpg.set_value(row_children[i], str(db_value))

            elif isinstance(db_value, tuple):  # Peak case (power, frequency)
                dpg.set_value(row_children[i], f"({db_value[0]}, {value[1]})")
 
            else:  # Single number case
                dpg.set_value(row_children[i], f"{db_value:.2f}")

def before_vs_after(sender,app_data,user_data):
    signal_tags,tab_label,func,tab_tag,parameter_values = user_data
    plot_filtered_signal(signal_tags,tab_label,func,tab_tag,parameter_values)

#------------GUI PRETTY-----------------
def create_alpha_theme(alpha=0.5):
    """
    Create and return a DearPyGui plot alpha theme.
    
    Parameters:
        alpha (float): Opacity value between 0.0 and 1.0
    
    Returns:
        int: The theme ID
    """
    with dpg.theme() as alpha_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvPlotStyleVar_FillAlpha, alpha, category=dpg.mvThemeCat_Plots)
    return alpha_theme

def switch_theme(sender, app_data, user_data):
    dpg.bind_theme(user_data)

def change_electrodes_names(sender, app_data, user_data):
    input_counter = [0]  # Use a list to allow mutable reference


    def handle_submit(sender, app_data, user_data):
        for i in range(user_data[0]):
            old_name = dpg.get_value(f"old_name_{i}")
            new_name = dpg.get_value(f"new_name_{i}")
            if new_name == '': new_name = old_name

            for side in ['LEFT','RIGHT']:
                electrodes_names[f'{old_name}_{side}'] = f'{new_name}_{side}'
        
    def reset(sender, app_data, user_data):
        electrodes_names.clear()

    if dpg.does_item_exist("Change Channel Names Window"):
        dpg.delete_item("Change Channel Names Window")

    with dpg.window(tag="Change Channel Names Window", width=400, height=300):
        dpg.add_text("Change Channel Names")
        dpg.add_spacing(count=2)
        channels = ['ONE_THREE','ZERO_THREE','ZERO_TWO']
        for row_id, ch in enumerate(channels):
            input_counter[0]+=1
            with dpg.group(tag=f"input_group_{row_id}", parent="input_container", horizontal=True):
                dpg.add_input_text(tag=f"old_name_{row_id}",default_value=ch, width=120)
                dpg.add_input_text(tag=f"new_name_{row_id}", label="New Name", width=120)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Submit", callback=handle_submit, user_data=input_counter)
            dpg.add_button(label="Reset", callback=reset)

        # dpg.configure_item("Change Channel Names Window",on_close=dpg.configure_item("Change Channel Names Window",show=False))

def change_inf_line_color(color_id):
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvInfLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, colors[color_id], category=dpg.mvThemeCat_Plots)
    return theme_id

def change_line_color(color_id):
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, colors[color_id], category=dpg.mvThemeCat_Plots)
    return theme_id

def change_line_thickness(thickness, component = dpg.mvLineSeries):
    with dpg.theme() as theme_id:
        with dpg.theme_component(component):
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, thickness, category=dpg.mvThemeCat_Plots)
    return theme_id

def change_text_color(color_id):
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvText):
            dpg.add_theme_color(dpg.mvThemeCol_Text, colors[color_id], category=dpg.mvThemeCat_Core)
    return theme_id

def different_combo(sender,app_data,user_data):

    if dpg.does_item_exist(f"{sender}_pac_w"):dpg.delete_item(f"{sender}_pac_w")
    doc_container, combos = user_data
    atual = dpg.get_value(sender)
    for key in combos.keys():
        if sender != combos[key]:
            other = dpg.get_value(combos[key])
    if atual == other:
        dpg.add_separator(parent=doc_container)
        dpg.add_text('Recordings cannot be the same!', parent=doc_container, show=True, tag = f"{sender}_pac_w")
        return
         

#--- Extract signal/identifiers
def extract_idx_from_series_tag(series_tag: str) -> int:
    match = re.search(r'_series_(\d+)(?:_|$)', series_tag)  # Match _series_<number> with or without trailing underscore
    if match:
        return int(match.group(1))  # Extract and return the idx as an integer
    else:
        raise ValueError(f"Invalid series_tag format: {series_tag}")
    
def extract_side_from_series_tag(series_tag: str) -> int:
    match = re.search(r'_(left|right)$', series_tag.lower())  # Match 'left' or 'right' at the end
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid series_tag format or missing side")
    
def extract_file_from_series_tag(series_tag: str):
    """Extracts the 'file' value from a formatted filename string."""
    match = re.search(r'_file_(\d+)_series_', series_tag)  # Ensure only digits
    return int(match.group(1)) if match else None  # Return integer or None

def extract_edx_from_series_tag(series_tag: str) -> str:
    """
    Extracts last group of string bla_bla_bla_group
    """
    if series_tag.split('_')[-1] in ['left','right']:
        return series_tag.split('_')[-2]
    return series_tag.split('_')[-1]

def extract_event_from_series_tag(event_string):
    parts = event_string.split('_')
    
    # Skip the first three (e.g., tab, Streaming, 0), then look for the next non-number
    for i in range(3, len(parts), 2):  # step by 2 to skip the numbers
        if not parts[i].isdigit():
            return parts[i]
    return None

def extract_channel_from_series_tag(series_tag: str) -> str:
    match = re.search(r'^(.*?)(?=_(left|right))', series_tag.lower())  # Look for '_left' or '_right' without including them
    
    if match:
        return match.group(1)  # Return the part before '_left' or '_right'
    else:
        return series_tag

def extract_window_id(tab_tag: str) -> int:
    """
    Extracts window_id as an integer from a tab_tag formatted as 'tab_{mode}_{window_id}' 
    or 'tab_{mode}_{window_id}_{suffix}'.
    """
    match = re.match(r"tab_[^_]+_(\d+)(?:_.+)?$", tab_tag)  # Capture window_id, ignore optional suffix
    if match:
        return int(match.group(1))  # Convert extracted value to an integer
    else:
        raise ValueError(f"Invalid tab_tag format: {tab_tag}")

def extract_type_window(window_id):
    if 'Data' in app_state['windows'][window_id].keys():
        return 'Individual'
    else: return 'Combined'

def extract_mode(tab_tag: str) -> str:
    """
    Extracts the mode from a tab_tag formatted as 'tab_{mode}_{window_id}' 
    or 'tab_{mode}_{window_id}_{suffix}'.
    """
    match = re.match(r"tab_([^_]+)_\d+(?:_.+)?$", tab_tag)  # Capture mode, ignore optional suffix
    if match:
        return match.group(1)  # Return the extracted mode
    else:
        raise ValueError(f"Invalid tab_tag format: {tab_tag}")

def extract_channel_hemisphere(label):
    """
    Parses a label like 'ZERO_THREE_LEFT' into channel and hemisphere.
    
    Returns:
        channel (str): The channel with underscores (e.g. 'zero_three')
        hemisphere (str): The hemisphere (e.g. 'left')
    """
    parts = label.split('_')
    
    if len(parts) < 2:
        raise ValueError("Label format is invalid. Expected format: CHANNEL_HEMISPHERE")

    hemisphere = parts[-1]
    channel = '_'.join(parts[:-1])
    
    return channel, hemisphere

def getActiveSeries(signal_tags):
    active_tags = []

    if type(signal_tags) == dict:
        tags = signal_tags.keys()
    elif type(signal_tags) == list:

        tags = signal_tags.copy()

    for tag in tags:
        info = dpg.get_item_configuration(tag)
        if info['show'] == True: 
            active_tags.append(tag)
    keywords = ['series', 'file', 'OFF', 'ON']
    active_tags = [tag for tag in active_tags if extract_event_from_series_tag(tag) in keywords]

    return active_tags

def getInactiveSeries(signal_tags):
    active_tags = []

    for tag, visible in signal_tags.items():
        info = dpg.get_item_configuration(tag)
        if info['show'] == False: 
            active_tags.append(tag)
    return active_tags

def getActiveSignals(tab_tag,signal_tags):
    window_id = extract_window_id(tab_tag)
    active_series = getActiveSeries(signal_tags)
    signals = []
    for serie in active_series:
        try:
            signal = getSignalbyIdx(window_id, tab_tag, serie)
            if signal is None:  # If `getSignalbyIdx` returns None
                signal = getSignalbyIdxSide(window_id, tab_tag, serie)
        except KeyError:  # Catch missing key issues
            signal = getSignalbyIdxSide(window_id, tab_tag, serie)
        except Exception as e:  # Catch any other unexpected error
            print(f"Unexpected error for {tab_tag}, {serie}: {e}")
            signal = None  # Handle gracefully

        signals.append(signal)

    return signals

def getSignalbyIdx(window_id,tab_tag,series_tag,mode=None):
    idx = extract_idx_from_series_tag(series_tag)
    file = extract_file_from_series_tag(series_tag)
    edx = int(extract_edx_from_series_tag(series_tag))
    wt = extract_type_window(window_id)
    if wt == 'Combined': #Combined window
        if mode == None: #signal and not events
            return app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Signals'][idx]
        else: #events
            return app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Events'][edx]
    else: #Individual - always signal
        return app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]

def getCleanTimelinebyIdx(window_id,tab_tag,series_tag,mode=None):
    wt = extract_type_window(window_id)
    idx = extract_idx_from_series_tag(series_tag)
    file = extract_file_from_series_tag(series_tag)
    edx = int(extract_edx_from_series_tag(series_tag))
    if wt == 'Combined':
        if mode == None: #signal and not events
            return app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Clean'][idx]
        else: #events
            return app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['CleanEvents'][edx]
    else: return app_state['windows'][window_id]['Data'][tab_tag]['Clean'][idx]

def getSignalbyIdxSide(window_id,tab_tag,series_tag):
    idx = extract_idx_from_series_tag(series_tag)
    side = extract_side_from_series_tag(series_tag)
    wt = extract_type_window(window_id)
    file = extract_file_from_series_tag(series_tag)
    if wt == 'Individual': return app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side][idx]
    else: return app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Signals'][idx][side]

def getEventsbyIdx(tab_tag,idx):
    window_id = extract_window_id(tab_tag)
    dictionary = {}
    if extract_type_window(window_id) == 'Combined':
        dictionary = app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]
    
    if 'Events' in dictionary.keys():
        return dictionary['Events']
    else: return None

def getEventsbyTag(tab_tag,series_tag):
    window_id = extract_window_id(tab_tag)
    idx = extract_idx_from_series_tag(series_tag)
    file = extract_file_from_series_tag(series_tag)
    if extract_type_window(window_id) == 'Combined':
        dictionary= app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]
    else:
        dictionary = app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]
    if 'Events' in dictionary.keys():
        return dictionary['Events']
    else: return None

def getBandsByTab(tab_tag):
    window_id = extract_window_id(tab_tag)
    return app_state['windows'][window_id]['Bands']

def getDatabyTag(series_tag):
    window_id = extract_window_id(series_tag)
    wt = extract_type_window(window_id)
    if wt == 'Combined':
        file = extract_file_from_series_tag(series_tag)
        return app_state['windows'][window_id]['Files'][file]['Data']
    else:
        return app_state['windows'][window_id]['Data']

def getDatabyFile(window_id, file):
    wt = extract_type_window(window_id)
    if wt == 'Combined':
        return app_state['windows'][window_id]['Files'][file]['Data']
    else:
        return app_state['windows'][window_id]['Data']

def updateKeySignalbyIdx(value,tab_tag,series_tag, key):
    window_id = extract_window_id(tab_tag)
    idx = extract_idx_from_series_tag(series_tag)
    file = extract_file_from_series_tag(series_tag)
    if file == None:
        app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx][key] = value
    else: app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Signals'][idx][key] = value

def updateSignalbyIdx(value,tab_tag,series_tag, func = None, mode = None, new_tab_tag = None):
    window_id = extract_window_id(tab_tag)
    idx = extract_idx_from_series_tag(series_tag)
    file = extract_file_from_series_tag(series_tag)
    edx = int(extract_edx_from_series_tag(series_tag))
    wt = extract_type_window(window_id)
    if new_tab_tag: tab_tag=new_tab_tag

    if mode == None:
        if file == None:
            if func != None:
                app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx][func] = value
            else: app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]['Y'] = value
        else:
            if func != None: app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Signals'][idx][func] = value
            else: app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Signals'][idx]['Y'] = value
    else: 
        if wt == 'Combined':
            if func != None: app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Events'][edx][func] = value
            else: 
                app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Events'][edx]['Y'] = value
        else:
            if func != None: app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]['Events'][edx][func] = value
            else: app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]['Events'][edx]['Y'] = value

def enforce_min_max(sender, app_data, user_data):
    """Ensure max is always at least 10 units greater than min, and min is never below 0."""
    min_tag, max_tag, diff = user_data  # Extract tag references
    
    min_value = max(0, dpg.get_value(min_tag))  # Ensure min is at least 0
    max_value = absolute_max = dpg.get_value(max_tag)
    
    if sender == min_tag:
        if min_value >= max_value - diff:  # If min is too close to max
            max_value = min_value + diff
            dpg.set_value(max_tag, max_value)  # Ensure max stays 10+ units above
        dpg.set_value(min_tag, min_value)  # Set min (ensuring it's 0 or higher)

    elif sender == max_tag:
        if max_value < diff:  # Prevent max from being below 10
            min_value = 0
            max_value = diff
        elif max_value <= min_value + diff:  # Ensure min stays 10 below max
            min_value = max_value - diff
        elif max_value > absolute_max:
            max_value = absolute_max    

        dpg.set_value(min_tag, min_value)
        dpg.set_value(max_tag, max_value)

def extract_psd_features(p, band):
    b,v = band
    band = {b: v}
    full_power = np.sum(p['Y'])
    freqs, psd = p['X'], p['Y']

    #mean power per band
    pc = ft.mean_power_all_bands(p, band)
    std = ft.std_dev_streams(p, band)
    mean = {'Mean Power (mean, std. dev)': [np.round(pc[b],2), np.round(std[b],2)]}

    #normalized mean power
    norm_mean = {'% Mean Power (mean, std. dev)': [np.round(pc[b]*100/full_power,2), np.round(std[b],2)]}

    if isinstance(freqs, list): 
        freqs = np.array(freqs)
        psd = np.array(psd)
    mask = (freqs >= v[0]) & (freqs <= v[1])
    auc = {'Sum Power (AUC)': np.round(np.sum(psd[mask]),2)}

    #normalized auc
    norm_auc = {'% Sum Power (AUC)': f"{np.round(np.sum(psd[mask])/full_power*100,2)}"}

    #peak power
    peak = ft.peak_per_band(p, band)
    picos = {'Peak Power (power, frequency)': p for p in peak.values()}


    info = mean | norm_mean| auc | norm_auc| picos

    return info

def extract_timeline_features(p, full_power=None, coherence=False):
    
    if full_power is None:
        full_power = np.sum(p['Y'])
    else: full_power = np.sum(full_power)

    freqs, psd = p['X'], p['Y']

    if isinstance(psd, np.ndarray):
        psd = psd.tolist()
    elif psd is None:
        return
    #mean power per band
    pc = np.mean(psd)
    std = np.std(psd)
    mean = {'Mean Power (mean, std. dev)': [np.round(pc,2), np.round(std,2)]}

    #normalized mean power
    if full_power is not None:
        sump = np.sum(psd)
        norm_mean = {'% Mean Power (mean, std. dev)': [np.round(sump*100/full_power,2), np.round(std * 100 / full_power,2)]}
 
    #peak power
    peak = max(psd)
    picos = {'Peak Power': peak}

    #peak time
    time = psd.index(peak)
    # print(time, ' ', len(freqs))
    
    try:
        time = freqs[time]
    except Exception: time = freqs[0]

    key = 'Peak Time'
    if isinstance(time,str):
        peak = str(utl.parse_datetime(time).time())
    if isinstance(time, (int, float)):
        if np.isnan(time):
            return
    if isinstance(time, np.ndarray):
        if np.any(np.isnan(time)):
            return
    elif isinstance(time,float):
        peak = time
        peak = str(datetime.fromtimestamp(time).time())
    if coherence:
        key = 'Peak Frequency'
        peak = time

    time = {key: peak}

    info = mean | norm_mean| picos | time

    return info

def extract_cc_features(p, y_axis, tab_label ,mode = None):

    tags = []
    max_value = max(p['Y'])
    idx = p['Y'].index(max_value)
    lag = p['X'][idx]
    half = np.round(max_value/2,2)
    temp = [np.round(y,2) for y in p['Y']]
    start, inf, hlf = None, None, None
    # start = list(reversed(temp[:idx])).index(half) 
    # start = p['X'][idx-start]
    # end = temp[idx:].index(half) + idx
    # end = p['X'][end]

    Y, X = p['Y'], p['X']

    # hilbert = pre.call_function('hilbert',{'x': np.array(p['Y'])})
    # envelope = np.abs(hilbert)
    

    for i in range(idx, 0, -1):
        if Y[i] >= half and Y[i-1] < half:
            # Linear interpolation to find exact crossing point
            x1, x2 = X[i-1], X[i]
            y1, y2 = Y[i-1], Y[i]
            start = x1 + (half - y1) * (x2 - x1) / (y2 - y1)
            break

    # 3. Search to the right of the peak for first crossing below half max
    for i in range(idx, len(Y)-1):
        if Y[i] >= half and Y[i+1] < half:
            x1, x2 = X[i], X[i+1]
            y1, y2 = Y[i], Y[i+1]
            end = x1 + (half - y1) * (x2 - x1) / (y2 - y1)
            break
    
    if mode:
        ext = mode
    else: ext = ''

    if start: inf = dpg.add_inf_line_series([start,end],parent=y_axis, label = ext + ' Half Max Width', tag = f"{tab_label}_{ext}_HMW")
    if half: hlf = dpg.add_inf_line_series([half],parent=y_axis,horizontal=True,label= ext +' Half Max', tag = f"{tab_label}_{ext}_HW")
    # dpg.add_line_series(p['X'], envelope.tolist(),label=f"{ext} Envelope", parent=y_axis,tag=f"{tab_label}_{ext}_env")


    tags.append(f"{tab_label}_{ext}_HMW")
    tags.append(f"{tab_label}_{ext}_HW")
    tags.append(f"{tab_label}_{ext}_peaks")

    red = change_inf_line_color(0)
    green = change_inf_line_color(1)
    if inf: dpg.bind_item_theme(inf,red)
    if hlf: dpg.bind_item_theme(hlf,green)
    

    if start: width = np.round((end-start)/250,2)
    else: width = 0
    parameters, _ = fill_params_features('find_peaks')
    parameters['x'] = p['Y']
    parameters['distance'] = 120
    peaks = pre.call_function('find_peaks',parameters)
    true_peaks = [(x+0.5-len(p['Y'])/2)/250 for x in peaks[0]]
    above_peaks = [p['Y'][x] for x in peaks[0]]

    rms = np.sqrt(np.mean(np.array(p['Y'])**2))
    mask = np.array(above_peaks) >= 3*rms
    true_peaks = np.array(true_peaks)[mask]
    
    dpg.add_scatter_series(true_peaks.tolist() ,np.ones(len(peaks[0])).tolist(),parent=y_axis,label = ext +' Peaks', tag = f"{tab_label}_{ext}_peaks")
    diff = np.diff(true_peaks)
    if diff.size == 0: diff = [1]
    freq_mean = np.round(1/np.mean(diff),2)
    freq_std = np.std(diff)
    info = {
        'RMS Correlation': rms,
        'Max Correlation': max_value,
        'Lag til Max (s)': lag,
        'Half Max Width (s)': width,
        'Peak Frequency (mean, std)': [freq_mean,freq_std]
    }
    

    return info, tags

def extract_artifact_type(s: str):
    if s == "ARTIFACT_NOT_PRESENT":
        return 'Not'
    if s.endswith("_ARTIFACT_PRESENT"):
        return s.replace("_ARTIFACT_PRESENT", "")
    return None  # fallback for unexpected format

#--- Process with signal

def Volt2dB2(sender,app_data,user_data):
    type = app_data
    if type == True:
        type = 'dB'
        label = type
    else: 
        type = 'Y'
        label = 'µV^2/Hz'

    signal_tags, tab_tag, func, tab_label, tables = user_data

    if tab_label == "":
        identifier = tab_tag
    else:
        identifier = tab_label

    series = getActiveSeries(signal_tags)
    window_id = extract_window_id(tab_tag)
    mode = extract_mode(tab_tag)

    if mode != 'Events': 
        events = [getEventsbyTag(tab_tag,serie) for serie in series]
        if all(e is None for e in events):events = None
    else: events = None

    plot_mode = None
    events_flag = False

    if dpg.does_item_exist(f"{tab_label}_bva"): status = dpg.get_value(f"{tab_label}_bva")
    else: status = 'None'

    for serie in series:
        if mode == 'Events':
            signal = getSignalbyIdxSide(window_id,tab_tag,serie)
            if app_data: 
                norm = pre.log_normalization_db(signal)
                signal[type] = norm
                dpg.set_value(serie, [signal['X'], norm])
            else:
                dpg.set_value(serie, [signal['X'], signal['Y']])
        else:
            if events: 
                plot_mode = 'segment'
                events_flag = True
            signal = getSignalbyIdx(window_id,tab_tag,serie, mode=plot_mode)[func]
            series_label = dpg.get_item_label(serie)
            if app_data: 
                norm = pre.log_normalization_db(signal)
                signal[type] = norm
            
                dpg.set_value(f"{tab_label}_{series_label}_{func}", [signal['X'], norm])
            # else:
            #     dpg.set_value(f"{tab_label}_{series_label}_{func}", [signal['X'], signal['Y']])


    if extract_type_window(window_id) == 'Combined' and status == True: #For before and after events
        children = dpg.get_item_children(f"{tab_label}_y_axis")
        for _,child in children.items():
            for kid in child:
                current = dpg.get_value(kid)
                if app_data: 
                    new_y = [convert_to_db(v) for v in current[1]]
                else:
                    new_y = [convert_from_db(v) for v in current[1]]
                dpg.set_value(kid, [current[0], new_y])
    # else:
    mean_tag = std_tag = ''
    if dpg.does_item_exist(f"{tab_tag}_mean"):
        mean_tag = f"{tab_tag}_mean"
        std_tag = f"{tab_tag}_std"
    elif dpg.does_item_exist(f"{tab_label}_mean"):
        mean_tag = f"{tab_label}_mean"
        std_tag = f"{tab_label}_std"

    if mean_tag != '':
        if type == 'Y': key = None
        else: key = type
        mean_power, std_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)

        if type=='dB':
            mean_power = pre.V2dB(mean_power)
            
        minus, plus = mean_power-std_power, mean_power+ std_power
        dpg.configure_item(std_tag, y1=minus,y2=plus)
        current = dpg.get_value(mean_tag)
        dpg.set_value(mean_tag, [current[0], mean_power])

    else:
        if dpg.does_item_exist(f"{identifier}_y_axis"):
            dpg.configure_item(f"{identifier}_y_axis", label = f"LFP Power ({label})")
            update_plot_feature(tab_tag,tab_label,signal_tags,func, identifier, type, events = events_flag, mode = plot_mode)

    time.sleep(0.1)
    for table in tables:
        update_table(table,type)

def Volt2dB(sender,app_data,user_data):
    type = app_data
    if type == True:
        type = 'dB'
        label = type
    else: 
        type = 'Y'
        label = 'µV^2/Hz'
    
    y_axis, plot_tag, signal_tags, tables = user_data
    
    dpg.set_item_label(y_axis,label=label)

    all_values = []
    for tag in signal_tags:
        if dpg.get_item_configuration(tag)['show']==True:
            _,y = dpg.get_value(tag)[:2]
            if type == 'dB':
                y = pre.V2dB(y)
                dpg.configure_item(tag,y=y)
            else:
                y = pre.dB2V(y)
                dpg.configure_item(tag,y=y)
            all_values.append(y)

    mean = np.nanmean(all_values,axis=0)
    std = np.nanstd(all_values,axis=0)
    minus, plus = mean-std, mean+std
    dpg.configure_item(f"{plot_tag}_std", y1=minus,y2=plus)
    dpg.bind_item_theme(f"{plot_tag}_std",create_alpha_theme())
    dpg.configure_item(f"{plot_tag}_mean", y=mean)
    dpg.bind_item_theme(f"{plot_tag}_mean", change_line_thickness(5))

    time.sleep(0.1)
    for table in tables:
        update_table(table,type)



    


def getMeanActiveSeries(window_id,tab_tag,signal_tags, key = None):
    active_tags = getActiveSeries(signal_tags)
    active_signals = []
    mode = extract_mode(tab_tag)
    for tag in active_tags:
        if mode =='Events':
            active = getSignalbyIdxSide(window_id,tab_tag,tag)
        else:
            active = getSignalbyIdx(window_id,tab_tag,tag)

        active_signals.append(active)

    mean_power = pre.MeanSignal(active_signals, key)
    std_power = pre.StdDevSignal(active_signals,key)
    #mean_power = [m*100/np.sum(mean_power) for m in mean_power]
    return mean_power, std_power

def segment_signal(tab_tag, signal_tags):
    with dpg.group(tag = f"{tab_tag}_segmentation"):
        time.sleep(0.1)
        dpg.add_spacer(height=10)
        dpg.add_text('SEGMENTATION: minimum of 10s')
        dpg.add_checkbox(label='Use only visible signals:', default_value=True,show=True, tag=f"{tab_tag}_flag_signals")
        mmax = int(dpg.get_axis_limits(axis=f"x_axis_{tab_tag}")[1])
        with dpg.group(horizontal=True):
            dpg.add_input_int(label='Start', tag=f"{tab_tag}_min", width=90, default_value=0, callback=enforce_min_max, user_data=(f"{tab_tag}_min", f"{tab_tag}_max", 10))
            dpg.add_input_int(label='End', tag=f"{tab_tag}_max", width=90, default_value=mmax, callback=enforce_min_max, user_data=(f"{tab_tag}_min", f"{tab_tag}_max", 10))
            dpg.add_button(label='Segment Signal', show=True, callback=cut_signals,user_data=(tab_tag, signal_tags))

def cut_signals(sender,app_data,user_data):   
    tab_tag, signal_tags = user_data
    window_id = extract_window_id(tab_tag)
    active_series = getActiveSeries(signal_tags)
    flag = dpg.get_value(item=f"{tab_tag}_flag_signals")
    min_value = dpg.get_value(f"{tab_tag}_min")
    max_value = dpg.get_value(f"{tab_tag}_max")

    min_idx = min_value*250
    max_idx = max_value*250

    if flag == False: #Activate all signals if unchecked
        dpg.set_value(f"{tab_tag}_all", True)  # Set the checkbox state
        callback = dpg.get_item_callback(f"{tab_tag}_all")
        if callback:
            callback(f"{tab_tag}_all", True)  

    dpg.set_axis_limits(axis=f"x_axis_{tab_tag}", ymin=min_value, ymax=max_value)

    for serie in active_series:
        signal = getSignalbyIdx(window_id,tab_tag,serie)
        new_x = signal['X'][min_idx:max_idx]
        new_y = signal['Y'][min_idx:max_idx]
        updateKeySignalbyIdx(new_x,tab_tag,serie,'X')
        updateKeySignalbyIdx(new_y,tab_tag,serie,'Y')

        
    time.sleep(0.1)
    update_plot_td(tab_tag,signal_tags,' Segment')

def interval_events(tab_tag, signal_tags):
    min_dif = 2
    with dpg.group(horizontal=True):
        dpg.add_input_int(label='T Before (s)', tag=f"{tab_tag}_emin", width=90, default_value=15, callback=enforce_min_max, user_data=(f"{tab_tag}_emin", f"{tab_tag}_emax", min_dif))
        dpg.add_input_int(label='T After (s)', tag=f"{tab_tag}_emax", width=90, default_value=15, callback=enforce_min_max, user_data=(f"{tab_tag}_emin", f"{tab_tag}_emax", min_dif))

def DefaultFilter(sender,app_data,user_data):
    '''
    Standard filtration = 5th order Butterworth bandpass filter 1-100 Hz + Removal of cardiac component 
    Remove cardiac component - Fixed peak finder method - BRAVO adapted
    '''
    tab_tag, signal_tags = user_data

    active_series = getActiveSeries(signal_tags)
    
    window_id = extract_window_id(tab_tag)
    signal_mode, plot_mode = None, None
    wt = extract_type_window(window_id)
    if wt == 'Combined':
        config = dpg.get_item_configuration(f"x_axis_{tab_tag}")
        for j in app_state['windows'][window_id]['Files']:
            if isinstance(j['Data'][tab_tag], dict) and 'Events' in j['Data'][tab_tag].keys():
                signal_mode = plot_mode = 'segment'
                if config['scale'] == 1: #if were plotting in datetime (signal w marked events) and not seconds (cutted events)
                    signal_mode = plot_mode = None
                break
       
    else: 
        signals = app_state['windows'][window_id]['Data'][tab_tag]['Signals']
        for i,_ in enumerate(signals):
            events = getEventsbyIdx(tab_tag,i)
            if events != None: plot_mode = 'segment'
    
    band = dpg.get_value(item=f"{tab_tag}_default_wn")[:2]

    # temp = {}
    # if signal_mode == 'segment':
    #     for series in active_series:
    #         temp['X'], temp['Y'] = dpg.get_value(series)[:2]
    #         clean, _ = pre.removeCardiacComponent(temp, band)
    #         clean = np.ascontiguousarray(clean)
    #         dpg.configure_item(series,y=clean)
        
    #     prev = dpg.get_item_label(f"plot_{tab_tag}")
    #     dpg.set_item_label(f"plot_{tab_tag}", f"{prev} - Default Filter")
    # else:      

    for series in active_series:
        signal = {}
        signal=getSignalbyIdx(window_id,tab_tag,series,mode=signal_mode)
        # signal['X'], signal['Y']=dpg.get_value(series)[:2]
        clean, _ = pre.removeCardiacComponent(signal, band)
        clean = np.ascontiguousarray(clean)
        updateSignalbyIdx(clean,tab_tag,series,mode=signal_mode)
        noise = np.sum((signal['Y']-clean)**2)
        if noise != 0:
            snr = (10*np.log10(np.sum(np.array(signal['Y'])**2)/noise))
        else: snr = 30

    title = 'Default Filter'
    update_plot_td(tab_tag,signal_tags, title,signal_mode = plot_mode)

def CustomFilter(sender,app_data,user_data):
    tab_tag, signal_tags = user_data

    window_id = extract_window_id(tab_tag)

    if not 'Data' in app_state['windows'][window_id]:
        if 'Events' in app_state['windows'][window_id]['Files'][-1]['Data'][tab_tag].keys():
            mode = 'segment'
        else: mode = None
    else: mode = None

    if dpg.does_item_exist(f"{tab_tag}_filters_container"): dpg.delete_item(f"{tab_tag}_filters_container")
    param_container = dpg.add_child_window(parent=f"{tab_tag}_filters", width=200, height=300, tag = f"{tab_tag}_filters_container")  # Space to add inputs dynamically
    parameter_values = {}
    input_fields = {}
    
    def create_input_fields(sender, app_data):

        
        """Dynamically create input fields for selected function."""
        #global parameter_values, input_fields
        
        dpg.delete_item(param_container, children_only=True)  # Clear previous inputs
        
        params = pre.get_required_params(app_data)
        if not params:
            dpg.add_text("No parameters found", parent=param_container)
            return
        dpg.add_text("Required parameters: ", parent=param_container)
        parameter_values.clear()  # Reset parameter storage
        input_fields.clear()  # Reset input field storage
        # _, documentation = fill_params_features(app_data)
        # documentation = pre.extract_params_and_returns(documentation)
        # dpg.add_text(documentation, parent=doc_container, tag = f"{doc_container}_doc")

        for param, default in params.items():
            if param == 'fs': default = 250

            input_id = dpg.add_input_text(
                label=param, 
                default_value=str(default) if default is not None else "",
                parent=param_container
            )
            input_fields[param] = input_id  # Store input field reference

        # Add save button
        dpg.add_button(label="Save Parameters", callback=save_parameters, parent=param_container, user_data = app_data)

    def save_parameters(sender, app_data, user_data):
        """Saves input values to the dictionary and prints them."""
        parameter_values.clear()  # Reset before saving

        for param, input_id in input_fields.items():
            values = dpg.get_value(input_id)
            if values is str and ',' in values:
                try:
                    # Split the string at the comma and convert each part to a float
                    values = np.array([float(val) for val in values.split(',')])
                except ValueError:
                    print(f"Invalid input for parameter {param}. Please enter valid numbers separated by commas.")
                    return  # If parsing fails, exit early
            parameter_values[param] = values

        if not dpg.does_item_exist(f"{tab_tag}_plot_filtered"): 
            dpg.add_button(label="Plot filtered signal", callback=apply_filt, parent=param_container, user_data=user_data, tag=f"{tab_tag}_plot_filtered")
            
    def apply_filt(sender, app_data, user_data):
        func = user_data
        tags = getActiveSeries(signal_tags)
        args = pre.call_function(func, parameter_values) #gets the parameters of the filter
        
        for tag in tags:
            if mode:
                stream=getSignalbyIdx(window_id,tab_tag,tag,mode='segment')
            else: stream = getSignalbyIdx(window_id,tab_tag,tag)
            y = stream['Y']
            filtered = pre.call_function2('filtfilt', *args, y)
            updateSignalbyIdx(np.ascontiguousarray(filtered),tab_tag,tag, mode=mode)
            snr = (10*np.log10(np.sum(np.array(y)**2)/np.sum(y-filtered)**2))
            print(f"{func} SNR: {snr/100:.3f}")

        title = f'Custom Filter: {func}'
        update_plot_td(tab_tag,signal_tags, title,signal_mode=mode)

    create_input_fields(sender,app_data)

def DefaultFeatures(sender, app_data, user_data):
    tab_tag, signal_tags = user_data
    window_id = extract_window_id(tab_tag)
    wt = extract_type_window(window_id)
    parameter_values = {}

    if app_data== 'multitaper coherence':
        parameter_values, documentation = fill_params_features('dpss')
    elif app_data == 'cross-correlation':
        parameter_values, documentation = fill_params_features('correlate')
        parameter_values['method'] = 'auto'
    elif app_data == 'PAC': 
        parameter_values, documentation = fill_params_features('hilbert')
    else: parameter_values, documentation = fill_params_features(app_data)

    func = app_data

    tags = getActiveSeries(signal_tags)
    events = [getEventsbyTag(tab_tag,serie) for serie in tags]
    if all(e is None for e in events): events = None
    
    if events: mode = 'segment'
    else: mode = None
    
    tab_label = f"{tab_tag}_df_{func}"
    if not dpg.does_item_exist(f"{tab_tag}_features_bar"):
        dpg.add_tab_bar(parent=f"{tab_tag}_features", tag = f"{tab_tag}_features_bar")

    if dpg.does_item_exist(tab_label):
        dpg.delete_item(tab_label, children_only=True)
    else:
        dpg.add_tab(label=f"Default {func}", parent=f"{tab_tag}_features_bar", tag=tab_label, closable=True)  
    
    dates = []
    for tag in tags: 
        signal = getSignalbyIdx(window_id,tab_tag,tag,mode)
        dates.append(signal['Date'])
    dates = np.unique(dates)
    if len(dates)>1:
        plot_modes = ['Join Recordings', 'Separate Recordings']
    else: plot_modes = [None]  

    continue_flag = True
    if wt == 'Individual': mode = None
    elif mode == None and (func == 'spectrogram' or func == 'wavelet'): 
        dpg.add_text(default_value=f"{func} only available in Combined Analysis for Event-lock based signals", show= True, parent=tab_label)
        continue_flag = False
    # dpg.add_group(parent=f"{tab_tag}_features_group", tag = f"{tab_tag}_df_group")
    if continue_flag == True:
        match func:
            case 'spectrogram': 
                if plot_modes[0] != None:
                    if not dpg.does_item_exist(f"{tab_label}_radio"): dpg.add_radio_button(items=plot_modes,label='Plot Mode', parent=tab_label, callback=choose, user_data=(tags, tab_label, func, tab_tag, parameter_values, mode), tag = f"{tab_label}_radio")
                else: plot_spectrogram_og(tags, tab_label, func, tab_tag, parameter_values, mode)
            case 'wavelet': 
                if plot_modes[0] != None:
                    if not dpg.does_item_exist(f"{tab_label}_radio"): dpg.add_radio_button(items=plot_modes,label='Plot Mode', parent=tab_label, callback=choose, user_data=(tags, tab_label, func, tab_tag, parameter_values, mode), tag = f"{tab_label}_radio")
                else: 
                    plot_wavelet(tags, tab_label, func, tab_tag, parameter_values, mode=mode)
            case 'multitaper coherence': plot_multitaper_coherence(parameter_values,tab_tag,tags)
            case 'cross-correlation': plot_cross_correlation(parameter_values,tab_tag,tags,mode='df')
            case 'PAC': plot_pac(tags,tab_tag,parameter_values,mode='df')
            case 'coherence': plot_df_coherence(parameter_values,tab_tag,tags)
            case _: plot_filtered_signal(signal_tags, tab_label, func, tab_tag, parameter_values)

def CustomFeatures(sender,app_data,user_data):
    tab_tag, signal_tags= user_data
    window_id = extract_window_id(tab_tag)
    parameter_values = {}
    input_fields = {}  # Store input field IDs
    tags = getActiveSeries(signal_tags)
    events = [getEventsbyTag(tab_tag,serie) for serie in tags]
    if all(e is None for e in events):events = None
    if events: mode = 'segment'
    else: mode = None
    tab_label = f"{tab_tag}_{app_data}"
    dates = []
    for tag in tags: 
        signal = getSignalbyIdx(window_id,tab_tag,tag,mode)
        dates.append(signal['Date'])
    
    labels = [[dpg.get_item_label(tag), tag] for tag in tags]
    bands = list(getBandsByTab(tab_tag).keys())

    dates = np.unique(dates)

    if len(dates)>1:
        plot_modes = ['Join Recordings', 'Separate Recordings']
    else: plot_modes = [None]

    if dpg.does_item_exist(f"{tab_tag}_ft_input"):
        dpg.delete_item(f"{tab_tag}_ft_input", children_only=True) 
        param_container = f"{tab_tag}_ft_input"
        dpg.delete_item(f"{tab_tag}_ft_doc", children_only=True) 
        doc_container = f"{tab_tag}_ft_doc"
    else:
        group = dpg.add_group(parent=f"{tab_tag}_custom_features", tag = f"{tab_tag}_cf_group", horizontal=True)
        param_container = dpg.add_child_window(width=200, height=300, tag = f"{tab_tag}_ft_input", parent=group)  # Space to add inputs dynamically 
        doc_container = dpg.add_child_window(width=600, height=300, tag = f"{tab_tag}_ft_doc", parent=group)

    def create_input_fields(sender, app_data):

        """Dynamically create input fields for selected function."""
        if app_data == 'multitaper coherence':
            params, documentation = fill_params_features('dpss') 
        elif app_data == 'cross-correlation':
            params, documentation = fill_params_features('correlate')
        elif app_data == 'PAC': 
            params, documentation = fill_params_features('hilbert')
        else: params, documentation = fill_params_features(app_data) 

        documentation = pre.extract_params_and_returns(documentation)
        
        if app_data == 'multitaper coherence':
            for k in ['step', 'nfft','y']:
                params[k] = None
        elif app_data == 'cross-correlation': 
            params['method'] = 'Choose: auto/direct/fft'
            params['mode'] = 'Choose: full/same/valid'
            params['dislocation'] = None
            params['normalization'] = None
            
        elif app_data == 'PAC': 
            for k in ['s1', 's2','b1', 'b2','n_bins']:
                params[k] = 'choose'

        dpg.add_text(documentation, parent=doc_container, tag = f"{doc_container}_doc")       
        if not params:
            dpg.add_text("No parameters found", parent=param_container)
            return
        dpg.add_text("Required parameters: ", parent=param_container)

        parameter_values.clear()  # Reset parameter storage
        input_fields.clear()  # Reset input field storage
        
        combos = {}   
        
        for param, default in params.items():
            # Set defaults
            if param == 'x' or param == 'data':
                default = '---'
            if param == 'y' and app_data == 'coherence':
                default = '---'
            if param == 'fs' or param == 'sfreq':
                default = 250
            if param == 'output':
                default = 'power'  # wavelet
            if param == 'freqs':
                default = 100  # wavelet

            if param != 'window':
                if ((param == 'x' or param == 'y') and 
                (app_data == 'coherence' or app_data=='multitaper coherence')) or (
                    (param=='a' or param=='v') and app_data=='cross-correlation') or (
                        app_data == 'PAC' and (param=='s1' or param=='s2')
                    ):
                    
                    # Use a combo box (select box) for this special case
                    input_id = dpg.add_combo(
                        label=param,
                        items=[l[0] for l in labels], 
                        default_value=default,
                        parent=param_container,
                        callback=different_combo,
                        tag = f"{tab_label}_{param}",
                        user_data=(doc_container, combos)
                    )
                    combos[param] = input_id

                elif app_data=='PAC' and (param=='b1' or param=='b2'):
                    input_id = dpg.add_combo(
                            label=param,
                            items=bands,  # <-- customize your options
                            default_value=default,
                            callback=different_combo,
                            user_data=(doc_container, combos),
                            tag = f"{tab_label}_{param}",
                            parent=param_container,
                        )
                    combos[param] = input_id
                else:
                    # Default to input text
                    input_id = dpg.add_input_text(
                        label=param,
                        default_value=default if default is not None else " ",
                        parent=param_container
                    )

                input_fields[param] = input_id  # Store input field reference


        # Add save button
        dpg.add_button(label="Save Parameters", callback=save_parameters, parent=param_container, user_data = app_data)

    def save_parameters(sender, app_data, user_data):
        """Saves input values to the dictionary and prints them."""
        parameter_values.clear()  # Reset before saving

        for param, input_id in input_fields.items():
            value = dpg.get_value(input_id)
            if (param == 'x' or param == 'y') and user_data == 'coherence':
                ls = [l[0] for l in labels]
                index = ls.index(value)
                tag = labels[index][1]
                signal = getSignalbyIdx(window_id,tab_tag,tag)
                parameter_values[param] = signal

            else: parameter_values[param] = value

        
        if not dpg.does_item_exist(f"{tab_tag}_plot_features"):
            dpg.add_button(label="Plot filtered signal", callback=apply_filt, parent=param_container, user_data=user_data, tag=f"{tab_tag}_plot_features")

    def apply_filt(sender, app_data, user_data):
        func = user_data

        tags = getActiveSeries(signal_tags)
        tab_label = f"{tab_tag}_{func}"
        if not dpg.does_item_exist(f"{tab_tag}_features_bar"):
            dpg.add_tab_bar(parent=f"{tab_tag}_features", tag = f"{tab_tag}_features_bar")

        if dpg.does_item_exist(tab_label):
            dpg.delete_item(tab_label, children_only=True)
        else:
            dpg.add_tab(label=f"{func}", parent=f"{tab_tag}_features_bar", tag=tab_label, closable=True)  
        
        match func:
            case 'spectrogram': 
                if plot_modes[0] != None:
                    if not dpg.does_item_exist(f"{tab_label}_radio"): dpg.add_radio_button(items=plot_modes,label='Plot Mode', parent=tab_label, callback=choose, user_data=(tags, tab_label, func, tab_tag, parameter_values, mode), tag = f"{tab_label}_radio")
                else: plot_spectrogram_og(tags, tab_label, func, tab_tag, parameter_values, mode)
            case 'wavelet': 
                if plot_modes[0] != None:
                    if not dpg.does_item_exist(f"{tab_label}_radio"): dpg.add_radio_button(items=plot_modes,label='Plot Mode', parent=tab_label, callback=choose, user_data=(tags, tab_label, func, tab_tag, parameter_values, mode), tag = f"{tab_label}_radio")
                else: 
                    plot_wavelet(tags, tab_label, func, tab_tag, parameter_values)
            case 'multitaper coherence': plot_multitaper_coherence(parameter_values,tab_tag,tags,flag='flag')
            case 'PAC': plot_pac(tags,tab_tag,parameter_values)
            case 'coherence': plot_coherence(parameter_values,tab_label)
            case 'cross-correlation': plot_cross_correlation(parameter_values,tab_tag,tags)
            case _: plot_filtered_signal(signal_tags, tab_label, func, tab_tag, parameter_values)
                                     
    create_input_fields(sender,app_data)

def insert_events(sender, app_data, user_data):
    window_id, tab_tag, signal_tags= user_data

    if dpg.does_item_exist(f"{tab_tag}_emin"):
        min = int(dpg.get_value(f"{tab_tag}_emin"))*250
        max = int(dpg.get_value(f"{tab_tag}_emax"))*250

    window_type = extract_type_window(window_id)

    def read_txt(sender, app_data, user_data):
        window_id, tab_tag, signal_tags = user_data
        
        streaming_file = app_data['file_path_name']
        events = utl.read_event_file(streaming_file)
        scatter, dates = [], []
        series = getActiveSeries(signal_tags)
        window_id = extract_window_id(tab_tag)

        scale = dpg.get_item_configuration(f"x_axis_{tab_tag}")['scale']
        for i,tag in enumerate(series):
            signal = getSignalbyIdx(window_id,tab_tag,tag)
            if window_type == 'Combined':
                file = extract_file_from_series_tag(tag)
                if 'Events' not in app_state['windows'][window_id]['Files'][file]['Data'][tab_tag].keys():
                    app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Events'] = []
            else:
                idx = extract_idx_from_series_tag(tag)
                if 'Events' not in app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx].keys():
                    app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]['Events'] = []

            date = signal['Date']

            channel = signal['Channel']
            if channel in electrodes_names.keys():
                channel = electrodes_names[channel]
            else:
                electrodes_names[channel] = channel

            dates.append(f"{date.year}-{date.month}-{date.day}")

            if scale == 0: #in linear
                new_time = [date + timedelta(seconds=val) for val in signal['X'] if isinstance(val,(int,float))]
                new_x = [d.timestamp() for d in new_time]
                updateKeySignalbyIdx(new_x,tab_tag,series[i],'X')
                dpg.configure_item(f"x_axis_{tab_tag}",scale=dpg.mvPlotScale_Time)
                dpg.configure_item(f"x_axis_{tab_tag}",label='Time (UTC)')
                dpg.configure_item(series[i], x=new_x)
            else: 
                new_x = signal['X']
                new_time = [datetime.fromtimestamp(val) for val in new_x]
                    
            for _, event in enumerate(events):
                hour, minute, second, type = event
                tidx = utl.find_closest_index(new_time,hour,minute, second)
                flag = True
                if tidx != None: 
                    flag = False
                    # events_times[f"{hour}:{minute}"] = (type, tidx)
                    tidx = int(tidx)
                    scatter.append([new_x[tidx], type, new_time[tidx]])
                    date_event = new_time[tidx]

                    if dpg.does_item_exist(f"{tab_tag}_emin"):
                        imin = tidx-min
                        imax = tidx+max
                        if imin<0:
                            imin = 0
                            imax = tidx+max+min
                        if imax>len(new_x)-1:
                            imax = len(new_x)-1
                            imin = len(new_x) -1-(max+min)

                        segment_x = new_x[imin:imax]
                        new_y = signal['Y'][imin:imax]
                        x_shift = segment_x[min] #mid_index

                        aligned_x = [xi - x_shift for xi in segment_x]
                        segment = {'X': aligned_x,'Y':new_y,'Channel':channel,'Type':type, 'Date': date_event, 'Idx': tidx, 'Serie': i}
                    else:
                        segment = {'Channel':channel,'Type':type, 'Date': date_event, 'Idx': tidx, 'Serie': i}

                    if window_type == 'Combined': app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Events'].append(segment)
                    else: app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]['Events'].append(segment)

            # if flag:
            #     if window_type == 'Combined': app_state['windows'][window_id]['Files'][file]['Data'][tab_tag].pop('Events')
            #     else: app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx].pop('Events')


        if scatter: 
            event_types = [s[1] for s in scatter]
            event_types = np.unique(event_types).tolist()
            for i, point in enumerate(scatter):
                idx, etype, time = point
                tag = f"{tab_tag}_{etype}_{time}"
                if not dpg.does_item_exist(tag): 
                    m = dpg.add_inf_line_series(parent=f"y_axis_{tab_tag}", x=[idx], label=f"{etype} - {time}", tag=tag)
                    # dpg.bind_item_theme(m, change_line_thickness(5, component=dpg.mvInfLineSeries))
                    dpg.bind_item_theme(m, change_inf_line_color(event_types.index(etype)))

                signal_tags[tag] = True

            scatter = np.array(scatter, dtype=object)
            types= np.unique(scatter[:,1]).tolist()
            if len(types)>1:
                if dpg.does_item_exist(f"{tab_tag}_buttons_hours"): dpg.delete_item(f"{tab_tag}_buttons_hours")

                # old_parent = f"{tab_tag}_add_events"
                new_parent = f"{tab_tag}_types"
                if dpg.does_item_exist(f"{new_parent}_events"): 
                    children = dpg.get_item_children(f"{new_parent}_events")
                    for _, child in children.items():
                        for kid in child:
                            label = dpg.get_item_label(kid)
                            if label not in types and label != '': types.append(label)
                    dpg.delete_item(f"{new_parent}_events")
                with dpg.group(parent=new_parent, tag = f"{new_parent}_events"):
                    dpg.add_text('By Event:')
                    for day in types:
                        toggleType(signal_tags,parent=f"{new_parent}_events", orientation=True, user_data=(day, window_id, tab_tag))  
            if window_type == 'Combined': align_events(sender,app_data,(tab_tag,signal_tags))  
        else: 
            dpg.add_text("No Events in the present recordings!", parent=f"{tab_tag}_add_events")

    def create_file_dialog(window_id,tab_tag, signal_tags):
        with dpg.file_dialog(
            directory_selector=False, 
            show=True, 
            callback=read_txt, 
            width=700, 
            height=400,
            modal=True, 
            default_path="C:/Users/OCD/Desktop/LRodrigues/NeoDBS",
            user_data=(window_id,tab_tag, signal_tags)
        ) as dialog_id:
            dpg.add_file_extension(".txt", color=(0, 255, 0, 255), custom_text="[TEXT File]")

    create_file_dialog(window_id,tab_tag, signal_tags)

def align_events(sender,app_data, user_data):
    tab_tag, signal_tags = user_data
    window_id = extract_window_id(tab_tag)
    window_type = extract_type_window(window_id)
    parent = f"y_axis_{tab_tag}"

    all_events, edx, fdx = [], [], []
    if window_type == 'Combined':
        files = app_state['windows'][window_id]['Files']
        for idx,_ in enumerate(files):
            count = 0
            if 'Events' in files[idx]['Data'][tab_tag].keys():
                events = files[idx]['Data'][tab_tag]['Events']
                if len(events)>1: #why only 1?
                    for event in events: 
                        all_events.append(event)
                        edx.append(count)
                        count+=1
                        fdx.append(idx)

        dpg.delete_item(parent,children_only=True)
        signal_tags.clear()
        dpg.configure_item(f"x_axis_{tab_tag}", scale=dpg.mvPlotScale_Linear)
        plot_td(all_events,parent,tab_tag, signal_tags,files=fdx,events=True, count=edx)
                # else: dpg.add_text('To compare events, needs at least 2 events', parent=parent)

        dpg.configure_item(f"{tab_tag}_add_events", show = False)
        dpg.configure_item(f"{tab_tag}_all_streams", show = False)
        dpg.configure_item(f"{tab_tag}_segmentation", show = False)

    else:
        signals = app_state['windows'][window_id]['Data'][tab_tag]['Signals']
        events = []
        for idx,_ in enumerate(signals):
            temp = getEventsbyIdx(tab_tag,idx)
            for t in temp: events.append(t)
        if len(events)>1:
            dpg.delete_item(parent,children_only=True)
            signal_tags.clear()
            dpg.configure_item(f"x_axis_{tab_tag}", scale=dpg.mvPlotScale_Linear)
            plot_td(events,parent,tab_tag, signal_tags,events=True)
            # else: dpg.add_text('To compare events, needs at least 2 events', parent=parent)

def changeTimelinePlot(sender,app_data,user_data):
    signal_tags, signals, data, plot_tag = user_data

    # signals = getActiveSignals(tab_tag,signal_tags)

    for idx, signal in enumerate(signals):
        for j, tag in enumerate(signal_tags.keys()):
            i = extract_idx_from_series_tag(tag)
            if i == idx and signal_tags[tag]==True:
                if app_data:
                    if isinstance(data,list):
                        dictionary = data[idx]
                    else: dictionary = data
                    if dictionary != None: 
                        extra = DH.correctMissingTimeline(dictionary, signal,'X_missing')[0]
                        for side in ['Left','Right']:
                            tagg = f"{tag}_{side}_added"
                            extra_x, extra_y = extra[side]['X_missing'], extra[side]['Y_missing']
                            extra_x = [x.timestamp() for x in extra_x]
                            if extra_x != []:
                                dpg.add_scatter_series(extra_x,extra_y,tag = tagg, parent=plot_tag)
                else:
                    if dpg.does_item_exist(f"{tag}_Left_added"): 
                        dpg.delete_item(f"{tag}_Left_added")
                        dpg.delete_item(f"{tag}_Right_added")

def circadian_rhythm(sender, app_data, user_data):
    tab_tag, signal_tags, data = user_data
    tab_label = tab_tag+'_circadian'
    window_id = extract_window_id(tab_tag)

    if not dpg.does_item_exist(f"{tab_tag}_features_bar"):
        dpg.add_tab_bar(parent=f"{tab_tag}_features", tag = f"{tab_tag}_features_bar")

    if dpg.does_item_exist(tab_label):
        dpg.delete_item(tab_label,children_only=True)
    else:
        dpg.add_tab(label=f"Circadian Rhythm", parent=f"{tab_tag}_features_bar", tag=tab_label)

    tags = getActiveSeries(signal_tags)

    days = {}
    mean, dates = [], []

    #preparing streams
    for tag in tags:
        dates.append(getSignalbyIdx(window_id,tab_tag,tag)['Date'][:10])
        old_x,old_y = dpg.get_value(tag)[:2]
        x = sorted(old_x)
        if x[0] != old_x[0]:
            old_y = list(reversed(old_y))

        old_x = [utl.extract_time_from_datetime_string(str(datetime.fromtimestamp(xx).time())) for xx in x]

        x,y = [], []
        for n in range(len(old_x)-1):
            x.append(old_x[n])
            y.append(old_y[n])
            if old_x[n+1]-old_x[n]>660:
                gap_times = np.arange(old_x[n]+600, old_x[n+1], 600)
                x.extend(gap_times)
                y.extend([np.nan]*len(gap_times))

        x.append(old_x[-1])
        y.append(old_y[-1])
        
        last = utl.extract_time_from_datetime_string("23:59:00")
        if x[0]>60*10:
            if x[0]>last:
                x[0] = x[0]-last
                
            diff = int((x[0]-600)//600)+1
            nan_array = [np.nan]*diff
            y = nan_array + y
            x = list(np.arange(x[0]-(diff*600),x[0],600)) + x

        
        if x[-1]<last:
            diff = int((last - x[-1])//600)+1
            nan_array = [np.nan]*diff
            y = y + nan_array
            x = x + list(np.arange(x[-1],last,600))

        days[tag] = [x,y]
        
        mean.append(y)

    mean = np.nanmean(mean,axis=0)
    minus = mean - np.nanstd(mean,axis=0)
    plus = mean + np.nanstd(mean,axis=0)

    def toggle(sender,app_data,user_data):
        label = dpg.get_item_label(sender)
        new_mean = []
        if dpg.get_value(f"{tab_label}_hide") == True:
            callback = dpg.get_item_callback(f"{tab_label}_hide")
            dpg.set_value(f"{tab_label}_hide",False)
            if callback:
                callback(f"{tab_label}_hide", None, dpg.get_item_user_data(f"{tab_label}_hide"))

        toggle_tags = [f"{tag}_{tab_label}" for tag in getActiveSeries(tags)]

        for t in toggle_tags:
            taglabel = dpg.get_item_label(t) 
            if label in taglabel:
                dpg.configure_item(t,show=app_data)
            show = dpg.get_item_configuration(t)['show']
            if show: 
                new_mean.append(dpg.get_value(t)[1])

        new_mean = np.nanmean(new_mean,axis=0)
        new_minus = new_mean - np.nanstd(new_mean,axis=0)
        new_plus = new_mean + np.nanstd(new_mean,axis=0)
        dpg.configure_item(f"{tab_label}_mean",y=new_mean)
        dpg.configure_item(f"{tab_label}_std",y1=new_minus,y2=new_plus)


    with dpg.group(parent=tab_label, horizontal=True, tag=f"{tab_label}_CR"):
        with dpg.plot(label = "Circadian Rhythm", tag = f'{tab_label}_plot', width=800): 
            dpg.bind_colormap(f"{tab_label}_plot", 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", scale = dpg.mvPlotScale_Time) #tag=f"{tab_label}_x_axis"
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power (µVp)", tag= f"{tab_label}_y_axis")
            
            for tag, val in days.items():
                label = dpg.get_item_label(tag)
                dpg.add_line_series(val[0],val[1],label=label,parent=y_axis, tag = f"{tag}_{tab_label}",skip_nan=False)

                new_x = [datetime.fromtimestamp(xx) for xx in val[0]]

                sign = {'X':new_x,'Y':val[1]}

                if not dpg.does_item_exist(f"{tab_label}_header"):
                    dpg.add_collapsing_header(tag=f"{tab_label}_header", parent=tab_label, label = 'Circadian Metrics')

                info = extract_timeline_features(sign)
                create_table(f"{tab_label}_header",f"{tab_label}_table", info, trial_label=label)


            s = dpg.add_shade_series(val[0],y1=minus,y2=plus,parent=y_axis,label='Std. Dev.',tag=f"{tab_label}_std")
            dpg.bind_item_theme(s,create_alpha_theme())
            m = dpg.add_line_series(val[0],mean,parent=y_axis,label='Mean',tag=f"{tab_label}_mean",skip_nan=False)
            dpg.bind_item_theme(m,change_line_thickness(4))

            sign = {'X':new_x,'Y':mean}

            info = extract_timeline_features(sign)
            create_table(f"{tab_label}_header",f"{tab_label}_table", info, trial_label='Mean')

        dates = np.unique(dates)
        checkboxes = []
        with dpg.group():
            with dpg.child_window(width=120, height=250):
                dpg.add_text('By Day:')
                for d in dates:
                    c = dpg.add_checkbox(label=d, default_value=True, callback=toggle)
                    checkboxes.append(c)
            with dpg.group():
                for side in ['Left', 'Right']:
                    dpg.add_checkbox(label=side, default_value=True, callback=toggle)
            dpg.add_checkbox(label='Hide Days', tag = f"{tab_label}_hide", callback=hide,parent = f"{tab_label}_vbuttons", user_data=(tags,checkboxes))

def stimulation_timeline(sender,app_data,user_data):
    tab_tag, signal_tags, data = user_data
    tab_label = tab_tag+'_stimulation'
    window_id = extract_window_id(tab_tag)

    if not dpg.does_item_exist(f"{tab_tag}_features_bar"):
        dpg.add_tab_bar(parent=f"{tab_tag}_features", tag = f"{tab_tag}_features_bar")

    if dpg.does_item_exist(tab_label):
        dpg.delete_item(f"{tab_label}_plot_group")
    else:
        dpg.add_tab(label=f"Stimulation", parent=f"{tab_tag}_features_bar", tag=tab_label)

    if extract_type_window(window_id) == 'Combined': 
        tag_date_pairs = []
        for tag in signal_tags:
            data = getDatabyTag(tag)
            date = data['Device']['SessionDate']
            tag_date_pairs.append((tag, date))

        tag_date_pairs.sort(key=lambda x: x[1])

        signal_tags = [tag for tag, _ in tag_date_pairs]

        files = [extract_file_from_series_tag(tag) for tag in signal_tags]
        files = np.unique(files)
    else: files = [None]
    # datas = [getDatabyFile(window_id,file) for file in files]


    stimulation = {'X': [], 'Y': [], 'Info':[]}
    for file in files: 
        stimus = DH.getStimulation(getDatabyFile(window_id,file))
        for x in stimus['X']: stimulation['X'].append(x)
        for x in stimus['Y']: stimulation['Y'].append(x)
        for x in stimus['Info']: 
            if stimulation['Info']!= [] and x[:10] == stimulation['Info'][-1][:10]: 
                stimulation['Info'][-1] = x
                continue
            stimulation['Info'].append(x)


    with dpg.group(parent=tab_label, horizontal=True):
        with dpg.plot(label = "Stimulation", tag = f'{tab_label}_plot', width=500, height=400): 
            dpg.bind_colormap(f"{tab_label}_plot", 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", scale = dpg.mvPlotScale_Time) #tag=f"{tab_label}_x_axis"
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Stimulation Amplitude (mA)", tag= f"{tab_label}_y_axis")

            x = [utl.parse_datetime(x).timestamp() for x in stimulation['X']]
            y = stimulation['Y']
            l = dpg.add_line_series(x,y,parent=y_axis)
            dpg.bind_item_theme(l,change_line_thickness(4))
        with dpg.group():
            dpg.add_text('Information')
            with dpg.child_window(height=380):
                for info in stimulation['Info']:
                    dpg.add_text(info)
                    dpg.add_separator()

def AnalyzeTimelineEvents(sender,app_data,user_data):
    tab_tag, events_tags, signal_tags = user_data
    # window_id = extract_window_id(tab_tag)
    # files = np.unique([e[1] for e in events_tags])

    event_ids = [dpg.get_value(e[0])[0] for e in events_tags]
    event_labels = [dpg.get_item_label(e[0]) for e in events_tags]

    timelines = [dpg.get_value(t)[:2] for t in signal_tags.keys()]
    timeline_labels = [dpg.get_item_label(t) for t in signal_tags.keys()]

    segments, event_names, checkboxes, days, temp_tags = [], [], [], [], []

    def cut_segment(x,y,event):

        diff = [abs(xx-event) for xx in x]
        ev_id = diff.index(min(diff))
        
        half_window = 6

        if ev_id >= half_window and ev_id <= len(x) - half_window - 1:
            start = ev_id - half_window
            end = ev_id + half_window + 1
            segment_x = x[start:end]
            segment_y = y[start:end]
        elif ev_id < half_window:
            # Pad at the start
            pad = np.full(half_window - ev_id, np.nan)
            segment_x = np.concatenate([pad, x[0:ev_id + half_window + 1]])
            segment_y = np.concatenate([pad, y[0:ev_id + half_window + 1]])
        else:
            # Pad at the end
            pad = np.full(ev_id + half_window + 1 - len(x), np.nan)
            segment_x = np.concatenate([x[ev_id - half_window:], pad])
            segment_y = np.concatenate([y[ev_id - half_window:], pad])

        onex = segment_x[0]
        segment_x = [x - onex for x in segment_x]

        return segment_x,segment_y

    for ex, event in enumerate(event_ids):
        event = event[0]
        for timeline in timelines:
            x, y = timeline[0], timeline[1]
            first, last = min(x), max(x)
            label = f"{event_labels[ex]} - {timeline_labels[timelines.index(timeline)]}"
            if not (first <= event <= last):
                continue
            
            segment = cut_segment(x,y,event)
            segments.append([segment,label])
            event_names.append(label)
            date = utl.date2str(datetime.fromtimestamp(event))
            days.append(date)

    values = [segment[0][1] for segment in segments]
    
    mean_value = np.nanmean(values, axis = 0)
    std_dev = np.nanstd(values, axis = 0)

    tab_label = tab_tag+'_events'
    plot_tag = f'{tab_label}_plot'

    def normal(segments, plot=True, bva=False):
        for s, seg in enumerate(segments):
            segment, label = seg
            x,y=segment[0],segment[1]
            if plot:
                dpg.add_line_series(x,y,label=label,parent=y_axis,tag=f"{tab_label}_{label}_{s}")
                temp_tags.append(f"{tab_label}_{label}_{s}")

            sign = {'X':x,'Y':y}                

            if not bva:
                header = f"{tab_label}_header"
                table = f"{tab_label}_table"
            elif 'Before' in label:
                header = f"{tab_label}_header_before"
                table = f"{tab_label}_table_before"
            else: 
                header = f"{tab_label}_header_after"
                table = f"{tab_label}_table_after"

            if not dpg.does_item_exist(f"{tab_label}_header"):
                dpg.add_collapsing_header(tag=f"{tab_label}_header", parent=tab_label,label='Stream Metrics')

            if not dpg.does_item_exist(f"{tab_label}_header_before"):
                dpg.add_collapsing_header(tag=f"{tab_label}_header_before", parent=tab_label,label='Before | Stream Metrics')

            if not dpg.does_item_exist(f"{tab_label}_header_after"):
                dpg.add_collapsing_header(tag=f"{tab_label}_header_after", parent=tab_label,label='After | Stream Metrics')

            if not isinstance(y,(list,np.ndarray)) or (np.all(y) == np.nan):
                continue
            info = extract_timeline_features(sign)
            if info != None: 
                create_table(header,table, info, trial_label=label)

        minus = mean_value - std_dev
        plus = mean_value + std_dev
        if plot:
            std = dpg.add_shade_series(segment[0],minus, y2 = plus,label='Std. Dev', parent=y_axis, tag = f"{tab_label}_std")
            dpg.bind_item_theme(std,create_alpha_theme())
            mean = dpg.add_line_series(segment[0],mean_value,label='Mean',parent=y_axis, tag = f"{tab_label}_mean")
            dpg.bind_item_theme(mean, change_line_thickness(5))

        mean_info = {'X': segment[0], 'Y':list(mean_value)}
        mean_info = extract_timeline_features(mean_info)
        create_table(f"{tab_label}_header",f"{tab_label}_table", mean_info, trial_label='Mean')

    def bva(segments):
        bva_segments = []
        for segment, label in segments:
            x,y = segment
            before = [x[:6],y[:6]]
            bva_segments.append([before,f"Before | {label}"])
            after = [x[6:],y[6:]]
            bva_segments.append([after,f"After | {label}"])
        normal(bva_segments, plot=False, bva=True)

    def toggle(sender,app_data,user_data):
        name = dpg.get_item_label(sender)
        mean_temp = []

        c = f"{tab_label}_hide"
        if dpg.get_value(c)==True:
            dpg.set_value(c,False)
            for s, tag in enumerate(segments):
                t, label = tag
                dpg.configure_item(f"{tab_label}_{label}_{s}",show=True)


        for s, tag in enumerate(segments):
            t, label = tag
            if name in label:
                dpg.configure_item(f"{tab_label}_{label}_{s}",show=app_data)
            show = dpg.get_item_configuration(f"{tab_label}_{label}_{s}")['show']
            if show:
                mean_temp.append(t[1])
            
        new_mean = np.nanmean(mean_temp,axis=0)
        new_std = np.nanstd(mean_temp,axis=0)
        minus = new_mean - new_std
        plus = new_mean + new_std

        dpg.configure_item(f"{tab_label}_std",y1=minus, y2=plus)
        dpg.configure_item(f"{tab_label}_mean",y=new_mean)

        mean_info = {'X': t[0], 'Y':new_mean}
        mean_info = extract_timeline_features(mean_info)
        create_table(f"{tab_label}_header",f"{tab_label}_table", mean_info, trial_label='New Mean')

    if not dpg.does_item_exist(f"{tab_tag}_features_bar"):
        dpg.add_tab_bar(parent=tab_tag, tag = f"{tab_tag}_features_bar")

    if dpg.does_item_exist(tab_label):
        dpg.delete_item(tab_label,children_only=True)
    else:
        dpg.add_tab(label=f"Timeline Events", parent=f"{tab_tag}_features_bar", tag=tab_label)

    e_names = np.unique(event_labels).tolist()
    with dpg.group(parent=tab_label, tag=f"{plot_tag}_group", horizontal=True):
        with dpg.plot(label = 'Event-locked Segments',tag = plot_tag,  width=600, height=400):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{plot_tag}", scale=dpg.mvPlotScale_Time)
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µVP)", tag=f"y_axis_{plot_tag}")

            max_timestamp = 2*60*60
            dpg.set_axis_limits(x_axis, 0, max_timestamp)

            normal(segments)
            bva(segments)

    with dpg.group(parent=f"{plot_tag}_group"):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=120,height=150):
                dpg.add_text('Hemisphere: ')
                for side in ['Left', 'Right']:
                    c = dpg.add_checkbox(label=side,callback = toggle,default_value=True)
                    checkboxes.append(c)
            with dpg.child_window(width=120,height=150):
                dpg.add_text('Events: ')
                for side in e_names:
                    c = dpg.add_checkbox(label=side,callback = toggle,default_value=True)
                    checkboxes.append(c)
            with dpg.child_window(width=120,height=150):
                dpg.add_text('Days: ')
                days = np.unique(days).tolist()
                for side in days:
                    c = dpg.add_checkbox(label=side,callback = toggle,default_value=True)
                    checkboxes.append(c)
        dpg.add_separator()
        dpg.add_checkbox(label='Hide Signals', tag = f"{tab_label}_hide", callback=hide, user_data=(temp_tags,checkboxes))

def RemoveTimelineOutliers(sender,app_data,user_data):
    tab_tag,signal_tags = user_data
    window_id = extract_window_id(tab_tag)
    tags = getActiveSeries(signal_tags)

    factor = app_data

    if dpg.does_item_exist(f"{tab_tag}_plot_progress"): dpg.delete_item(f"{tab_tag}_plot_progress")

    # create_table(f"{tab_tag}_header",f"{tab_tag}_table", info, trial_label=label_left)
    dpg.delete_item(f"{tab_tag}_header", children_only=True)

    dpg.add_progress_bar(parent=f"{tab_tag}_plot_group",overlay='Removing', default_value=0.0, width = 400, height = 50, tag = f"{tab_tag}_plot_progress")
    
    for i, tag in enumerate(tags):
        values = dpg.get_value(tag)
        x,_= values[0], values[1]
        data = getDatabyTag(tag)
        info = dpg.get_item_configuration(tag)
        series_label = info['label']
        side = series_label.split(' ')[0]

        stream = getSignalbyIdx(window_id,tab_tag,tag)
        stream = DH.correctMissingTimeline(data,stream)[0]
        new_x,y = stream[side]['X'],stream[side]['Y']

        new_x = [utl.convert_to_timestamp(n) for n in new_x]
        y = np.array(y)
        copy = np.copy(y)


        '''USING RMS'''
        # threshold = np.sqrt(np.mean(np.array(y)**2))

        # '''USING ITERATIVE RMS'''
        rms = np.sqrt(np.mean(y**2))

        for _ in range(3):  # Iterate a few times
            y = y[np.abs(y) <= factor * rms]
            rms = np.sqrt(np.mean(y**2))
        # threshold =rms

        '''USING MEDIAN'''
        mad = np.median(np.abs(y - np.median(y)))
        threshold = mad   # Or some scaled version
       
        
        mask = copy > factor*threshold
        copy[mask] = rms
        dpg.set_value(tag,[new_x,copy.tolist()])
        updateSignalbyIdx(copy.tolist(),tab_tag,tag,f'Filtered_{side}')

        sign = {'X': new_x, 'Y':copy.tolist()}
        info = extract_timeline_features(sign)
        create_table(f"{tab_tag}_header",f"{tab_tag}_table", info, trial_label=dpg.get_item_label(tag))
        

        progress = np.round((i+1)/len(tags),2)
        dpg.set_value(f"{tab_tag}_plot_progress", progress)
        if progress == 1: dpg.configure_item(f"{tab_tag}_plot_progress", overlay = 'Removed')

#-------------------------------------GENERAL TABS-------------------------------------------
def device_window(Data, window_id, file_id = None):
    wt = extract_type_window(window_id)
    device = DH.getDeviceInfo(Data)
    battery = DH.getBatteryInfo(Data)
    battery_reminder = Data['Device']['BatteryReminder']
    date = DH.getSessionDate(Data)
    info_parent = f"device_parameteres_{window_id}"

    dpg.configure_item(f"{info_parent}_title", show=True)
    
    if wt == 'Individual':
        dpg.delete_item(item=info_parent,children_only=True)   
    else:
        dpg.configure_item(info_parent, show=True)
        header_tag = info_parent + f'_{file_id}'
        if dpg.does_item_exist(header_tag): dpg.delete_item(header_tag)
        dpg.add_collapsing_header(tag=header_tag, parent=info_parent, label = date)
        info_parent = header_tag

    #WARNINGS
    if battery_reminder==True: 
        w = dpg.add_text("WARNING: Battery needs recharge!", parent=f"window_{window_id}", show=True)
        color = change_text_color(0)
        dpg.bind_item_theme(w,color)
    if int(device['OverdischargeCount'])>0: 
        w = dpg.add_text(f"Warning! Overdischarge count above 0", parent=f"window_{window_id}")
        color = change_text_color(0)
        dpg.bind_item_theme(w,color)

    #INFO
    dpg.add_text(f"Battery Charge: {battery['BatteryPercentage']}%", parent=info_parent, show=True)
    dpg.add_text(f"Battery Status: {utl.after_point(battery['BatteryStatus'])}", parent=info_parent, show=True)
    dpg.add_separator(parent=info_parent)
    dpg.add_text(f"Neurostimulator: {device['Neurostimulator']} {device['NeurostimulatorModel']}", parent=info_parent, show=True)
    dpg.add_text(f"Location: {utl.after_point(device['NeurostimulatorLocation'])}", parent=info_parent, show=True)
    dpg.add_text(f"Overdischarge Count: {device['OverdischargeCount']}", parent=info_parent, show=True)
    dpg.add_separator(parent=info_parent)
    dpg.add_text('Versions', parent=info_parent)
    dpg.add_text(f"Device Version: {device['DeviceVersion']}", parent=info_parent)
    dpg.add_text(f"Product Version: {device['ProductVersion']}", parent=info_parent)

    dpg.configure_item(info_parent, show=True)

def stimulation_window(Data, window_id, file_id = None):
    wt = extract_type_window(window_id)
    try:
        stimulation = DH.info_electrodes(Data)
    except Exception as e: 
        print(e)
        return
    
    
    date = DH.getSessionDate(Data)
    info_parent = f"stimulation_parameteres_{window_id}"
    
    dpg.configure_item(f"{info_parent}_title", show=True)


    if wt == 'Individual':
        dpg.delete_item(item=info_parent,children_only=True) 
    else:
        dpg.configure_item(info_parent, show=True)
        header_tag = info_parent + f'_{file_id}'
        if dpg.does_item_exist(header_tag): dpg.delete_item(header_tag)
        dpg.add_collapsing_header(tag=header_tag, parent=info_parent, label = date)
        info_parent = header_tag
            
    ch = stimulation['Sense_electrodes']
    if ch in electrodes_names.keys():
        ch = electrodes_names[ch]
    else:
        electrodes_names[ch] = ch
    
    dpg.add_text(f"Active Group: {stimulation['Group_id']}", parent=info_parent)
    dpg.add_text(f"Frequency: {stimulation['Frequency']} Hz", parent=info_parent)
    dpg.add_text(f"Amplitude: {stimulation['Amplitude']} mA", parent=info_parent)
    dpg.add_text(f"Pulse Width: {stimulation['Pulse']} µs", parent=info_parent)
    dpg.add_text(f"Type: {stimulation['Type']}", parent=info_parent)
    dpg.add_text(f"Electrodes: {stimulation['Stim_electrodes']}", parent=info_parent)
    dpg.add_separator(parent=info_parent)
    dpg.add_text(f"Sensing Channel: {ch}", parent=info_parent)
    f = stimulation['Sense_frequency']
    if f != '': 
        f1, f2 = f-2.5,f+2.5
        dpg.add_text(f"Sensing Band: [{f1}, {f2}] Hz", parent=info_parent)
    
    dpg.configure_item(info_parent, show=True)

def session_window(Data, window_id, file_id = None):
    wt = extract_type_window(window_id)
    date = DH.getSessionDate(Data)
    session_duration = DH.getSessionDuration(Data)
    initial_stim_status, final_stim_status = DH.getStimStatus(Data)
    impedance = DH.getImpedance(Data)
    patient_info = DH.getPatientInfo(Data)
    info_parent = f"session_parameteres_{window_id}"

    dpg.configure_item(f"{info_parent}_title", show=True)


    if not isinstance(impedance, str):
        impedance_status, l, r = impedance
    else: 
        impedance_status = impedance
        l=False

    if wt == 'Individual':
        dpg.delete_item(item=f"session_parameteres_{window_id}",children_only=True) 
    else:
        header_tag = info_parent + f'_{file_id}'
        if dpg.does_item_exist(header_tag): dpg.delete_item(header_tag)
        dpg.add_collapsing_header(tag=header_tag, parent=info_parent, label = date)
        info_parent = header_tag
    
    dpg.add_text(f"Session date: {date}", parent=info_parent, show=True)
    dpg.add_text(f"Session duration: {session_duration}", parent=info_parent, show=True)
    dpg.add_text(f"Initial Stimulation: {initial_stim_status}", parent=info_parent, show=True)
    dpg.add_text(f"Final Stimulation: {final_stim_status}", parent=info_parent, show=True)
    dpg.add_separator(parent=info_parent)

    dpg.add_text(f"Patient Name: {patient_info['PatientFirstName']} {patient_info['PatientLastName']}", parent=info_parent, show=True)
    dpg.add_text(f"Patient Date of Birth: {patient_info['PatientDateOfBirth']}", parent=info_parent, show=True)
    dpg.add_text(f"Diagnosis: {utl.after_point(patient_info['Diagnosis'])}", parent=info_parent, show=True)
    if patient_info['ClinicianNotes'] != "":
        dpg.add_text(f"Notes: {patient_info['ClinicianNotes']}", parent=info_parent, show=True)
    dpg.add_separator(parent=info_parent)

    dpg.add_text(f"Impedance Status: {impedance_status}", parent=info_parent, show=True)
    dpg.configure_item(info_parent, show=True)

    return l

#--------------------------------------INDIVIDUAL TABS-----------------------------------------
def event_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    app_state['windows'][window_id]['Data'][tab_tag]['Signals'] = {'left': [], 'right': []}
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)   
    dpg.add_text(f"Total events: {len(signals)}", parent=tab_tag, tag = f"{tab_tag}_text_recordings")
    if len(signals)==0: return

    initial, final = DH.getEventsElectrodes(app_state['windows'][window_id]['Data'])
    
    power, tables = [], []
    bands = getBandsByTab(tab_tag)
    max_p = 0
    if not isinstance(initial, str): 
        for ch in initial:
            if ch in electrodes_names.keys():
                ch = electrodes_names[ch]
            else:
                electrodes_names[ch] = ch
        dpg.add_text(f"Electrodes | Left: {electrodes_names[initial[0]]} | Right: {electrodes_names[initial[1]]}", parent=tab_tag)
    else: 
        og = utl.after_point(signals[0]['Left']['Channel'])
        electrodes_names[og] = og
        dpg.add_text(f'{electrodes_names[og]}', parent=tab_tag)

    with dpg.group(label = f"{tab_tag}_group", parent=tab_tag, horizontal=True ):
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power (µVp)", tag=f"y_axis_{tab_tag}")

            for idx, signal in enumerate(signals):
                date = utl.parse_datetime(signal['DateInitial'])

                for side in ['Left', 'Right']:
                    sign = signal[side]
                    label = f"day {date.day:02d}/{date.month:02d}/{date.year} | {date.minute} | {side} | {signal['EventName']}"
                    x = sign['X']
                    y = sign['Y']
                    
                    # Create a unique series tag for each side
                    series_tag = f"{tab_tag}_series_{idx}_{side.lower()}"                                      

                    while len(app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side.lower()]) <= idx:
                        app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side.lower()].append(None)  # Fill with placeholders

                    app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side.lower()][idx] = sign

                    # Add the line series for each side
                    l = dpg.add_line_series(x, y, label=label, parent=f"y_axis_{tab_tag}", tag=series_tag)#, fill=[1.0, 0, 0, 0.5]) --> define transparency?
                    # dpg.bind_item_theme(l, 'default_line_thickness_theme')
                    signal_tags[series_tag] = True  # Track visibility

                    
                    tab_label = tab_tag
                    p = sign
                    power.append(y) 
                    max_p = max(max_p,np.max(p['Y']))      
                    series_label = series_tag
                    if not dpg.does_item_exist(f"{tab_label}_{series_label}"):
                        header = dpg.get_item_label(series_label)
                        dpg.add_collapsing_header(label = header, tag =f"{tab_label}_{series_label}", parent = tab_label)
                    else:
                        dpg.delete_item(f"{tab_label}_{series_label}", children_only=True)

                    #TABLE CONTENT
                    for band in bands.items():
                        info = extract_psd_features(p, band)
                        create_table(f"{tab_label}_{series_label}",f"{tab_label}_{series_label}_table", info, trial_label=band[0])

                    tables.append(f"{tab_label}_{series_label}_table")

            if not dpg.does_item_exist(f"{tab_label}_mean_metric"):
                dpg.add_collapsing_header(label = 'MEAN POWER', tag =f"{tab_label}_mean_metric", parent = tab_label)
            else:
                dpg.delete_item(f"{tab_label}_mean_metric", children_only=True)


            
            mean_power, std_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
            minus, plus = mean_power-std_power, mean_power+std_power
            s = dpg.add_shade_series(x,y1=minus,y2=plus,label = 'Std. Dev', parent=f"y_axis_{tab_tag}",tag=f"{tab_tag}_std")
            dpg.bind_item_theme(s,create_alpha_theme())

            m = dpg.add_line_series(x, mean_power, label="Mean Power", parent=f"y_axis_{tab_tag}", tag=f"{tab_tag}_mean")
            dpg.bind_item_theme(m, change_line_thickness(5))
            mean_power = {'Y': mean_power, 'X': p['X']}
            for band in bands.items():
                info = extract_psd_features(mean_power, band)
                create_table(f"{tab_label}_mean_metric",f"{tab_label}_mean_metric_table", info, trial_label=band[0])

            tables.append(f"{tab_label}_mean_metric_table")

        toggleDisplay2(signals,signal_tags,window_id,tab_tag)
                 
def timeline_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    dpg.add_text(f"Total days: {len(signals)}", parent=tab_tag)
    data = app_state['windows'][window_id]['Data']
    app_state['windows'][window_id]['Data'][tab_tag] = {'Signals': []}
    flag, mean = False, []
    evt = DH.getEventSummary(data)
    events = DH.getSignals(data,'Events')
    ocd_events = np.unique([event['EventName'] for event in events])
    ocd_events = ocd_events.tolist()
    # bands = DH.getTimelineBand(data)

    if 'Eventos' in evt.keys():
        for e in evt['Eventos']:
            event = f"{e['EventName']}:  {e['EventCount']}"
            dpg.add_text(event, parent=tab_tag)

    days = []
    with dpg.group(parent=tab_tag, horizontal=True):
        dpg.add_text('Events Legend: ')
        for oc in ocd_events:
            color_id = list(ocd_events).index(oc)
            ev = dpg.add_text(f"{oc} ")
            dpg.add_text("|")
            theme = change_text_color(color_id)
            dpg.bind_item_theme(ev, theme)
    with dpg.group(parent=tab_tag, horizontal=True):
        dpg.add_text('Signals Legend: ')
        left = dpg.add_text("Left ")
        dpg.add_text("|")
        right = dpg.add_text(" Right")
        lef = change_text_color(-1)
        dpg.bind_item_theme(left, lef)
        ri = change_text_color(-3)
        dpg.bind_item_theme(right, ri)


    initial, _ = DH.getEventsElectrodes(data)
    
    if not isinstance(initial, str): 
        for ch in initial:
            if ch in electrodes_names.keys():
                ch = electrodes_names[ch]
            else:
                electrodes_names[ch] = ch
        dpg.add_text(f"Electrodes | Left: {electrodes_names[initial[0]]} | Right: {electrodes_names[initial[1]]}", parent=tab_tag)
    else: 
        electrodes_names[initial] = initial
        dpg.add_text(f'{electrodes_names[initial]}', parent=tab_tag)

    with dpg.group(label = f"{tab_tag}_group" , parent=tab_tag, horizontal=True):
        
        dpg.add_group(width=600, tag=f"{tab_tag}_plot_group", horizontal=False)
        with dpg.plot(label=f"{mode} Signals", height=400, width=800, tag=plot_tag, parent=f"{tab_tag}_plot_group"):
            # dpg.bind_colormap(plot_tag, 0)
            legend = dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag=f"x_axis_{tab_tag}", scale = dpg.mvPlotScale_Time)
            y_left = dpg.add_plot_axis(dpg.mvYAxis, label="Mean LFP Power (µVp)", tag=f"y_axis_{tab_tag}_left")
            #y_right = dpg.add_plot_axis(dpg.mvYAxis, label="Stimulation Amplitude (mA)", tag=f"y_axis_{tab_tag}_right")

            dpg.set_axis_limits_auto(y_left)

            for idx, signal in enumerate(signals):
                app_state['windows'][window_id]['Data'][tab_tag]['Signals'].append(signal)

                date = utl.parse_datetime(signal['Date'])
                extra = DH.correctMissingTimeline(data, signal,'X_missing')[0]
                if extra['Right']['X_missing'] != [] and flag == False: 
                    flag = True
                for side in ['Left','Right']:   
                    sign = signal[side]
                    date = utl.parse_datetime(signal['Date'])
                    label_left = f"{side} - day {date.year}-{date.month:02d}-{date.day:02d}"
                
                    try:
                        x = [utl.convert_to_timestamp(val) for val in sign['X']]
                        y = [float(val) for val in sign['Y']]
                    except ValueError as e:
                        print(f"Error converting data for {label_left}: {e}")
                        continue  

                    # LFP power
                    series_tag = f"{tab_tag}_series_{idx}_{side.lower()}"
                    l=dpg.add_line_series(x, y, parent=y_left, tag=series_tag ,label=label_left)
                    if side=='Left':color_id=-1
                    else: color_id=-3
                    th = change_line_color(color_id)
                    dpg.bind_item_theme(l, th)
                    signal_tags[series_tag] = True  # Track visibility

                    if not dpg.does_item_exist(f"{tab_tag}_header"):
                        dpg.add_collapsing_header(tag=f"{tab_tag}_header", parent=tab_tag, label = 'Stream Metrics')

                    info = extract_timeline_features(sign)
                    create_table(f"{tab_tag}_header",f"{tab_tag}_table", info, trial_label=label_left)

                    mean.append(info)
        
        mean_dict = {}

        for key in mean[0].keys():
            values = [m[key] for m in mean]
            if isinstance(values[0], str):
                #its datetime in string
                values=[utl.extract_time_from_datetime_string(t) for t in values]
                mean_value = utl.extract_time(datetime.fromtimestamp(np.mean(values)))
                mean_value = {key: mean_value}
            else:
                mean_value = {key: np.mean(values,axis=0)}

            mean_dict = mean_dict | mean_value 

        create_table(f"{tab_tag}_header",f"{tab_tag}_table", mean_dict, trial_label=label_left)

        
        days = []
        for signal in signals: 
            date = utl.date2str(utl.parse_datetime(signal['Date']))
            days.append(date)

        days = np.unique(days).tolist()
        sides = ['Left','Right']

        for event in events:
            x_event = utl.convert_to_timestamp(event['DateInitial'])
            if event['DateInitial'][:10] < signals[0][side]['X'][0][:10]:
                continue
            label = event['EventName']
            color = list(ocd_events).index(label)
            e = dpg.add_inf_line_series(x=[x_event], parent = y_left)
            theme = change_inf_line_color(color)
            dpg.bind_item_theme(e, theme)

        dpg.configure_item(legend, show=False)

        with dpg.group(label = f"{tab_tag}_buttons", parent=f"{tab_tag}_group",):
            toggleVisibility(signal_tags,parent=tab_tag, group=f"{tab_tag}_buttons", user_data = window_id)
            with dpg.group(horizontal=True):
                with dpg.child_window(height=150, width=120):
                    dpg.add_text('By Day: ')
                    for day in days:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons", user_data=(day, window_id, tab_tag)) #check day
                with dpg.child_window(height=150, width=120):
                    dpg.add_text('By Hemisphere: ')
                    for day in sides:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons", user_data=(day, window_id, tab_tag)) #check hemisphere
                if len(ocd_events)>1:
                    with dpg.child_window(height=150, width=120):
                        dpg.add_text('By Event: ')
                        for ocd in ocd_events:
                            toggleType(signal_tags,parent=f"{tab_tag}_buttons", user_data=(ocd, window_id, tab_tag)) #check hemisphere
            #dpg.add_button(label='Normalize',callback=Volt2dB, user_data=(signal_tags,tab_tag),parent=f"{tab_tag}_buttons")
            dpg.add_slider_float(label = 'Remove Outlier', callback=RemoveTimelineOutliers,default_value=3.0,user_data=(tab_tag,signal_tags), width=100, min_value=0,max_value=100)
            if flag == True:
                dpg.add_text( 'Warning: There are missing points in Timeline', tag=f"{tab_tag}_wmp", parent=f"{tab_tag}_buttons")
                dpg.add_checkbox(label='Show missing points',parent=f"{tab_tag}_buttons", default_value=False, callback=changeTimelinePlot, user_data=(signal_tags, signals, data, y_left))

    add_timeline_features_buttons(tab_tag, signal_tags)
    add_correlation_buttons(tab_tag)

def setup_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    sense, calibration, artifacts = signals   
    
    def setup_off_tab():
        #SENSE CHANNEL TEST - STIMULATION OFF
        tab_tag_off = tab_tag + "_OFF"
        app_state['windows'][window_id]['Data'][tab_tag_off]= {'Signals': []}

        dpg.add_tab(label='Setup OFF', tag=tab_tag_off, parent=f"tab_bar_window_{window_id}", closable=True)
        with dpg.group(parent=tab_tag_off, horizontal=True):  # STIM OFF
            signal_tags = {}
            plot_tag = f"plot_{tab_tag_off}"
            with dpg.group():
                # First plot (Stimulation OFF)
                with dpg.plot(label=f"{mode} SETUP - Stimulation OFF", height=400, width=600, tag=plot_tag):
                    dpg.bind_colormap(plot_tag, 0)
                    dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast, no_buttons = True)
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag_off}")
                    dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag_off}")

                    parent = f"y_axis_{tab_tag_off}"
                    plot_td(sense, parent, tab_tag_off, signal_tags)

            toggleDisplay(sense, signal_tags, window_id, tab_tag_off)
        add_filters_buttons(tab_tag_off,signal_tags)
        add_features_buttons(tab_tag_off, signal_tags)
        add_correlation_buttons(tab_tag_off)

    def setup_on_tab():
        #CALIBRATION TEST - STIMULATION OFF
        tab_tag_on = tab_tag + "_ON"
        app_state['windows'][window_id]['Data'][tab_tag_on]= {'Signals': []}

        dpg.add_tab(label='Setup ON', tag=tab_tag_on, parent=f"tab_bar_window_{window_id}", closable=True)
        with dpg.group(parent=tab_tag_on, horizontal=True):  # STIM ON
            signal_tags = {}
            plot_tag = f"plot_{tab_tag_on}"
            with dpg.group():
                # Second plot (Stimulation ON)
                with dpg.plot(label=f"{mode} SETUP - Stimulation ON", height=400, width=600, tag=plot_tag):
                    dpg.bind_colormap(plot_tag, 0)
                    dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag_on}")
                    dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag_on}")

                    parent = f"y_axis_{tab_tag_on}"
                    plot_td(calibration, parent, tab_tag_on, signal_tags)

            toggleDisplay(calibration, signal_tags, window_id, tab_tag_on)
        add_filters_buttons(tab_tag_on,signal_tags)
        add_features_buttons(tab_tag_on, signal_tags)
        add_correlation_buttons(tab_tag_on)

    def setup_artifacts():
        types_artifacts, channels = [], []
        tab_tag_art = tab_tag + "_ARTIFACTS"
        app_state['windows'][window_id]['Data'][tab_tag_art]= {'Signals': []}
        bands = getBandsByTab(tab_tag_art)

        def toggle2(sender,app_data,user_data):
            _ = []
            ch = dpg.get_item_label(sender)
            for tag in signal_tags:
                if ch in tag:
                    dpg.configure_item(tag, show=app_data)
                flag = dpg.get_item_configuration(tag)['show']
                if flag:
                    _.append(tag)

            array = [dpg.get_value(t)[1] for t in _]
            mean = np.mean(array, axis=0)
            dpg.configure_item(f"{tab_tag_art}_mean",y=mean)

        dpg.add_tab(label='Setup ARTIFACTS', tag=tab_tag_art, parent=f"tab_bar_window_{window_id}", closable=True)
        with dpg.group(parent=tab_tag_art, horizontal=True):  # STIM ON
            signal_tags = {}
            plot_tag = f"plot_{tab_tag_art}"
            with dpg.plot(label=f"{mode} SETUP - Artifacts", height=400, width=600, tag=plot_tag):
                dpg.bind_colormap(plot_tag, 0)
                dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)") #tag=f"{tab_label}_x_axis"
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power (µVp)", tag=f"y_axis_{tab_tag_art}")

                for idx, signal in enumerate(artifacts):
                   
                    artifact = signal['Artifact']
                    label = f"{electrodes_names[signal['Channel']]} | {artifact}"

                    if isinstance(artifact,str): types_artifacts.append(f"{extract_artifact_type(artifact).upper()} Artifact")
                    # channel = electrodes_names[extract_channel_from_series_tag(signal['Channel'])].upper()
                    channel = electrodes_names[signal['Channel']].upper()
                    channels.append(channel) 
                    x = signal['X']
                    y = signal['Y']
                    
                    # Create a unique series tag for each side
                    series_tag = f"{tab_tag_art}_series_{channel}_{types_artifacts[-1]}_{idx}"
                                    
                    while len(app_state['windows'][window_id]['Data'][tab_tag_art]['Signals']) <= idx:
                        app_state['windows'][window_id]['Data'][tab_tag_art]['Signals'].append(None)  # Fill with placeholders

                    app_state['windows'][window_id]['Data'][tab_tag_art]['Signals'][idx] = signal

                    # Add the line series for each side
                    dpg.add_line_series(x, y, label=label, parent=f"y_axis_{tab_tag_art}", tag=series_tag)#, fill=[1.0, 0, 0, 0.5]) --> define transparency?
                    signal_tags[series_tag] = True  # Track visibility

                    if not dpg.does_item_exist(f"{series_tag}_header"): dpg.add_collapsing_header(tag=f"{series_tag}_header", parent=tab_tag_art,label=label)

                    for band in bands.items():
                        info = extract_psd_features(signal, band)
                        create_table(f"{series_tag}_header",f"{series_tag}_table", info, trial_label=band[0])

                
                mean_power = np.mean([signal['Y'] for signal in artifacts], axis = 0)
                m = dpg.add_line_series(x, mean_power, label="Mean Power", parent=f"y_axis_{tab_tag_art}", tag=f"{tab_tag_art}_mean")
                dpg.bind_item_theme(m, change_line_thickness(5))
                mean_power = {'Y': mean_power, 'X':x}

                if not dpg.does_item_exist(f"{tab_tag_art}_mean_metric"): dpg.add_collapsing_header(tag=f"{tab_tag_art}_mean_metric",parent=tab_tag_art,label = 'Mean')

                for band in bands.items():
                    info = extract_psd_features(mean_power, band)
                    create_table(f"{tab_tag_art}_mean_metric",f"{tab_tag_art}_mean_metric_table", info, trial_label=band[0])

            with dpg.group(tag=f"{tab_tag_art}_buttons", horizontal=True):
                types_artifacts = np.unique(types_artifacts)
                channels = np.unique(channels)
                if len(channels)>1: 
                    with dpg.group(): #channels
                        dpg.add_text('Channels: ')
                        for ch in channels:
                            dpg.add_checkbox(label=ch, callback=toggle2, default_value=True)
                if len(types_artifacts)>1:
                    with dpg.group(): #type of artifact
                        dpg.add_text('Artifacts: ')
                        for d in types_artifacts:
                            dpg.add_checkbox(label=d, callback=toggle2, default_value=True)
                with dpg.group():
                    dpg.add_text('Hemisphere: ')
                    for s in ['LEFT', 'RIGHT']:
                        dpg.add_checkbox(label=s, callback=toggle2, default_value=True)

    if sense:
        setup_off_tab()
    if calibration:
        setup_on_tab()
    if artifacts:
        setup_artifacts()

def survey_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):

    # 'Recordings Time Domain'
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    dpg.add_text(f"Total recordings: {len(signals)}", parent=tab_tag)
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"
            plot_td(signals,parent,tab_tag,signal_tags)

        toggleDisplay(signals, signal_tags, window_id, tab_tag)
    add_filters_buttons(tab_tag,signal_tags)
    add_features_buttons(tab_tag, signal_tags)
    add_correlation_buttons(tab_tag)


    def toggle(sender,app_data,user_data):
        what = user_data
        labels = [dpg.get_item_label(t) for t in line_tags]
        for l in labels:
            if what in l:
                dpg.configure_item(line_tags[labels.index(l)],show =app_data)

    # 'Recordings PSDs'
    new_tab_tag = f"{tab_tag}_psd"
    new_signals = getDatabyTag(tab_tag)[mode]['LFPMontage']
    new_plot_tag = f"{plot_tag}_psd"
    bands = getBandsByTab(tab_tag)

    dpg.add_tab(label=f"{mode} PSD", tag=new_tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    dpg.add_text(f"Total recordings: {len(signals)}", parent=new_tab_tag)
    line_tags, channels = [], []
    child = dpg.add_child_window(height=150, width=-1, parent=new_tab_tag)
    with dpg.group(parent=new_tab_tag, label = f"{new_tab_tag}_group", horizontal=True):
        signal_tags = {}
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=new_plot_tag):
            dpg.bind_colormap(new_plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag=f"x_axis_{new_tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µVp)", tag=f"y_axis_{new_tab_tag}")
            
            parent = f"y_axis_{new_tab_tag}"
            # plot_td(new_signals,parent,new_tab_tag,signal_tags)
            for _,signal in enumerate(new_signals):
                side = utl.after_point(signal['Hemisphere'])
                f = signal['LFPFrequency']
                m = signal['LFPMagnitude']
                channel = utl.after_point(signal['SensingElectrodes'])
                line_label = f"{channel} | {side}"
                line_tag = f"{new_tab_tag}_{channel}_{side}"
                line_tags.append(line_tag)
                channels.append(channel)
                artifact = utl.after_point(signal['ArtifactStatus'])
                dpg.add_line_series(f,m,label=line_label,parent=parent, tag = line_tag)
                tt = dpg.add_text(f"{channel}: {artifact}", parent=child)
                if artifact != 'ARTIFACT_NOT_PRESENT':
                    dpg.bind_item_theme(tt, change_text_color(1))
                signal_tags[line_tag] = True
                if 'PeakFrequencyInHertz' in signal:
                    peak = signal['PeakFrequencyInHertz']
                    peak_m = m[f.index(peak)]
                    dpg.add_scatter_series([peak],[peak_m],label=f"{channel} PEAK", parent=parent, tag =f"{line_tag}_peak")
                    line_tags.append(f"{new_tab_tag}_{channel}_{side}_peak")

                if not dpg.does_item_exist(f"{line_tag}_header"):
                    header = dpg.get_item_label(line_tag)
                    dpg.add_collapsing_header(label = header, tag =f"{line_tag}_header", parent = new_tab_tag)
                else:
                    dpg.delete_item(f"{line_tag}_header", children_only=True)

                #TABLE CONTENT
                p = {'X': f, 'Y': m}
                for band in bands.items():
                    info = extract_psd_features(p, band)
                    create_table(f"{line_tag}_header",f"{line_tag}_header_table", info, trial_label=band[0])


        channels = np.unique(channels)
        with dpg.child_window(height=150,width=120):
            for c in channels:
                dpg.add_checkbox(label=c, parent=f"{new_tab_tag}_group", callback=toggle, user_data=c, default_value=True)
        with dpg.child_window(height=150,width=120):
            for c in ['Left', 'Right', 'PEAK']:
                dpg.add_checkbox(label=c, parent=f"{new_tab_tag}_group", callback=toggle, user_data=c, default_value=True)

def streaming_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    dpg.add_text(f"Total recordings: {len(signals)}", parent=tab_tag)
    rdate = signals[0]['Date']

    dpg.add_text(f"Day: {rdate.day}/{rdate.month}/{rdate.year}", parent=tab_tag)

    Channel = signals[0]['Channel']
    stimulation = DH.getStreamingStimulation(getDatabyTag(tab_tag),signals[0]['Date'])
    
    if Channel in electrodes_names.keys():
        Channel = electrodes_names[Channel]
    else:
        electrodes_names[Channel] = Channel


    dpg.add_text(f"Channel: {extract_channel_from_series_tag(Channel).upper()}", parent=tab_tag)
    dpg.add_text(f"{stimulation}", parent=tab_tag)

    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):

        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"
            plot_td(signals,parent,tab_tag,signal_tags)

        toggleDisplay(signals, signal_tags, window_id, tab_tag)
    
    with dpg.group(parent=tab_tag, tag = f"{tab_tag}_add_events", horizontal=True):
        # interval_events(tab_tag,signal_tags)
        dpg.add_button(label='Insert Streaming Events', parent=f"{tab_tag}_add_events", callback = insert_events, user_data=(window_id, tab_tag, signal_tags))
        # dpg.add_button(label='Analyze Events', parent = f"{tab_tag}_add_events", callback=align_events,user_data=(tab_tag,signal_tags), tag=f"{tab_tag}_align",show=False)
    dpg.set_item_width
    add_filters_buttons(tab_tag,signal_tags)
    add_features_buttons(tab_tag, signal_tags)
    add_correlation_buttons(tab_tag)

def indefinite_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    dpg.add_text(f"Total recordings: {len(signals)}", parent=tab_tag, tag = f'{tab_tag}_info')
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"
            plot_td(signals,parent,tab_tag,signal_tags)

        toggleDisplay(signals, signal_tags, window_id, tab_tag)
        #button_parent = f"{tab_tag}_buttons"
        with dpg.group(parent=f"{tab_tag}_buttons"):
            dpg.add_spacer(height=10)  # Optional: Adds some spacing
            dpg.add_button(label='Segment Signal', show=True)
    with dpg.group(parent=tab_tag, tag = f"{tab_tag}_add_events", horizontal=True):
        # interval_events(tab_tag,signal_tags)
        dpg.add_button(label='Insert Streaming Events', parent=f"{tab_tag}_add_events", callback = insert_events, user_data=(window_id, tab_tag, signal_tags))
        # dpg.add_button(label='Analyze Events', parent = f"{tab_tag}_add_events", callback=align_events,user_data=(tab_tag,signal_tags), tag=f"{tab_tag}_align",show=False)
    
        
    add_filters_buttons(tab_tag,signal_tags)
    add_features_buttons(tab_tag, signal_tags)
    add_correlation_buttons(tab_tag)

def impedance_tab(Data, tab_tag):
    window_id = extract_window_id(tab_tag)
    mode = extract_mode(tab_tag)
    status, l, r = DH.getImpedance(Data)

    impedance = DH.getImpedance(Data)
    if not isinstance(impedance, str):
        impedance_status, l, r = impedance
    else: 
        impedance_status = impedance
        l=False

    def build_result_table(session_name, session_data):
        # Collect unique electrodes
        electrodes1 = sorted(set(entry["Electrode1"] for entry in session_data))
        electrodes2 = sorted(set(entry["Electrode2"] for entry in session_data))

        # Build a lookup dictionary
        result_dict = {
            (entry["Electrode2"], entry["Electrode1"]): entry["ResultValue"]
            for entry in session_data
        }

        with dpg.table(header_row=True, borders_innerH=True, borders_innerV=True,
                        borders_outerH=True, borders_outerV=True, resizable=True, policy=dpg.mvTable_SizingStretchProp):
            # Header row
            dpg.add_table_column(label="SenSight")
            for e1 in electrodes1:
                new_label = utl.after_underscore(e1)
                if new_label==e1:
                    new_label=utl.after_point(e1)
                dpg.add_table_column(label=new_label)

            # Rows
            for e2 in electrodes2:
                with dpg.table_row():
                    dpg.add_text(utl.after_underscore(e2))
                    for e1 in electrodes1:
                        val = result_dict.get((e2, e1), "")
                        if e2==e1: val = '-'
                        if val == "": val = result_dict.get((e1, e2), "")
                        dpg.add_text(str(val))

    def build_result_bar_graph(title, session_data):
        # Deduplicate electrode pairs and collect values
        unique_results = {}
        for entry in session_data:
            e1 = utl.after_underscore(utl.after_point(entry["Electrode1"]))
            e2 = utl.after_underscore(utl.after_point(entry["Electrode2"]))
            value = entry["ResultValue"]
            key = tuple(sorted([e1, e2]))
            if key not in unique_results and e1 != e2:
                try:
                    unique_results[key] = float(value)
                except (ValueError, TypeError):
                    unique_results[key] = 0.0  # Fallback if non-numeric

        labels = [f"{e1}-\n{e2}" for (e1, e2) in unique_results.keys()]
        if title == 'Monopolar':
            labels = [f"{_}" for (_, e2) in unique_results.keys()]
        
        values = list(unique_results.values())

        # Create the plot
        with dpg.plot(label=title, height=400, width=700):
            if title=='Monopolar':
                x_label = "Case - Electrode Pair"
            else: x_label = "Electrode Pair"
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label=x_label)
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Impedance (Ohm)")

            ticks = tuple((label, float(i)) for i, label in enumerate(labels))
            dpg.set_axis_ticks(x_axis, ticks)

            for i, val in enumerate(values):
                dpg.add_bar_series([float(i)], [val], parent=y_axis)

        
            plot = dpg.get_item_parent(y_axis)
            dpg.bind_colormap(plot, dpg.mvPlotColormap_Viridis)
                    
    with dpg.tab(tag = tab_tag, label = mode, parent=f"tab_bar_window_{window_id}", closable=True):
        dpg.add_text(f"Impedance Status: {impedance_status}", parent=tab_tag, show=True)
        with dpg.collapsing_header(label='Monopolar Left'): 
            build_result_table("Monopolar", l["Monopolar"])
            build_result_bar_graph("Monopolar", l["Monopolar"])

        with dpg.collapsing_header(label='Monopolar Right'):
            build_result_table("Monopolar", r["Monopolar"])
            build_result_bar_graph("Monopolar", r["Monopolar"])

        with dpg.collapsing_header(label='Bipolar Left'): 
            build_result_table("Bipolar", l["Bipolar"])
            build_result_bar_graph("Bipolar", l["Bipolar"])

        with dpg.collapsing_header(label='Bipolar Right'): 
            build_result_table("Bipolar", r["Bipolar"])
            build_result_bar_graph("Bipolar", r["Bipolar"])

#--------------------------------------COMBINED TABS--------------------------------------------
def comb_event_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags):
    
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    power, tables = [], []
    max_p = 0
    bands = getBandsByTab(tab_tag)
    files = app_state['windows'][window_id]['Files']
    all_signals, all_mean = [], {}
    for file in files: 
        data = file['Data']
        initial, _ = DH.getEventsElectrodes(data)
        if not isinstance(initial, str): 
            for ch in initial:
                if ch in electrodes_names.keys():
                    ch = electrodes_names[ch]
                else:
                    electrodes_names[ch] = ch
            dpg.add_text(f"Electrodes {DH.getSessionDate(data)} | Left: {electrodes_names[initial[0]]} | Right: {electrodes_names[initial[1]]}", parent=tab_tag)
        else: 
            electrodes_names[initial] = initial
            dpg.add_text(f'{DH.getSessionDate(data)}: {electrodes_names[initial]}', parent=tab_tag)

    
    plotted = []
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):

        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µVp)", tag=f"y_axis_{tab_tag}")
            ids = []
            tab_label = tab_tag
            
            for idx, file in enumerate(files):
                app_state['windows'][window_id]['Files'][idx]['Data'][tab_tag] = {}
                
                if mode in file['Modes']: 
                    app_state['windows'][window_id]['Files'][idx]['Data'][tab_tag]['Signals'] = []
                    signals = DH.getSignals(file['Data'],mode)

                    file['Data'][tab_tag]= {'Signals': []}
                    if len(signals) == 0: ids.append(idx)

            if len(ids) == len(files): return #No file has a single event

            for idx, file in enumerate(files):
                app_state['windows'][window_id]['Files'][idx]['Data'][tab_tag] = {}
                if idx in ids: continue
                
                if mode in file['Modes']: 
                    app_state['windows'][window_id]['Files'][idx]['Data'][tab_tag]['Signals'] = []
                    signals = DH.getSignals(file['Data'],mode)

                    file['Data'][tab_tag]= {'Signals': []}

                    rdate = signals[0]['DateInitial']
                    rdate = utl.parse_datetime(rdate)
                    dpg.add_text(f"Day: {rdate.day}/{rdate.month}/{rdate.year}", parent=tab_tag)

                    for sdx, signal in enumerate(signals):

                        all_signals.append(signal)
                        
                        date = utl.parse_datetime(signal['DateInitial'])
                        if plotted != []:
                            if date in plotted:
                                continue
                        else: plotted.append(date)
                        app_state['windows'][window_id]['Files'][idx]['Data'][tab_tag]['Signals'].append({'left': [], 'right': []})

                        for side in ['Left', 'Right']:
                            
                            sign = signal[side]
                            label = f"day {date.day:02d}/{date.month:02d} | {date.minute:02d} | {side} | {signal['EventName']}"
                            x = sign['X']
                            y = sign['Y']
                            
                            # Create a unique series tag for each side
                            series_tag = f"{tab_tag}_file_{idx}_series_{sdx}_{side.lower()}"
                            app_state['windows'][window_id]['Files'][idx]['Data'][tab_tag]['Signals'][sdx][side.lower()] = sign

                            # Add the line series for each side
                            dpg.add_line_series(x, y, label=label, parent=y_axis, tag=series_tag)#, fill=[1.0, 0, 0, 0.5]) --> define transparency?
                            signal_tags[series_tag] = True  # Track visibility

                            p = sign
                            power.append(y) 
                            max_p = max(max_p,np.max(p['Y']))      
                            series_label = series_tag

                            if not dpg.does_item_exist(f"{tab_label}_grouped"):
                                dpg.add_tree_node(tag=f"{tab_label}_grouped",
                                    label="Grouped Streams",
                                    parent=tab_label,
                                    default_open=True
                                ) 

                            if not dpg.does_item_exist(f"{tab_label}_{side}_all_mean"):
                                dpg.add_collapsing_header(label = f'All Mean Power - {side}', tag =f"{tab_label}_{side}_all_mean", parent = f"{tab_label}_grouped")
                                tables.append(f"{tab_label}_{side}_all_mean_table")

                            if not dpg.does_item_exist(f"{tab_label}_{side}_{signal['EventName']}"):
                                dpg.add_collapsing_header(label = f"All {signal['EventName']}s - {side}", tag =f"{tab_label}_{side}_{signal['EventName']}", parent = f"{tab_label}_grouped")
                                tables.append(f"{tab_label}_{side}_{signal['EventName']}_table")

                            if not dpg.does_item_exist(f"{tab_label}_individuals"):
                                dpg.add_tree_node(tag=f"{tab_label}_individuals",
                                    label="Individual Streams",
                                    parent=tab_label,
                                    default_open=True
                                )   

                            if not dpg.does_item_exist(f"{tab_label}_{series_label}"):
                                header = dpg.get_item_label(series_label)
                                dpg.add_collapsing_header(label = header, tag =f"{tab_label}_{series_label}", parent = f"{tab_label}_individuals")
                            else:
                                dpg.delete_item(f"{tab_label}_{series_label}", children_only=True)

                            #TABLE CONTENT
                            for band in bands.items():
                                info = extract_psd_features(p, band)
                                temp = info['Mean Power (mean, std. dev)']
                                # temp = info['Peak Power (power, frequency)']
                                if not isinstance(temp,(int,float)): all_mean[band[0]] = temp[-1]
                                else: all_mean[band[0]]=temp
                                create_table(f"{tab_label}_{series_label}",f"{tab_label}_{series_label}_table", info, trial_label=band[0])

                            create_table(f"{tab_label}_{side}_all_mean",f"{tab_label}_{side}_all_mean_table", all_mean, trial_label=header)
                            create_table(f"{tab_label}_{side}_{signal['EventName']}",f"{tab_label}_{side}_{signal['EventName']}_table", all_mean, trial_label=header)

                            tables.append(f"{tab_label}_{series_label}_table")
       

            if not dpg.does_item_exist(f"{tab_label}_mean_metric"):
                dpg.add_collapsing_header(label = 'MEAN POWER', tag =f"{tab_label}_mean_metric", parent = tab_label)
            else:
                dpg.delete_item(f"{tab_label}_mean_metric", children_only=True)


            mean_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
            m = dpg.add_line_series(x, mean_power, label="Mean Power", parent=f"y_axis_{tab_tag}", tag=f"{tab_tag}_mean")
            dpg.bind_item_theme(m, change_line_thickness(5))
            mean_power = {'Y': mean_power, 'X': p['X']}
            for band in bands.items():
                info = extract_psd_features(mean_power, band)
                create_table(f"{tab_label}_mean_metric",f"{tab_label}_mean_metric_table", info, trial_label=band[0])

            tables.append(f"{tab_label}_mean_metric_table")

        toggleDisplay2(all_signals,signal_tags,window_id,tab_tag)
        def show_mean(sender,app_data):
            dpg.configure_item(f"{tab_tag}_mean",show=app_data)

        dpg.add_checkbox(label='Mean Visibility', default_value=True, callback=show_mean, parent=f"{tab_tag}_buttons")

def comb_streaming_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):

        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"

            for idx, file in enumerate(files):
                if mode in file['Modes']: 
                    signals = DH.getSignals(file['Data'],mode)
                    file['Data'][tab_tag]= {'Signals': []}
                    rdate = signals[0]['Date']
                    channel = extract_channel_from_series_tag(signals[0]['Channel'])
                    dpg.add_text(f"Day: {rdate.day}/{rdate.month}/{rdate.year} | Channel: {channel.upper()}", parent=tab_tag)
                    plot_td(signals,parent,tab_tag,signal_tags,files=idx)

        toggleDisplay(signals, signal_tags, window_id, tab_tag)
    
    with dpg.group(parent=tab_tag, tag = f"{tab_tag}_add_events", horizontal=True):
        interval_events(tab_tag,signal_tags)
        dpg.add_button(label='Analyze Streaming Events', parent=f"{tab_tag}_add_events", callback = insert_events, user_data=(window_id, tab_tag, signal_tags))
    
    add_filters_buttons(tab_tag,signal_tags)
    add_features_buttons(tab_tag, signal_tags)

def comb_setup_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags): 

    def setup_plot(mode, tab_tag, type):
        signals = None
        plot_tag = f"plot_{tab_tag}"
        dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
        with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):
            signal_tags = {}
            with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
                dpg.bind_colormap(plot_tag, 0)
                dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
                dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag}")
                
                parent = f"y_axis_{tab_tag}"
                for idx, file in enumerate(files):
                    file['Data'][tab_tag]= {'Signals': []}
                    if 'Setup' in file['Modes']: 
                        signals = DH.getSignals(file['Data'],'Setup')[type]
                        plot_td(signals,parent,tab_tag,signal_tags, files=idx)

            toggleDisplay(signals, signal_tags, window_id, tab_tag)
        add_filters_buttons(tab_tag,signal_tags)
        add_features_buttons(tab_tag, signal_tags)
        add_correlation_buttons(tab_tag)

    for idx, ext in enumerate(['OFF','ON']):
        new_mode = mode + ' ' + ext
        new_tag = tab_tag + '_' + ext
        setup_plot(new_mode, new_tag, idx)

    def setup_artifacts():
        types_artifacts, channels, days = [], [], []
        tab_tag_art = tab_tag + "_ARTIFACTS"
        bands = getBandsByTab(tab_tag_art)

        def toggle2(sender,app_data,user_data):
            _ = []
            ch = dpg.get_item_label(sender)
            for tag in signal_tags:
                if ch in tag:
                    dpg.configure_item(tag, show=app_data)
                flag = dpg.get_item_configuration(tag)['show']
                if flag:
                    _.append(tag)

            array = [dpg.get_value(t)[1] for t in _]
            mean = np.mean(array, axis=0)
            dpg.configure_item(f"{tab_tag_art}_mean",y=mean)

        dpg.add_tab(label='Setup ARTIFACTS', tag=tab_tag_art, parent=f"tab_bar_window_{window_id}", closable=True)
        with dpg.group(parent=tab_tag_art, horizontal=True):  # STIM ON
            signal_tags = {}
            plot_tag = f"plot_{tab_tag_art}"
            with dpg.plot(label=f"{mode} SETUP - Artifacts", height=400, width=600, tag=plot_tag):
                dpg.bind_colormap(plot_tag, 0)
                dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)") #tag=f"{tab_label}_x_axis"
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power (µVp)", tag=f"y_axis_{tab_tag_art}")

                for fdx, file in enumerate(files):
                    file['Data'][tab_tag_art]= {'Signals': []}
                    date = utl.parse_datetime(file['Data']['Device']['SessionDate'])
                    date = f"{date.day:02d}/{date.month:02d}/{date.year}"
                    days.append(date)
                    if 'Setup' in file['Modes']: 
                        artifacts = DH.getSignals(file['Data'],'Setup')[2]

                        for idx, signal in enumerate(artifacts):
                        
                            artifact = signal['Artifact']
                            label = f"{signal['Channel']} | {artifact}"
                            if extract_type_window(window_id) == 'Combined':
                                label = label + f' {date}'

                            if isinstance(artifact,str): types_artifacts.append(f"{extract_artifact_type(artifact).upper()} Artifact")
                            channel = electrodes_names[signal['Channel']].upper()
                            channels.append(channel) 
                            x = signal['X']
                            y = signal['Y']
                            
                            # Create a unique series tag for each side
                            series_tag = f"{tab_tag_art}_series_{channel}_{types_artifacts[-1]}_{idx}_{date}"

                            file['Data'][tab_tag_art]['Signals'].append(signal)
                            # Add the line series for each side
                            dpg.add_line_series(x, y, label=label, parent=f"y_axis_{tab_tag_art}", tag=series_tag)#, fill=[1.0, 0, 0, 0.5]) --> define transparency?
                            signal_tags[series_tag] = True  # Track visibility

                            if not dpg.does_item_exist(f"{series_tag}_header"): dpg.add_collapsing_header(tag=f"{series_tag}_header", parent=tab_tag_art,label=label)

                            for band in bands.items():
                                info = extract_psd_features(signal, band)
                                create_table(f"{series_tag}_header",f"{series_tag}_table", info, trial_label=band[0])

                mean_power = np.mean([signal['Y'] for signal in artifacts], axis = 0)
                dpg.add_scatter_series(x, mean_power, label="Mean Power", parent=f"y_axis_{tab_tag_art}", tag=f"{tab_tag_art}_mean")
                mean_power = {'Y': mean_power, 'X':x}

                if not dpg.does_item_exist(f"{tab_tag_art}_mean_metric"): dpg.add_collapsing_header(tag=f"{tab_tag_art}_mean_metric",parent=tab_tag_art,label = 'Mean')

                for band in bands.items():
                    info = extract_psd_features(mean_power, band)
                    create_table(f"{tab_tag_art}_mean_metric",f"{tab_tag_art}_mean_metric_table", info, trial_label=band[0])

                
            with dpg.group(tag=f"{tab_tag_art}_buttons"):
                with dpg.group(horizontal=True):
                    types_artifacts = np.unique(types_artifacts)
                    channels = np.unique(channels)
                    days = np.unique(days)
                    if len(channels)>1: 
                        with dpg.group(): #channels
                            dpg.add_text('Channels: ')
                            for ch in channels:
                                dpg.add_checkbox(label=ch, callback=toggle2, default_value=True)
                    if len(types_artifacts)>1:
                        with dpg.group(): #type of artifact
                            dpg.add_text('Artifacts: ')
                            for d in types_artifacts:
                                dpg.add_checkbox(label=d, callback=toggle2, default_value=True)
                with dpg.group(horizontal=True):
                    if len(days)>1:
                        with dpg.group(): #type of artifact
                            dpg.add_text('Days: ')
                            for d in days:
                                dpg.add_checkbox(label=d, callback=toggle2, default_value=True)

                    with dpg.group():
                        dpg.add_text('Hemisphere: ')
                        for s in ['LEFT', 'RIGHT']:
                            dpg.add_checkbox(label=s, callback=toggle2, default_value=True)
    
    setup_artifacts()
       
def comb_survey_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags): 
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):

        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"

            for idx, file in enumerate(files):
                if mode in file['Modes']: 
                    signals = DH.getSignals(file['Data'],mode)
                    file['Data'][tab_tag]= {'Signals': []}
                    rdate = signals[0]['Date']
                    dpg.add_text(f"Day: {rdate.day}/{rdate.month}/{rdate.year}", parent=tab_tag)
                    plot_td(signals,parent,tab_tag,signal_tags,files=idx)

        
        toggleDisplay(signals, signal_tags, window_id, tab_tag)
    
    with dpg.group(parent=tab_tag, tag = f"{tab_tag}_add_events", horizontal=True):
        interval_events(tab_tag,signal_tags)
        dpg.add_button(label='Analyze Streaming Events', parent=f"{tab_tag}_add_events", callback = insert_events, user_data=(window_id, tab_tag, signal_tags))
    
    add_filters_buttons(tab_tag,signal_tags)
    add_features_buttons(tab_tag, signal_tags)

    # 'Recordings PSDs'
    new_tab_tag = f"{tab_tag}_psd"
    new_plot_tag = f"{plot_tag}_psd"
    bands = getBandsByTab(tab_tag)

    def toggle(sender,app_data,user_data):
        what = user_data
        labels = [dpg.get_item_label(t) for t in line_tags]
        for l in labels:
            if what in l:
                dpg.configure_item(line_tags[labels.index(l)],show =app_data)


    dpg.add_tab(label=f"{mode} PSD", tag=new_tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    dpg.add_text(f"Total recordings: {len(signals)}", parent=new_tab_tag)
    line_tags, channels = [], []
    child = dpg.add_child_window(height=150, width=-1, parent=new_tab_tag)
    with dpg.group(parent=new_tab_tag, label = f"{new_tab_tag}_group", horizontal=True):
        signal_tags, dates = {}, []
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=new_plot_tag):
            dpg.bind_colormap(new_plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag=f"x_axis_{new_tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µVp)", tag=f"y_axis_{new_tab_tag}")
            
            parent = f"y_axis_{new_tab_tag}"
            # plot_td(new_signals,parent,new_tab_tag,signal_tags)
            for idx, file in enumerate(files):
                if mode in file['Modes']: 
                    new_signals = file['Data'][mode]['LFPMontage']
                    date = file['Data']['Device']['SessionDate'][:10]
                    dates.append(date)
                for _,signal in enumerate(new_signals):
                    side = utl.after_point(signal['Hemisphere'])
                    f = signal['LFPFrequency']
                    m = signal['LFPMagnitude']
                    channel = utl.after_point(signal['SensingElectrodes'])
                    line_label = f"{date} | {channel} | {side}"
                    line_tag = f"{file['name']}_{new_tab_tag}_{channel}_{side}"
                    line_tags.append(line_tag)
                    channels.append(channel)
                    artifact = utl.after_point(signal['ArtifactStatus'])
                    dpg.add_line_series(f,m,label=line_label,parent=parent, tag = line_tag)

                    artifact_info = f"{date}_{tab_tag}"
                    if dpg.does_item_exist(artifact_info):
                        tt = dpg.add_text(f"{channel}: {artifact}", parent=artifact_info)
                    else:
                        dpg.add_collapsing_header(label = date, tag=artifact_info, parent=child)
                        tt = dpg.add_text(f"{channel}: {artifact}", parent=artifact_info)

                    if artifact != 'ARTIFACT_NOT_PRESENT':
                        dpg.bind_item_theme(tt, change_text_color(1))
                    signal_tags[line_tag] = True
                    if 'PeakFrequencyInHertz' in signal:
                        peak = signal['PeakFrequencyInHertz']
                        peak_m = m[f.index(peak)]
                        dpg.add_scatter_series([peak],[peak_m],label=f"{channel} PEAK", parent=parent, tag =f"{line_tag}_peak")
                        line_tags.append(f"{line_tag}_peak")

                    if not dpg.does_item_exist(f"{line_tag}_header"):
                        header = dpg.get_item_label(line_tag)
                        dpg.add_collapsing_header(label = header, tag =f"{line_tag}_header", parent = new_tab_tag)
                    else:
                        dpg.delete_item(f"{line_tag}_header", children_only=True)

                    #TABLE CONTENT
                    p = {'X': f, 'Y': m}
                    for band in bands.items():
                        info = extract_psd_features(p, band)
                        create_table(f"{line_tag}_header",f"{line_tag}_header_table", info, trial_label=band[0])

        channels = np.unique(channels)
        dates = np.unique(dates).tolist()
        if len(dates)>1:
            with dpg.child_window(height=150,width=120, tag =f"{new_tab_tag}day" ):
                dpg.add_text('By Day:', parent=f"{new_tab_tag}day" )
                for d in dates:
                    dpg.add_checkbox(label=d, parent=f"{new_tab_tag}_group", callback=toggle, user_data=d, default_value=True)
        with dpg.child_window(height=150,width=120):
            dpg.add_text('By Channel:')
            for c in channels:
                dpg.add_checkbox(label=c, parent=f"{new_tab_tag}_group", callback=toggle, user_data=c, default_value=True)
        with dpg.child_window(height=150,width=120):
            dpg.add_text('By Hemisphere:')
            for c in ['Left', 'Right', 'PEAK']:
                dpg.add_checkbox(label=c, parent=f"{new_tab_tag}_group", callback=toggle, user_data=c, default_value=True)

def comb_indefinite_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags): 
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):

        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"

            for idx, file in enumerate(files):
                if mode in file['Modes']: 
                    signals = DH.getSignals(file['Data'],mode)
                    file['Data'][tab_tag]= {'Signals': []}
                    rdate = signals[0]['Date']
                    plot_td(signals,parent,tab_tag,signal_tags,files=idx)
                else: 
                    app_state['windows'][window_id]['Files'][idx]['Data'][tab_tag] = []
        
        toggleDisplay(signals, signal_tags, window_id, tab_tag)
    
    with dpg.group(parent=tab_tag, tag = f"{tab_tag}_add_events", horizontal=True):
        interval_events(tab_tag,signal_tags)
        dpg.add_button(label='Analyze Streaming Events', parent=f"{tab_tag}_add_events", callback = insert_events, user_data=(window_id, tab_tag, signal_tags))

    add_filters_buttons(tab_tag,signal_tags)
    add_features_buttons(tab_tag, signal_tags)

def comb_timeline_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    files = app_state['windows'][window_id]['Files']
    flag = False
    datas, temp_signals, events_tags, ocd_events = [], [], [], []
    for file in files: 
        data = file['Data']
        initial, _ = DH.getEventsElectrodes(data)
        date = file['Data']['Device']['SessionDate'][:10]
        header = f"{date}_{tab_tag}"
        dpg.add_collapsing_header(tag=header,label=date,parent=tab_tag)
        if not isinstance(initial, str): 
            for ch in initial:
                if ch in electrodes_names.keys():
                    ch = electrodes_names[ch]
                else:
                    electrodes_names[ch] = ch
            dpg.add_text(f"Electrodes {DH.getSessionDate(data)} | Left: {electrodes_names[initial[0]]} | Right: {electrodes_names[initial[1]]}", parent=header)
            f = DH.info_electrodes(data)['Sense_frequency']
            if f != '': 
                f1, f2 = f-2.5,f+2.5
                dpg.add_text(f"Sensing Band: [{f1}, {f2}] Hz", parent=header)
    
        else: 
            electrodes_names[initial] = initial
            dpg.add_text(f'{DH.getSessionDate(data)}: {electrodes_names[initial]}', parent=header)

        evt = DH.getEventSummary(data)
        if 'Eventos' in evt.keys():
            for e in evt['Eventos']:
                event = f"{e['EventName']}:  {e['EventCount']}"

        events = DH.getSignals(file['Data'],'Events')       
        for edx, event in enumerate(events):
            ocd_events.append(event['EventName'])

    days = []
    
    #Signals legend
    with dpg.group(parent=tab_tag, horizontal=True):
        dpg.add_text('Signals Legend: ')
        left = dpg.add_text("Left ")
        dpg.add_text("|")
        right = dpg.add_text(" Right")
        lef = change_text_color(-1)
        dpg.bind_item_theme(left, lef)
        ri = change_text_color(-3)
        dpg.bind_item_theme(right, ri)


    ocd_events = np.unique(ocd_events).tolist()
    with dpg.group(parent=tab_tag, horizontal=True):
        dpg.add_text('Events Legend: ')
        for oc in ocd_events:
            color_id = list(ocd_events).index(oc)
            ev = dpg.add_text(f"{oc} ")
            dpg.add_text("|")
            theme = change_text_color(color_id)
            dpg.bind_item_theme(ev, theme)
        
    with dpg.group(parent=tab_tag, tag = f"{tab_tag}_group", horizontal=True):

        dpg.add_group(width=600, tag=f"{tab_tag}_plot_group", horizontal=False)
        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag, parent=f"{tab_tag}_plot_group"):
            dpg.bind_colormap(plot_tag, 0)
            legend = dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}", scale=dpg.mvPlotScale_Time)
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Mean LFP Power (µVp)", tag=f"y_axis_{tab_tag}")
           
            for idx, file in enumerate(files):
                app_state['windows'][window_id]['Files'][idx]['Data'][tab_tag] = {}
                
                if mode in file['Modes']: 
                    signals = DH.getSignals(file['Data'],mode)

                    events = DH.getSignals(file['Data'],'Events')

                    file['Data'][tab_tag]= {'Signals': []}
                    rdate = signals[0]['Date']
                    rdate = utl.date2str(utl.parse_datetime(rdate))

                    for sdx, signal in enumerate(signals):
                        extra = DH.correctMissingTimeline(file['Data'], signal,'X_missing')[0]
                        signal = DH.correctMissingTimeline(file['Data'], signal,'X')[0]
                        temp_signals.append(signal)
                        if extra['Right']['X_missing'] != []:
                            datas.append(file['Data'])
                            flag = True
                            
                        else: datas.append(None)

                        signal_tag = f"{tab_tag}_file_{idx}_series_{sdx}"
                        date = utl.date2str(utl.parse_datetime(signal['Date']))
                        app_state['windows'][window_id]['Files'][idx]['Data'][tab_tag]['Signals'].append({'Date':date,'Left': [], 'Right': []})
                        
                        days.append(date)
                            
                        for side in ['Left', 'Right']:
                            sign = signal[side]
                            label_left = f"{side} - day {date}"
                            
                            try:
                                
                                x = [utl.convert_to_timestamp(val) for val in sign['X']]
                                y = [float(val) for val in sign['Y']]
                                sign['X'] = x
                            except ValueError as e:
                                print(f"Error converting data for {label_left}: {e}")
                                continue
                            
                            # Create a unique series tag for each side
                            series_tag = f"{signal_tag}_{side.lower()}"
                            app_state['windows'][window_id]['Files'][idx]['Data'][tab_tag]['Signals'][sdx][side] = sign

                            labels = [dpg.get_item_label(k) for k in list(signal_tags.keys())]
                            if label_left not in labels:
                                # Add the line series for each side
                                l = dpg.add_line_series(x, y, label=label_left, parent=y_axis, tag=series_tag)#, fill=[1.0, 0, 0, 0.5]) --> define transparency?
                                if side=='Left':color_id=-1
                                else: color_id=-3
                                th = change_line_color(color_id)
                                dpg.bind_item_theme(l, th)
                                signal_tags[series_tag] = True  # Track visibility

                            if not dpg.does_item_exist(f"{tab_tag}_header"):
                                dpg.add_collapsing_header(tag=f"{tab_tag}_header", parent=tab_tag, label = 'Stream Metrics')

                            info = extract_timeline_features(sign)
                            create_table(f"{tab_tag}_header",f"{tab_tag}_table", info, trial_label=label_left)

                    for edx, event in enumerate(events):
                        x_event = utl.convert_to_timestamp(event['DateInitial'])
                        if event['DateInitial'][:10]<rdate[:10]:
                            print(event['DateInitial'])
                            continue
                        label = event['EventName']
                        e_tag = f"{tab_tag}_{edx}_{idx}"
                        try:
                            color = list(ocd_events).index(label)
                        except Exception: 
                            ocd_events.append(label)
                            color = list(ocd_events).index(label)
                        t = dpg.add_inf_line_series(x=[x_event],parent = y_axis, tag =f"{tab_tag}_{edx}_{idx}", label=label)
                        events_tags.append([e_tag,idx])
                        theme = change_inf_line_color(color)
                        dpg.bind_item_theme(t, theme)

                dpg.add_text(f"Total days: {len(days)}", parent=header)
                dpg.add_text(f"Timezone/offset: {DH.extract_dict_offset(data)}", parent=header)
                dpg.add_separator(parent=header)
        days = np.unique(days).tolist()
        sides = ['Left','Right']
        dpg.configure_item(legend,show=False)

        with dpg.group(label = f"{tab_tag}_buttons", parent=f"{tab_tag}_group"):
            toggleVisibility(signal_tags,parent=tab_tag, group=f"{tab_tag}_buttons", user_data = window_id)
            with dpg.group(horizontal=True):
                with dpg.child_window(height=150, width=150):
                    dpg.add_text('By day: ')
                    for day in days:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons", user_data=(day, window_id, tab_tag)) #check day
                with dpg.child_window(height=150, width=150):
                    dpg.add_text('By hemisphere: ')
                    for day in sides:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons", user_data=(day, window_id, tab_tag))
            dpg.add_slider_float(label = 'Remove Outlier RMS', callback=RemoveTimelineOutliers,default_value=3.0,user_data=(tab_tag,signal_tags), width=100, min_value=0,max_value=100)
            if flag == True:
                dpg.add_text( 'Warning: There are missing points in Timeline', tag=f"{tab_tag}_wmp", parent=f"{tab_tag}_buttons")
                dpg.add_checkbox(label='Show missing points',parent=f"{tab_tag}_buttons", default_value=False, callback=changeTimelinePlot, user_data=(signal_tags, temp_signals, datas, y_axis))

            dpg.add_button(label = 'Analyze Events', callback=AnalyzeTimelineEvents, user_data=(tab_tag, events_tags, signal_tags),parent=f"{tab_tag}_buttons")
            
        add_timeline_features_buttons(tab_tag, signal_tags)

def comb_impedance_tab(mode,tab_tag,window_id,files):
    dict_impedance = {}
    dict_impedance['Left'], dict_impedance['Right'] = {}, {}
    dates = []
    for _, file in enumerate(files):
        if mode in file['Modes']:
            Data = file['Data']
            date = Data['Device']['SessionDate']
            dates.append(date[:10])
            status, l, r = DH.getImpedance(Data)
            impedance = DH.getImpedance(Data)
            if not isinstance(impedance, str): #preenchido
                _, l, r = impedance
                dict_impedance['Left'][date] = l
                dict_impedance['Right'][date] = r
            else: 
                l=False
    
    name_dates = sorted(dates)

    if len(dict_impedance['Left'])>1: print('line graph')
    else:
        impedance_tab(Data,tab_tag)
        return
    
    sorted_left = {key: value for key, value in sorted(dict_impedance['Left'].items())}
    sorted_right = {key: value for key, value in sorted(dict_impedance['Right'].items())}
    # dict_impedance['Left'], dict_impedance['Right'] = sorted_left, sorted_right

    with dpg.tab(tag = tab_tag, label = mode, parent=f"tab_bar_window_{window_id}", closable=True):
        dpg.add_text(f"Impedance Status: {status}", parent=tab_tag, show=True)

        def impedance_header(read,side):
            if side == 'Left': 
                array = sorted_left
            else:
                array = sorted_right

            with dpg.collapsing_header(label=f"{read} {side}"): 
                raw_values, labels = [], []
                for _,id in array.items():
                    for v in id[read]:
                        value= v['ResultValue']
                        label = utl.after_underscore(utl.after_point(v["Electrode2"]))
                        if read == 'Bipolar':
                            label = utl.after_underscore(utl.after_point(v["Electrode2"])) + '- \n' + label
                        raw_values.append(value)
                        labels.append(label)

                with dpg.plot(label=f"{read} {side}",width=800,height=400):
                    dpg.add_plot_legend(outside=True,location=dpg.mvPlot_Location_North)
                    x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Day")
                    y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Impedance (Ohm)")
                    ticks = tuple((labels[i],float(i)) for i in range(len(labels)))
                    dpg.set_axis_ticks(x_axis,ticks)
                    dpg.add_bar_group_series(raw_values, name_dates, group_size=len(name_dates),parent=y_axis)

        impedance_header('Monopolar', 'Left')
        impedance_header('Monopolar', 'Right')
        impedance_header('Bipolar', 'Left')
        impedance_header('Bipolar', 'Right')

#-----------------------------------COMBINED ANALISYS-------------------------------------
def create_multiple_window():
    window_id = len(app_state["windows"])  # Unique ID
    app_state["windows"][window_id] = {"Files": []}  # Track window state
    app_state['windows'][window_id]['Bands'] = global_bands

    warning_text = ''

    def file_dialog_callback(sender, app_data, user_data):
        window_id = user_data  # Get window-specific ID
        files = app_data['selections']  # Dict { "full_path": "file_name" }
        for file in files:
            app_state["windows"][window_id]["Files"].append(
                {"name": file, "path": files[file]})
        dpg.set_item_label(f"window_{window_id}", f"Combined {window_id}")
        update_file_list(window_id)
    
    def remove_file_callback(sender,app_data,user_data):
        window_id, file_index = user_data
        del app_state['windows'][window_id]['Files'][file_index]
        update_file_list(window_id)

    def update_file_list(window_id):
        dpg.delete_item(f"file_list_group_{window_id}", children_only = True)

        files = app_state['windows'][window_id]['Files']
        if not files:
            if not dpg.does_item_exist(f"file_list_{window_id}"):
                dpg.add_text('No file selected', parent=f"file_list_group_{window_id}", tag =f"file_list_{window_id}")
            
            dpg.configure_item(f"open_file_btn_{window_id}", show=False)
            dpg.configure_item(f"mode_list_group_{window_id}", show=False)
            dpg.configure_item(f"modes_{window_id}", show = False)
        else:
            dpg.configure_item(f"file_list_{window_id}", show=False)
            for idx, file in enumerate(files):
                with dpg.group(horizontal=True, parent=f"file_list_group_{window_id}"):
                    dpg.add_text(file['name'])
                    dpg.add_button(label='X',width=20, height=20, callback=remove_file_callback, user_data=(window_id,idx))
            dpg.configure_item(f"open_file_btn_{window_id}", show=True)

    def create_file_dialog(window_id):
        """Creates a file dialog for a given window."""
        with dpg.file_dialog(
            directory_selector=False, 
            show=False, 
            callback=file_dialog_callback, 
            id=f"file_dialog_{window_id}", 
            width=700, 
            height=400,
            modal=True, #only allows 1 file to be selected
            default_path="C:/Users/OCD/Desktop/DATA/RN",
            user_data=window_id  # Pass window ID for tracking
        ):
            dpg.add_file_extension(".*")
            dpg.add_file_extension(".json", color=(0, 255, 0, 255), custom_text="[JSON File]")

    def open_file_callback(sender, app_data, user_data):
        window_id = user_data  
        files = app_state["windows"][window_id]["Files"]

        dpg.delete_item(f"mode_list_group_{window_id}", children_only = True)

        all_modes = []
        if not files:
            dpg.configure_item(f"modes_{window_id}", show = False)
            dpg.configure_item(f"mode_list_group_{window_id}", show = False)
        else:
           
            for idx, file in enumerate(files):

                file_path = file['path']
                Data = DH.getData(file_path)
                if isinstance(Data,str): 
                    t = dpg.add_text(f"{file['name']} corrupted.", parent=f"file_list_group_{window_id}")
                    red = change_text_color(1)
                    dpg.bind_item_theme(t, red)
                    continue
                _ = session_window(Data, window_id, idx)
                device_window(Data,window_id, idx)
                stimulation_window(Data,window_id, idx)
                modes = DH.getModes(Data)
                if _: modes.append('Impedance')
                if modes == ['None. Recording is Damaged!']:
                    remove_file_callback('','',user_data=(window_id,idx))
                    dpg.add_text(f"File {file['name']} was removed due to being damaged!", parent = f"mode_list_group_{window_id}",show=True)
                    dpg.add_text("Try to load again!", parent = f"mode_list_group_{window_id}",show=True)
                    update_file_list(window_id)
                else:
                    file['Data'] = Data
                    file['Modes'] = modes
                    for mode in modes:
                        if mode != ['None. Recording is Damaged!']:
                            all_modes.append(mode)
                        else: pass

            for mode in np.unique(all_modes):
                if mode == 'Damaged': 
                    continue
                dpg.add_button(label = mode, parent=f"mode_list_group_{window_id}",callback=open_tab_mode ,user_data=(mode,window_id),show=True)

        dpg.configure_item(f"mode_list_group_{window_id}", show = True)
        dpg.configure_item(f"session_parameteres_{window_id}", show = True)
   
    def open_tab_mode(sender,app_data,user_data): 
        mode, window_id = user_data

        files = app_state["windows"][window_id]["Files"]
        
        dpg.configure_item(item=f"open_file_btn_{window_id}",show=False)
        dpg.configure_item(item=f"{window_id}_add_file",show=False)
        

        tab_tag = f"tab_{mode}_{window_id}"
        if dpg.does_item_exist(tab_tag): #check if its already created
            if not dpg.is_item_shown(tab_tag):  # If closed, show it again
                dpg.configure_item(tab_tag, show=True)
                '''maybe delete tab, create a new one from scrath enabling reset (?)'''
            return
        
        plot_tag = f"plot_{tab_tag}"
        signal_tags = {}

        

        match mode:
            case 'Setup': comb_setup_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags=signal_tags)

            case 'Survey': comb_survey_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags=signal_tags)
                
            case 'Streaming': comb_streaming_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags=signal_tags)
                
            case 'Indefinite': comb_indefinite_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags=signal_tags)
        
            case 'Events': comb_event_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags=signal_tags)
            
            case 'Timeline': comb_timeline_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags=signal_tags)

            case 'Impedance': comb_impedance_tab(mode,tab_tag,window_id,files)

            case 'Damaged': return

        dpg.set_item_width(item=f"window_{window_id}",width=-1)
        dpg.set_item_height(item=f"window_{window_id}",height=-1)
                    
    with dpg.window(label=f"Window {window_id + 1}", width=400, height=300, tag=f"window_{window_id}"):
        dpg.add_button(label="Add File", callback=lambda: dpg.show_item(f"file_dialog_{window_id}"), tag = f"{window_id}_add_file")
        dpg.add_text("No file selected", tag=f"file_list_{window_id}")

        with dpg.group(tag=f"file_list_group_{window_id}"): pass
        
        dpg.add_text('', tag=f"damage_{window_id}", show=True)
        dpg.add_text('', tag=f"modes_{window_id}", show=False) #Modes in 
        dpg.add_button(label="Load Files", callback=open_file_callback,
                       tag=f"open_file_btn_{window_id}", show=False, user_data=window_id)
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text(f"Session Information", show=False, tag = f"session_parameteres_{window_id}_title")
                dpg.add_child_window(tag = f"session_parameteres_{window_id}",  height= 150, width=300, show=False)
            with dpg.group(): 
                dpg.add_text(f"Device Information", show=False, tag = f"device_parameteres_{window_id}_title")
                dpg.add_child_window(tag = f"device_parameteres_{window_id}",  height= 150, width=300, show=False)
            with dpg.group():
                dpg.add_text(f"Stimulation Information", show=False, tag = f"stimulation_parameteres_{window_id}_title")
                dpg.add_child_window(tag = f"stimulation_parameteres_{window_id}",  height= 150, width=-1, show=False)
        with dpg.group(horizontal=True,tag = f"mode_list_group_{window_id}"): pass  
        with dpg.tab_bar(tag=f"tab_bar_window_{window_id}"): pass

    create_file_dialog(window_id)

#-----------------------------------INDIVIDUAL ANALISYS-----------------------------------
def create_individual_window():
    """Dynamically creates a new independent window."""
    window_id = len(app_state["windows"])  # Unique ID
    app_state["windows"][window_id] = {"Files": []}  # Track window state
    app_state['windows'][window_id]['Bands'] = global_bands
    warning_text = ''

    def file_dialog_callback(sender, app_data, user_data):
            
        if isinstance(app_data['selections'], dict):  # Check if files were selected
            selected_files = list(app_data['selections'].values())
            
            if len(selected_files) > 1:
                dpg.set_value(f"file_list_{window_id}","Only one file can be selected! Please try again.")
            else:
                print(f"Selected file: {selected_files[0]}")
                window_id = user_data  # Get window-specific ID
                files = app_data['selections']  # Dict { "full_path": "file_name" }

                # Store full paths and filenames per window
                app_state["windows"][window_id]["Files"] = [
                    {"name": full_path, "path": file_name} 
                    for full_path, file_name in files.items()
                ]

                # Update text display with full paths
                file_list_text = "\n".join(file["name"] for file in app_state["windows"][window_id]["Files"]) if files else "No file selected"
                dpg.set_value(f"file_list_{window_id}", file_list_text)

                dpg.configure_item(f"open_file_btn_{window_id}", show=True)

    def create_file_dialog(window_id):
        """Creates a file dialog for a given window."""
        with dpg.file_dialog(
            directory_selector=False, 
            show=False, 
            callback=file_dialog_callback, 
            id=f"file_dialog_{window_id}", 
            width=700, 
            height=400,
            #modal=True, #if True: user must select a file before returning to main window - não vi diferença
            default_path="C:/Users/OCD/Desktop/DATA/RN",
            user_data=window_id  # Pass window ID for tracking
        ):
            dpg.add_file_extension(".*")
            dpg.add_file_extension("*.json", color=(0, 255, 0, 255), custom_text="[JSON File]")

    def open_tab_mode(sender, app_data, user_data): #create tab
        mode, window_id = user_data
        
        dpg.configure_item(item=f"open_file_btn_{window_id}",show=False)
        dpg.configure_item(item=f"file_selector_{window_id}",show=False)

        tab_tag = f"tab_{mode}_{window_id}"

        if dpg.does_item_exist(tab_tag): #check if its already created
            if not dpg.is_item_shown(tab_tag):  # If closed, show it again
                dpg.configure_item(tab_tag, show=True)
                '''maybe delete tab, create a new one from scrath enabling reset (?)'''
            return

        Data = app_state['windows'][window_id]['Data']
        if mode == 'Impedance':
            impedance_tab(Data,tab_tag)
            '''status, l, r = DH.getImpedance(Data)

            def build_result_table(session_name, session_data):
                # Collect unique electrodes
                electrodes1 = sorted(set(entry["Electrode1"] for entry in session_data))
                electrodes2 = sorted(set(entry["Electrode2"] for entry in session_data))

                # Build a lookup dictionary
                result_dict = {
                    (entry["Electrode2"], entry["Electrode1"]): entry["ResultValue"]
                    for entry in session_data
                }

                with dpg.table(header_row=True, borders_innerH=True, borders_innerV=True,
                                borders_outerH=True, borders_outerV=True, resizable=True, policy=dpg.mvTable_SizingStretchProp):
                    # Header row
                    dpg.add_table_column(label="SenSight")
                    for e1 in electrodes1:
                        new_label = utl.after_underscore(e1)
                        if new_label==e1:
                            new_label=utl.after_point(e1)
                        dpg.add_table_column(label=new_label)

                    # Rows
                    for e2 in electrodes2:
                        with dpg.table_row():
                            dpg.add_text(utl.after_underscore(e2))
                            for e1 in electrodes1:
                                val = result_dict.get((e2, e1), "")
                                if e2==e1: val = '-'
                                if val == "": val = result_dict.get((e1, e2), "")
                                dpg.add_text(str(val))
            with dpg.tab(tag = tab_tag, label = mode, parent=f"tab_bar_window_{window_id}"):
                with dpg.collapsing_header(label='Monopolar Left'): 
                    build_result_table("Monopolar", l["Monopolar"])
                with dpg.collapsing_header(label='Monopolar Right'):
                    build_result_table("Monopolar", r["Monopolar"])
                with dpg.collapsing_header(label='Bipolar Left'): 
                    build_result_table("Bipolar", l["Bipolar"])
                with dpg.collapsing_header(label='Bipolar Right'): 
                    build_result_table("Bipolar", r["Bipolar"])
        '''
        else:
            app_state['windows'][window_id]['Data'][tab_tag]= {'Signals': []}

            signals = DH.getSignals(Data,mode)

            plot_tag = f"plot_{tab_tag}"
            signal_tags = {}

            match mode:
                case 'Setup': setup_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags)

                case 'Survey': survey_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags)
                    
                case 'Streaming': streaming_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags)
                    
                case 'Indefinite': indefinite_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags)
            
                case 'Events': event_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags)
                
                case 'Timeline': timeline_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags)

        dpg.set_item_width(item=f"window_{window_id}",width=-1)
        dpg.set_item_height(item=f"window_{window_id}",height=-1)
               
    def open_file_callback(sender, app_data, user_data): #open file
        window_id = user_data  # Get window-specific ID
        files = app_state["windows"][window_id]["Files"]
        file_path = files[0]['path']

        #check if its not opening the same file
        previous_file_path = app_state['windows'][window_id].get('PreviousFilePath', None)
        if file_path == previous_file_path: 
            return 
        else: #show modes and buttons

            Data = DH.getData(file_path)

            app_state['windows'][window_id]['Data'] = Data
            if isinstance(Data,str):
                warning_text = f"{files[0]['name']} file not terminated!"
                og = dpg.get_value(f"damage_{window_id}")
                if og != "":
                    text = f"{og} | {warning_text}"
                else:
                    text = warning_text
                dpg.set_value(f"damage_{window_id}", text)
                red = change_text_color(1)
                dpg.bind_item_theme(f"damage_{window_id}", red)
                return
            app_state['windows'][window_id]['Modes'] = DH.getModes(Data)

            
            if app_state['windows'][window_id]['Modes'] == ['None. Recording is Damaged!']: 
                dpg.set_value(f"modes_{window_id}", 'Recording is damaged! Choose another file.')
                dpg.configure_item(f"modes_{window_id}", show=True)
                modes = []
            else:
                dpg.delete_item(item=f"mode_list_group_{window_id}",children_only=True)
                l = session_window(Data,window_id)
                device_window(Data,window_id)
                stimulation_window(Data,window_id)
                
                modes = app_state['windows'][window_id]['Modes']
                if l: modes.append('Impedance')
                if modes != ['None. Recording is Damaged!']:
                    dpg.set_value(f"modes_{window_id}", 'Recording modes present in the file:')
                    dpg.configure_item(f"modes_{window_id}", show=True)
                    dpg.set_item_label(f"window_{window_id}", files[0]['name'])
                    
                for mode in modes:
                    if mode == 'Damaged':
                        dpg.set_value(f"damage_{window_id}",'Session is damaged, recordings available.')
                        dpg.configure_item(f"damage_{window_id}",show=True)
                        continue
                    dpg.add_button(label = mode, parent=f"mode_list_group_{window_id}",callback=open_tab_mode ,user_data=(mode,window_id),show=True)
                    
                dpg.configure_item(f"mode_list_group_{window_id}", show = True)
                app_state['windows'][window_id]['PreviousFilePath'] = file_path

    with dpg.window(label=f"Window {window_id + 1}", width=400, height=300, tag=f"window_{window_id}"): #individual window 
        dpg.add_button(label="File Selector", callback=lambda: dpg.show_item(f"file_dialog_{window_id}"), tag = f"file_selector_{window_id}")
        dpg.add_text("No file selected", tag=f"file_list_{window_id}")
        dpg.add_button(label="Open File", callback=open_file_callback,
                    tag=f"open_file_btn_{window_id}", show=False, user_data=window_id)
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text(f"Session Information", show=False, tag = f"session_parameteres_{window_id}_title")
                dpg.add_child_window(tag = f"session_parameteres_{window_id}",  height= 150, width=300, show=False)
            with dpg.group(): 
                dpg.add_text(f"Device Information", show=False, tag = f"device_parameteres_{window_id}_title")
                dpg.add_child_window(tag = f"device_parameteres_{window_id}",  height= 150, width=300, show=False)
            with dpg.group():
                dpg.add_text(f"Stimulation Information", show=False, tag = f"stimulation_parameteres_{window_id}_title")
                dpg.add_child_window(tag = f"stimulation_parameteres_{window_id}",  height= 150, width=-1, show=False)
        # damage_text = ''
        # if warning_text != '': damage_text == warning_text
        dpg.add_text('', tag=f"damage_{window_id}", show=True)
        dpg.add_text('', tag=f"modes_{window_id}", show=False) #Modes in  
        with dpg.group(horizontal=True,tag = f"mode_list_group_{window_id}"): pass  
        with dpg.tab_bar(tag=f"tab_bar_window_{window_id}"): pass 
            
    create_file_dialog(window_id)  # Create a file dialog for this window
   
#---------------------------------------MAIN WINDOW---------------------------------------

dpg.create_context()
dpg.create_viewport(title="NeoDBS", width=500, height=500)
dpg.set_viewport_large_icon('NeoDBS.ico')
dpg.set_viewport_small_icon('NeoDBS.ico')
dpg.setup_dearpygui()

with dpg.texture_registry(show=False):
    width, height, channels, data = dpg.load_image("NeoDBS.png")
    dpg.add_static_texture(width, height, data, tag="logo_tex")


# Create window that matches image size exactly
with dpg.window(label="", tag="Splash", no_title_bar=True, no_resize=True, no_close=True,
                no_collapse=True, no_move=True, width=width, height=height):
    dpg.add_image("logo_tex", width=width, height=height, pos=[0, 0])


def load_main_ui():
    dpg.delete_item("Splash")

    light_theme = themes.create_theme_imgui_light()
    dark_theme = themes.create_theme_imgui_dark()
    default_classic_theme = dpg.add_theme()  # DPG default

    # Main window
    with dpg.window(label="NeoDBS", width=1000, height=600, tag="Main"):
        with dpg.menu_bar():
            with dpg.menu(label="Themes"):
                dpg.add_menu_item(label="Classic", callback=switch_theme, user_data=default_classic_theme)
                dpg.add_menu_item(label="Light", callback=switch_theme, user_data=light_theme)
                dpg.add_menu_item(label="Dark", callback=switch_theme, user_data=dark_theme)
            with dpg.menu(label="Settings"):
                dpg.add_menu_item(label="Change electrodes' names", callback=change_electrodes_names)
                # dpg.add_menu_item(label="Save All Plots")
                # dpg.add_menu_item(label="Save All Tables")
                # dpg.add_menu_item(label="Save Workspace")

        with dpg.group(horizontal=True, pos=[250, 250]):
            dpg.add_button(label="Individual/Recording Analysis", callback=create_individual_window)
            dpg.add_spacer(indent=2)
            dpg.add_button(label="Combined/Event Analysis", callback=create_multiple_window)

        dpg.set_viewport_width(1000)
        dpg.set_viewport_height(600)

    dpg.set_primary_window("Main", True)

dpg.show_viewport()
dpg.set_frame_callback(60, load_main_ui)  

dpg.start_dearpygui()
dpg.destroy_context()

'''light_theme = themes.create_theme_imgui_light()
dark_theme = themes.create_theme_imgui_dark()
default_classic_theme = dpg.add_theme() #created automatically, but no existent function in themes

# Main window with menu
with dpg.window(label="NeoDBS", width=-1, height=-1, tag="Main"):
    with dpg.menu_bar():
        with dpg.menu(label="Themes"):
            dpg.add_menu_item(label="Classic", callback=switch_theme, user_data=default_classic_theme)
            dpg.add_menu_item(label="Light", callback=switch_theme, user_data=light_theme)
            dpg.add_menu_item(label="Dark", callback=switch_theme, user_data=dark_theme)
        with dpg.menu(label="Settings"):
            dpg.add_menu_item(label="Change electrodes' names", callback=change_electrodes_names)
            dpg.add_menu_item(label="Save All Plots")
            dpg.add_menu_item(label="Save All Tables")
            dpg.add_menu_item(label="Save Workspace")
    
    with dpg.group(horizontal=True, pos=[250, 250]):
        dpg.add_button(label="Individual (Recording) Analysis", callback=create_individual_window)
        dpg.add_spacer(indent=2)
        dpg.add_button(label="Combined (Event) Analysis", callback=create_multiple_window)

dpg.show_viewport()
dpg.set_primary_window("Main", True)
dpg.start_dearpygui()
dpg.destroy_context()'''