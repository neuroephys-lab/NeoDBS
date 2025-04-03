from datetime import timedelta
import dearpygui.dearpygui as dpg
import numpy as np
import re 
import DataHandling as DH # type: ignore
import utils as utl
import Preprocessing as pre
import Features as ft
import time
import csv

unchecked_channels = {}
#----------------------------------------GLOBAL-----------------------------
bands = ft.bands
#-----------------------------------------UTILS----------------------------------------
def show_metadata(data):
    info_electrodes = DH.info_electrodes(data)
    print(info_electrodes)

def print_me(sender, app_data):
    print(f"Menu item {sender} clicked!")

def add_band(sender, app_data, user_data):
    global bands
    tab_tag = user_data
    min = dpg.get_value(f"{tab_tag}_band_min")
    max = dpg.get_value(f"{tab_tag}_band_max")
    new = {f'Band {min}-{max}': [min,max]}
    bands = bands | new

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

def add_correlation_buttons(tab_tag):
    if dpg.does_item_exist(tab_tag):
        with dpg.group(parent=tab_tag, horizontal=True, width=600):
            # "Correlation" menu simulation
            with dpg.collapsing_header(label="Correlation", default_open=False, parent=tab_tag):
                dpg.add_button(label="Statistical Analysis",width=-1)
                dpg.add_button(label="Machine Learning Analysis",width=-1)
    else:
        print(f"Tab {tab_tag} does not exist yet.")

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
                'bessel','iirnotch','iirpeak', 'iircomb']

    dpg.add_spacer(parent=f"{tab_tag}_filters")
    with dpg.group(horizontal=True,parent=f"{tab_tag}_filters"):
        dpg.add_combo(label='IIR Filters',callback = CustomFilter, user_data=(tab_tag,signal_tags),items = filters, parent=f"{tab_tag}_filters", tag = f"{tab_tag}_combo_filters",width=200)

def add_combo_features(tab_tag,signal_tags):

    features = ['periodogram','welch','multitaper','spectrogram', 'dpss', 'wavelet']

    dpg.add_spacer(parent=f"{tab_tag}_features")
    with dpg.group(parent=f"{tab_tag}_features", tag = f"{tab_tag}_custom_features"):
        dpg.add_combo(label='Spectral Personalized Analysis',callback = CustomFeatures, user_data=(tab_tag,signal_tags),items = features, parent=f"{tab_tag}_custom_features", tag = f"{tab_tag}_combo_features",width=200)

def add_combo_df_features(tab_tag,signal_tags):

    features = ['periodogram','welch','multitaper','spectrogram', 'dpss', 'wavelet']

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
                    mean_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
                    current = dpg.get_value(f"{tab_tag}_mean")
                    dpg.set_value(f"{tab_tag}_mean", [current[0], mean_power])

        dpg.add_checkbox(label="Select All", default_value=True, callback=toggle_all, tag = f"{tab_tag}_all")

        with dpg.child_window(autosize_x=True, height=100, border=True):
            
            # Create checkboxes for each plot
            for series_tag, visible in signal_tags.items():
                series_config = dpg.get_item_configuration(series_tag)
                label = series_config.get('label', series_tag.split('_')[-1])

                def toggle_visibility(sender, app_data, user_data):
                    dpg.configure_item(user_data, show=app_data)
                    item_id = f"{parent}_select_all"
                    if dpg.does_item_exist(item_id):  # Check if the item exists
                        dpg.set_value(item_id, False)
                        
                    else:
                        pass
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
                mean_power = getMeanActiveSeries(window_id, tab_tag, signal_tags)
                current = dpg.get_value(f"{tab_tag}_mean")
                dpg.set_value(f"{tab_tag}_mean", [current[0], mean_power])

        # Add type-level checkbox
        dpg.add_checkbox(label=f"{type_filter}", default_value=True, callback=toggle_filtered_series, tag=f"{tab_tag}_{type_filter}_checkbox")

def toggleType(signal_tags, parent, user_data):
    type_filter, window_id, tab_tag = user_data  # This is the type (like "day", "hemisphere", or "event")
    
    with dpg.group(parent=parent):
        # Create a checkbox to toggle all matching series at once
        def toggle_filtered_series(sender, app_data):
            inactive_tags = getInactiveSeries(signal_tags)
            for series_tag in signal_tags:
                series_label = str(dpg.get_item_label(series_tag))

                if type_filter.lower() in series_label.lower():  # Check if the label contains the type
                    dpg.configure_item(series_tag, show=app_data)
                      
            if dpg.does_item_exist(f"{tab_tag}_mean"):
                mean_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
                current = dpg.get_value(f"{tab_tag}_mean")
                dpg.set_value(f"{tab_tag}_mean", [current[0], mean_power])

        dpg.add_checkbox(label=f"{type_filter}", default_value=True, callback=toggle_filtered_series,tag = f"{tab_tag}_{type_filter}_checkbox")

def toggleDisplay(signals, signal_tags, window_id, tab_tag):

    days = [] #by date
    for signal in signals: 
        date = signal['Date']
        date = f"{date.hour:02d}:{date.minute:02d}"
        days.append(date)
        
    days = np.unique(days).tolist()

    channels = []
    for signal in signals: # by channel
        channels.append(extract_channel_from_series_tag(signal['Channel']).upper())
    channels = np.unique(channels).tolist()

    sides = ['Left','Right']
    
    with dpg.group(label=f"{tab_tag}_buttons"):

        # Ensure toggleVisibility is inside a vertical group
        with dpg.group(parent=f"{tab_tag}_buttons"):
            toggleVisibility(signal_tags, tab_tag, group=f"{tab_tag}_buttons", user_data=window_id)

        # Spacer to separate toggleVisibility from the buttons
        dpg.add_spacer(height=10)

        # Horizontal group for types
        with dpg.group(horizontal=True, parent=f"{tab_tag}_buttons", tag=f"{tab_tag}_types"):
            
            with dpg.group(label=f"{tab_tag}_buttons_day"):
                if len(days) > 1:
                    dpg.add_text('By recording:')
                    for day in days:
                        toggleType(signal_tags, parent=f"{tab_tag}_buttons_day", user_data=(day, window_id, tab_tag))

            with dpg.group(label=f"{tab_tag}_buttons_channel"):
                if len(channels) > 1:
                    dpg.add_text('By channel:')
                    for day in channels:
                        toggleType(signal_tags, parent=f"{tab_tag}_buttons_channel", user_data=(day, window_id, tab_tag))

            with dpg.group(label=f"{tab_tag}_buttons_side"):
                if len(sides) > 1:
                    dpg.add_text('By hemisphere:')
                    for day in sides:
                        toggleType(signal_tags, parent=f"{tab_tag}_buttons_side", user_data=(day, window_id, tab_tag))
        segment_signal(tab_tag, signal_tags)

def toggleDisplay2(signals, signal_tags, window_id, tab_tag):
    events = [signal['EventName'] for signal in signals]
    dates = []
    for signal in signals: 
        date = utl.parse_datetime(signal['DateInitial'])
        date = f"day {date.day:02d}/{date.month}"
        dates.append(date)

    dates = np.unique(dates).tolist()
    events = np.unique(events).tolist()
    sides = ['Left', 'Right']

    with dpg.group(label = f"{tab_tag}_buttons", width = -1):
        toggleVisibility(signal_tags, tab_tag, group = f"{tab_tag}_buttons",user_data=window_id)
        dpg.add_spacer(parent=f"{tab_tag}_buttons")
        with dpg.group(horizontal=True, parent=f"{tab_tag}_buttons"):
            #check days
            with dpg.group(label = f"{tab_tag}_buttons_day"):
                if len(dates)>1:
                    dpg.add_text('By days:')
                    for day in dates:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons_day", user_data=(day, window_id, tab_tag)) 

            #check channels
            with dpg.group(label = f"{tab_tag}_buttons_events"):
                if len(events)>1:
                    dpg.add_text('By events:')
                    for day in events:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons_events", user_data=(day, window_id, tab_tag)) 

            #check sides
            with dpg.group(label = f"{tab_tag}_buttons_side"):
                if len(sides)>1:
                    dpg.add_text('By hemisphere:')
                    for day in sides:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons_side", user_data=(day, window_id, tab_tag))

        dpg.add_button(label='Change to dB',callback=Volt2dB, user_data=(signal_tags,tab_tag, "", "", ""),parent=f"{tab_tag}_buttons")
        

#--- Visualization functions
def plot_td(signals, parent, tab_tag, signal_tags, files = None):
    '''
    Plot Time Domain signals (Streaming, Indefinite, Setup, Survey)
    '''
    extra =  len(signal_tags)
    window_id = extract_window_id(tab_tag)
    
    for idx, signal in enumerate(signals):
        x = signal['X']
        y = np.ascontiguousarray(signal['Y'])
        date = signal['Date']
        channel = signal['Channel']
        
        series_tag = f"{tab_tag}_series_{idx + extra}"
        combined_tag = f"{tab_tag}_file_{files}_series_{idx + extra}"
        
        if 'Data' in app_state['windows'][window_id].keys():
            if not dpg.does_item_exist(series_tag):
                dpg.add_line_series(x, y, label=f"{channel} ({date})", parent=parent, tag=series_tag)
                signal_tags[series_tag] = True  # Track visibility
                app_state['windows'][window_id]['Data'][tab_tag]['Signals'].append(signal)
            else:
                print(f"Skipping duplicate series: {series_tag}")
        else:
            if not dpg.does_item_exist(combined_tag):
                dpg.add_line_series(x, y, label=f"{channel} ({date})", parent=parent, tag=combined_tag)
                signal_tags[combined_tag] = True 
                app_state['windows'][window_id]['Files'][files]['Data'][tab_tag]['Signals'].append(signal)
            else:
                print(f"Skipping duplicate series: {combined_tag}")
        
def update_plot_td(tab_tag, signal_tags, title = None):
    active_series = getActiveSeries(signal_tags)
    window_id = extract_window_id(tab_tag)
    mode = extract_mode(tab_tag)
    plot_tag = f"plot_{tab_tag}"

    previous = dpg.get_item_label(item=plot_tag)
    if title != None: dpg.set_item_label(item=plot_tag,label=f"{previous} - {title}")

    for i,serie in enumerate(active_series):
        file = extract_file_from_series_tag(serie)
        if mode == 'Events':
            signal = getSignalbyIdxSide(window_id,tab_tag,serie)
        else:
            signal = getSignalbyIdx(window_id,tab_tag,serie)
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

def update_plot_feature(tab_tag, signal_tags, func, identifier, type):

    active_series = getActiveSeries(signal_tags)
    window_id = extract_window_id(tab_tag)
    plot_tag = f"{identifier}_y_axis"

    if dpg.does_item_exist(plot_tag):
        dpg.delete_item(plot_tag, children_only=True)

    for serie in active_series:
        memory = getSignalbyIdx(window_id,tab_tag,serie)
        signal = memory[func]
        channel = memory['Channel']
        dpg.add_line_series(signal['X'], signal[type], label = channel, parent=plot_tag)

    dpg.set_axis_limits_auto(plot_tag)

def create_table(tab_label,table_tag,features, trial_label = "New Trial"):

    def add_row():
        with dpg.table_row(parent=table_tag):
            dpg.add_input_text(default_value=trial_label, width=-1)                          
            for band, value in features.items():
                if isinstance(value, (list, np.ndarray, tuple)):  # Check if value is a list or NumPy array
                    if len(value) == 1:  # Single-element array
                        dpg.add_text(f"{float(value[0]):.2f}")  # Convert to float for clean display
                    else:  # Multiple values
                        rounded_values = [float(v) for v in np.round(value, 2)]  # Convert each np.float64 to float
                        dpg.add_text(f"{rounded_values}")  # Display clean list
                elif isinstance(value, str):
                    dpg.add_text(value)
                else:  # Single number case
                    dpg.add_text(f"{float(value):.2f}")  # Ensure it's a clean float

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
            rep = {'freqs':100,'n_cycles': 2,'sfreq':250, 'output':'power'}
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

    for param in parameter_values.keys():
        if param == 'fs' or param =='sfreq':
            parameter_values[param] = 250
        if param == 'x' or param =='data':
            parameter_values[param] = np.array(raw)

    
    match func:

        case 'multitaper': 
            func = 'psd_array_multitaper'
            parameter_values
            signal = pre.call_function(func, parameter_values, module='mtf')
            return signal
        case 'dpss':
            parameter_values['M'] = len(np.array(raw))
            power_combined =[]
            windows = pre.call_function(func, parameter_values, module = 'ssw')
            for order, taper in enumerate(windows):
                parameter_values['window'] = taper
                try: 
                    freq, psd = pre.call_function('welch', parameter_values,module='ss')
                except Exception as e: print(e)
                power_combined.append(psd)
                #power_sum = np.abs(psd).mean()

            signal = freq, np.mean(power_combined, axis=-2)
            return signal
        case 'wavelet':
            func = 'tfr_array_morlet'
            a = np.array(raw)
            parameter_values['data'] = a[np.newaxis, np.newaxis, :]
            parameter_values['sfreq'] = 250
            if isinstance(parameter_values['freqs'], str):
                parameter_values['freqs'] = int(parameter_values['freqs'])
                parameter_values['n_cycles'] = int(parameter_values['n_cycles'])
            parameter_values['freqs'] = np.arange(1,parameter_values['freqs']+1, 1)
            parameter_values['n_cycles'] = parameter_values['freqs'] / parameter_values['n_cycles']
            
            try:
                signal = pre.call_function(func, parameter_values, module = 'mtf')
                return signal
            except Exception as e: print(e)

        case _: 
            
            try: 
                signal = pre.call_function(func, parameter_values)
                return signal
            except Exception as e: print(e) 

    return signal

def plot_filtered_signal(signal_tags, tab_label, func, tab_tag, parameter_values):
    #tab_label = f"{tab_tag}_{func}"
    window_id = extract_window_id(tab_tag)
    tags = getActiveSeries(signal_tags)
    tables = []

    with dpg.group(horizontal=True, parent = tab_label,tag=f"{tab_label}_plot_group"):
        with dpg.plot(label=f"Spectral Analysis - {func}", height=400, width=600, tag = f"{tab_label}_plot"):
            dpg.bind_colormap(f"{tab_label}_plot", 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)") #tag=f"{tab_label}_x_axis"
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power (µV^2/Hz)", tag= f"{tab_label}_y_axis")
            
            power = []
            for tag in tags:
                stream = getSignalbyIdx(window_id,tab_tag,tag)
                idx = extract_idx_from_series_tag(tag)
                y = stream['Y']
                date = stream['Date']
                date = f"{date.day:02d}/{date.month:02d} - {date.hour:02d}:{date.minute:02d}"
                channel = stream['Channel']
                series_label = f"{channel} - {date}"

                signal = apply_feat(func,parameter_values,y)
                if func == 'multitaper': 
                    mask = signal[1] <= 100
                    psd = np.ascontiguousarray(signal[0][mask])
                    freqs = np.ascontiguousarray(signal[1][mask])
                else:
                    mask = signal[0] <= 100
                    freqs = np.ascontiguousarray(signal[0][mask])
                    psd = np.ascontiguousarray(signal[1][mask])

                p = {'X': freqs,
                    'Y': psd} #*100/np.sum(psd)                               

                dpg.add_line_series(freqs,p['Y'], label=series_label, parent=y_axis, tag = f"{tab_label}_{series_label}_{func}")


                if not dpg.does_item_exist(f"{tab_label}_{series_label}"):
                    dpg.add_collapsing_header(label = f'{series_label}', tag =f"{tab_label}_{series_label}", parent = tab_label)
                else:
                    dpg.delete_item(f"{tab_label}_{series_label}_table")

                #TABLE CONTENT
                full_power = np.sum(psd)
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
                    create_table(f"{tab_label}_{series_label}",f"{tab_label}_{series_label}_table", info, trial_label=b)
                tables.append(f"{tab_label}_{series_label}_table")

                updateSignalbyIdx(p,tab_tag,tag,func)

            if len(power)>1:
                mean = np.mean([p['Y'] for p in power], axis=0)
                dpg.add_line_series(freqs, mean, label="Mean Power", parent=y_axis, tag=f"{tab_label}_mean")
            dpg.set_axis_limits(x_axis,min(freqs),max(freqs))
            dpg.set_axis_limits(y_axis,min(psd),max(psd))

        dpg.add_checkbox(label='Change to dB',callback=Volt2dB, user_data=(signal_tags,tab_tag,func, tab_label, tables),parent=f"{tab_tag}_buttons", tag = f"{tab_label}_2db")
    
    time.sleep(0.2)
    dpg.set_axis_limits_auto(x_axis)
    dpg.set_axis_limits_auto(y_axis)

def plot_spectrogram(tags, tab_label, func, tab_tag, parameter_values):
    #tab_label = f"{tab_tag}_{func}"
    window_id = extract_window_id(tab_tag)
    num_plots = len(tags)
    num_cols = 2
    num_rows = (num_plots + 1) // num_cols  # Determine the required rows for the grid

    global_min = float("inf")
    global_max = float("-inf")

    for tag in tags:
        stream = getSignalbyIdx(window_id, tab_tag, tag)
        y = stream['Y']
        parameter_values['x'] = np.array(y)
        signal = pre.call_function(func, parameter_values)

        frequencies, times, Sxx = signal
        Sxx_log = 10 * np.log10(Sxx + 1e-10)  # Convert to dB scale
        Sxx_log = np.flipud(Sxx_log)

        global_min = min(global_min, Sxx_log.min())
        global_max = max(global_max, Sxx_log.max())     

    with dpg.group(horizontal=True, parent=f"{tab_label}", tag=f"{tab_label}_plot_group"):

        dpg.add_colormap_scale(tag=f"{tab_label}_colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Jet,
                                            min_scale = global_min, max_scale=global_max, height=400*num_rows)
        
        with dpg.subplots(rows=num_rows, columns=num_cols, label="Spectrograms", width=800, height=400*num_rows, tag=f"{tab_label}_subplots"):
            
            for tag in tags:
                stream = getSignalbyIdx(window_id, tab_tag, tag)
                y = stream['Y']
                channel = stream['Channel']
                parameter_values['x'] = np.array(y)
                signal = pre.call_function(func, parameter_values)
                updateSignalbyIdx(signal,tab_tag,tag,func)

                frequencies, times, Sxx = signal
                Sxx_log = 10 * np.log10(Sxx + 1e-10)  # Convert to dB scale
                Sxx_log = np.flipud(Sxx_log)

                # Create a new subplot for each heat series
                
                with dpg.plot(label=f"Spectrogram - {channel}", width=-1, height=-1, tag = f"{tab_label}_{channel}"):
                    x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                    y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")


                    label_pairs = ()
                    #for i in np.arange(0, 1, 1/len(times)):
                    for i in np.arange(0, Sxx_log.shape[0], 0.1):
                        label_pairs += ((f"{i*len(times):.0f}", i),)
                    dpg.set_axis_ticks(x_axis, label_pairs)

                    freq_pairs = ()
                    for i in np.arange(0, Sxx_log.shape[1],0.1):
                        freq_pairs += ((f"{i*max(frequencies):.0f}", i),)
                    dpg.set_axis_ticks(y_axis, freq_pairs)


                    dpg.add_heat_series(Sxx_log.flatten(), rows=Sxx_log.shape[0], cols=Sxx_log.shape[1],
                                            scale_min=global_min, scale_max=global_max, 
                                            parent=y_axis, format="")
                                            
                    
                    dpg.bind_colormap(f"{tab_label}_{channel}", dpg.mvPlotColormap_Jet)

        def link(sender, app_data):
            dpg.configure_item(f"{tab_label}_subplots", link_all_x=app_data, link_all_y=app_data)

        dpg.add_checkbox(label='Synchronize Axis', callback=link)      

def plot_wavelet(tags, tab_label, func, tab_tag, parameter_values):

    #tab_label = f"{tab_tag}_{func}"
    window_id = extract_window_id(tab_tag)
    num_plots = len(tags)
    num_cols = 2
    num_rows = (num_plots + 1) // num_cols

    with dpg.group(horizontal=True,tag = f"{tab_label}_plot_group", parent=tab_label):
        with dpg.subplots(rows=num_rows, columns=num_cols, label=f"Wavelet", width=800, height=400*num_rows, tag=f"{tab_label}_subplots"):
            
            for tag in tags:
                stream = getSignalbyIdx(window_id, tab_tag, tag)
                idx = extract_idx_from_series_tag(tag)
                y = stream['Y']
                channel = stream['Channel']
                
                try:
                    signal = apply_feat(func,parameter_values,y)
                    updateSignalbyIdx(signal,tab_tag,tag,func)
                except Exception as e: print(e)
            
                with dpg.plot(label = f'Morlet Wavelet - {channel}', width=-1, height=-1, tag = f"{tab_label}_{channel}"):
                
                    x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                    y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

                    freqs = parameter_values['freqs']
                    tfr = signal

                    # tfr = (tfr * 100) / np.max(tfr)
                    tfr = 10 * np.log10(tfr)

                    tfr = np.flipud(tfr[0, 0, :, :])

                    times = np.arange(0, len(tfr[0,:])/parameter_values['sfreq'], 1)

                    downsampled_tfr = tfr[:, ::2]
                    heatmap_data = downsampled_tfr.flatten().tolist()

                    global_min = np.min(downsampled_tfr)
                    global_max = np.max(downsampled_tfr)

                    label_pairs = ()
                    for i in np.arange(0,1.1,0.1):
                        label_pairs += ((f"{i*times[-1]:.2f}", i),)
                    dpg.set_axis_ticks(x_axis, label_pairs)

                    freq_pairs = ()
                    for i in freqs[::5]:
                        freq_pairs += ((f"{i:.0f}", i/np.max(freqs)),)
                    dpg.set_axis_ticks(y_axis, freq_pairs)


                    # Add downsampled heatmap series
                    dpg.add_heat_series(heatmap_data, rows=downsampled_tfr.shape[0], cols=downsampled_tfr.shape[1], 
                                        parent=y_axis, scale_min=global_min, scale_max=global_max, label="Wavelet Power", format="")

                    dpg.bind_colormap(f"{tab_label}_{channel}", dpg.mvPlotColormap_Jet)

        dpg.add_colormap_scale(tag=f"{tab_label}_colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Jet,
                            min_scale=global_min, max_scale=global_max, height=400*num_rows)

        def link(sender, app_data):
            dpg.configure_item(f"{tab_label}_subplots", link_all_x=app_data, link_all_y=app_data)

        dpg.add_checkbox(label='Synchronize Axis', callback=link)

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

def extract_channel_from_series_tag(series_tag: str) -> str:
    match = re.search(r'^(.*?)(?=_(left|right))', series_tag.lower())  # Look for '_left' or '_right' without including them
    
    if match:
        return match.group(1)  # Return the part before '_left' or '_right'
    else:
        raise ValueError("Invalid series_tag format or missing side")

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

def getSignalbyIdx(window_id,tab_tag,series_tag):
    idx = extract_idx_from_series_tag(series_tag)
    file = extract_file_from_series_tag(series_tag)
    if 'Data' in app_state['windows'][window_id].keys():
        return app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]
    else:
        return app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Signals'][idx]

def getSignalbyIdxSide(window_id,tab_tag,series_tag):
    idx = extract_idx_from_series_tag(series_tag)
    side = extract_side_from_series_tag(series_tag)
    return app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side][idx]

def updateXSignalbyIdx(value,tab_tag,series_tag):
    window_id = extract_window_id(tab_tag)
    idx = extract_idx_from_series_tag(series_tag)
    file = extract_file_from_series_tag(series_tag)
    if file == None:
        app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]['X'] = value
    else: app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Signals'][idx]['X'] = value

def updateSignalbyIdx(value,tab_tag,series_tag, func = None):
    window_id = extract_window_id(tab_tag)
    idx = extract_idx_from_series_tag(series_tag)
    file = extract_file_from_series_tag(series_tag)
    if file == None:
        if func != None:
            app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx][func] = value
        else: app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]['Y'] = value
    else:
        if func != None: app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Signals'][idx][func] = value
        else: app_state['windows'][window_id]['Files'][file]['Data'][tab_tag]['Signals'][idx]['Y'] = value

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

def get_window_type(window_id):
    temp = app_state['windows'][window_id]['Files']
    if len(temp)>1:
        return 'combined'
    else:
        return 'individual'

#--- Process with signal

def Volt2dB(sender,app_data,user_data):
    type = app_data
    if type == True:
        type = 'dB'
        label = type
    else: 
        type = 'Y'
        label = 'µV^2/Hz'

    signal_tags,tab_tag, func, tab_label, tables = user_data
    if tab_label == "":
        identifier = tab_tag
    else:
        identifier = tab_label

    series = getActiveSeries(signal_tags)
    window_id = extract_window_id(tab_tag)
    mode = extract_mode(tab_tag)
    for serie in series:
        idx = extract_idx_from_series_tag(serie)
        if mode == 'Events':
            signal = getSignalbyIdxSide(window_id,tab_tag,serie)
            norm = pre.log_normalization_db(signal)
            signal['dB'] = norm
        else:
            signal = getSignalbyIdx(window_id,tab_tag,serie)
            norm = pre.log_normalization_db(signal[func])
            signal[func]['dB'] = norm


    time.sleep(0.1)
    update_plot_td(tab_tag,series,'Log Normalized')

    if dpg.does_item_exist(f"{tab_tag}_mean"):
        mean_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
        current = dpg.get_value(f"{tab_tag}_mean")
        dpg.set_value(f"{tab_tag}_mean", [current[0], mean_power])

    if dpg.does_item_exist(f"{identifier}_y_axis"):

        dpg.configure_item(f"{identifier}_y_axis", label = f"LFP Power ({label})")
        update_plot_feature(tab_tag,signal_tags,func, identifier, type)

    for table in tables:
        update_table(table,type)

def getMeanActiveSeries(window_id,tab_tag,signal_tags):
    active_tags = getActiveSeries(signal_tags)
    active_signals = []
    mode = extract_mode(tab_tag)
    for tag in active_tags:
        if mode =='Events':
            active = getSignalbyIdxSide(window_id,tab_tag,tag)
        else:
            active = getSignalbyIdx(window_id,tab_tag,tag)

        active_signals.append(active)
    mean_power = pre.MeanSignal(active_signals)
    #mean_power = [m*100/np.sum(mean_power) for m in mean_power]
    return mean_power

def segment_signal(tab_tag, signal_tags):
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
        idx = extract_idx_from_series_tag(serie)
        signal = app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]
        app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]['X'] = signal['X'][min_idx:max_idx]
        app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]['Y'] = signal['Y'][min_idx:max_idx]
    
    time.sleep(0.1)
    update_plot_td(tab_tag,signal_tags,' Segment')

def DefaultFilter(sender,app_data,user_data):
    '''
    Standard filtration = 5th order Butterworth bandpass filter 1-100 Hz + Removal of cardiac component 
    Remove cardiac component - Fixed peak finder method - BRAVO adapted
    '''
    tab_tag, signal_tags = user_data

    active_series = getActiveSeries(signal_tags)
    window_id = extract_window_id(tab_tag)
    

    band = dpg.get_value(item=f"{tab_tag}_default_wn")[:2]

    for series in active_series:
        signal = getSignalbyIdx(window_id,tab_tag,series)
        clean, _ = pre.removeCardiacComponent(signal, band)
        clean = np.ascontiguousarray(clean)
        updateSignalbyIdx(clean,tab_tag,series)

    title = 'Standard Filter'
    update_plot_td(tab_tag,signal_tags, title)

def CustomFilter(sender,app_data,user_data):
    tab_tag, signal_tags = user_data

    window_id = extract_window_id(tab_tag)

    param_container = dpg.add_child_window(parent=f"{tab_tag}_filters", width=200, height=300)  # Space to add inputs dynamically
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
        args = pre.call_function(func, parameter_values) #calculates the parameters of the filter
        

        for tag in tags:
            stream = getSignalbyIdx(window_id,tab_tag,tag)
            idx = extract_idx_from_series_tag(tag)
            y = stream['Y']
            filtered = pre.call_function2('filtfilt', *args, y)
            updateSignalbyIdx(np.ascontiguousarray(filtered),tab_tag,tag)

        title = f'Custom Filter: {func}'
        update_plot_td(tab_tag,signal_tags, title)

    create_input_fields(sender,app_data)

def DefaultFeatures2(sender, app_data, user_data):
    tab_tag, signal_tags = user_data
    series_tag = list(signal_tags.keys())
    mode = extract_mode(tab_tag)
    window_id = extract_window_id(tab_tag)
    signals = getActiveSignals(tab_tag, signal_tags)

    if not dpg.does_item_exist(f"{tab_tag}_features_bar"):
        dpg.add_tab_bar(parent=f"{tab_tag}_features", tag = f"{tab_tag}_features_bar")

    func = "df"
    tab_label = f"{tab_tag}_{func}"
    if not dpg.does_item_exist(tab_label):
        dpg.add_tab(label = 'Medtronic PSD',tag=tab_label, parent=f"{tab_tag}_features_bar")

    power_band = {}
    channels = []

    if mode == 'Events':

        power = []
        for signal in signals:
            p = np.array(signal['Y'])
            f = np.array(signal['X'])
            mask = f <= 100  
            f_filtered = f[mask]  
            p_filtered = p[mask]  
            pwr = {'X':f_filtered,
                'Y':p_filtered} #*100/np.max(p_filtered)
            power.append(pwr)
            
    elif mode != 'Timeline':
        #calcular PSD --> testar e ver o melhor aspeto
        power = []
        if not dpg.does_item_exist(f"{tab_tag}_df_plot_group"):
            
            with dpg.group(parent=tab_label,tag =f"{tab_tag}_df_plot_group"):
                with dpg.plot(parent=f"{tab_tag}_df_plot_group", width=-1, label="Medtronic PSD", tag = f"{tab_tag}_df_plot"):
                    dpg.bind_colormap(f"{tab_tag}_df_plot", 0)
                    dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
                    
                    dpg.add_plot_axis(dpg.mvXAxis, label="x",tag=f"{tab_tag}_df_x_axis")
                    dpg.add_plot_axis(dpg.mvYAxis, label="y", tag=f"{tab_tag}_df_y_axis")

                dpg.add_button(label='Change to dB',callback=Volt2dB, user_data=(signal_tags,tab_tag,func),parent=f"{tab_tag}_buttons")
        else:
            dpg.delete_item(f"{tab_tag}_df_y_axis",children_only=True)
        
        for i,signal in enumerate(signals):
            medtronic = ft.MedtronicPSD(signal['Y'])

            p = medtronic['Power']
            mask = medtronic['Frequency'] <= 100  
            f_filtered = medtronic['Frequency'][mask]  
            p_filtered = p[mask]  # *100/np.sum(p_filtered)

            pwr = {'X':f_filtered,
                'Y':p_filtered}
            power.append(pwr)
            channels.append(signal['Channel'])
            power_band[signal['Channel']] = ft.mean_power_all_bands(pwr, bands)

            dpg.add_line_series(f_filtered,p_filtered, label=f"{signal['Channel']} Medtronic", parent=f"{tab_tag}_df_y_axis")

            idx = extract_idx_from_series_tag(series_tag[i])
            app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx][func] = pwr

        dpg.set_axis_limits_auto(f"{tab_tag}_df_y_axis")
        dpg.set_axis_limits_auto(f"{tab_tag}_df_x_axis")
       

    if not dpg.does_item_exist(f"{tab_label}_mean_power"): #once the first is created all are
        dpg.add_collapsing_header(label = 'Channel Power', tag =f"{tab_label}_power", parent = tab_label)
        dpg.add_collapsing_header(label = 'Mean Power', tag =f"{tab_label}_mean_power", parent = tab_label) #adicionar normalize dentro de cada collapsing header
        dpg.add_collapsing_header(label = 'Peak Features', tag =f"{tab_label}_peak", parent = tab_label)
        
        
    #Power per band per stream
    for ch, pwr in power_band.items():
        std_dev = ft.std_dev_streams(power, bands)
        info = {band: f"{np.round(p,2)} , {np.round(s,2)}" for band,p,s in zip(bands,pwr.values(),std_dev.values())}
        create_table(f"{tab_label}_power",f"{tab_label}_table_power", info, trial_label=ch)

    #Mean power per band for all streams
    features = ft.mean_power_all_bands(power, bands)
    std_dev = ft.std_dev_streams(power, bands)
    info = {band: f"{np.round(p,2)} , {np.round(s,2)}" for band,p,s in zip(bands,features.values(),std_dev.values())}
    create_table(f"{tab_label}_mean_power",f"{tab_label}_table_mean_power",info)

    #Peaks per band and stream
    for p, ch in zip(power,channels):
        picos = ft.peak_per_band(p)
        create_table(f"{tab_label}_peak",f"{tab_label}_table_peak",picos, trial_label=ch)

def DefaultFeatures(sender, app_data, user_data):
    tab_tag, signal_tags = user_data

    parameter_values = {}

    parameter_values, documentation = fill_params_features(app_data)

    func = app_data

    tags = getActiveSeries(signal_tags)
    
    tab_label = f"{tab_tag}_df_{func}"
    if not dpg.does_item_exist(f"{tab_tag}_features_bar"):
        dpg.add_tab_bar(parent=f"{tab_tag}_features", tag = f"{tab_tag}_features_bar")

    if dpg.does_item_exist(tab_label):
        dpg.delete_item(f"{tab_label}_plot_group")
    else:
        dpg.add_tab(label=f"Default {func}", parent=f"{tab_tag}_features_bar", tag=tab_label)  
    match func:
        case 'spectrogram': plot_spectrogram(tags, tab_label, func, tab_tag, parameter_values)
        case 'wavelet': plot_wavelet(tags, tab_label, func, tab_tag, parameter_values)
        case _: plot_filtered_signal(signal_tags, tab_label, func, tab_tag, parameter_values)

def CustomFeatures(sender,app_data,user_data):
    tab_tag, signal_tags = user_data

    window_id = extract_window_id(tab_tag)
    parameter_values = {}
    input_fields = {}  # Store input field IDs


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
        params, documentation = fill_params_features(app_data) 
        documentation = pre.extract_params_and_returns(documentation)

        dpg.add_text(documentation, parent=doc_container)       
        print(documentation)
        if not params:
            dpg.add_text("No parameters found", parent=param_container)
            return
        dpg.add_text("Required parameters: ", parent=param_container)

        parameter_values.clear()  # Reset parameter storage
        input_fields.clear()  # Reset input field storage
        

        for param, default in params.items():            
            if param == 'x' or param == 'data':  default = '---'
            if param == 'fs' or param =='sfreq': default = 250
            if param == 'output': default = 'power' #wavelet
            if param == 'freqs': default = 100 #wavelet
            if param != 'window':
                input_id = dpg.add_input_text(
                    label=param, 
                    default_value= default if default is not None else " ",
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
            parameter_values[param] = value

        
        if not dpg.does_item_exist(f"{tab_tag}_plot_features"):
            dpg.add_button(label="Plot filtered signal", callback=apply_filt, parent=param_container, user_data=user_data, tag=f"{tab_tag}_plot_features")

    def apply_filt(sender, app_data, user_data):
        func = user_data

        tags = getActiveSeries(signal_tags)
        
        tab_label = f"{tab_tag}_{func}"
        if not dpg.does_item_exist(f"{tab_tag}_features_bar"):
            dpg.add_tab_bar(parent=f"{tab_tag}_features", tag = f"{tab_tag}_features_bar")

        if dpg.does_item_exist(tab_label):
            dpg.delete_item(f"{tab_label}_plot_group")
        else:
            dpg.add_tab(label=f"{func}", parent=f"{tab_tag}_features_bar", tag=tab_label)  
        match func:
            case 'spectrogram': plot_spectrogram(tags, tab_label, func, tab_tag, parameter_values)
            case 'wavelet': plot_wavelet(tags, tab_label, func, tab_tag, parameter_values)
            case _: plot_filtered_signal(signal_tags, tab_label, func, tab_tag, parameter_values)
                #dpg.add_button(label='Normalize', parent = tab_label)
                                     
    create_input_fields(sender,app_data)

def insert_events(sender, app_data, user_data):
    window_id, tab_tag, signal_tags= user_data

    def read_txt(sender, app_data, user_data):
        streaming_file = app_data['file_path_name']
        events = utl.read_event_file(streaming_file)
        events_times = {}
        scatter = []
        active = getActiveSignals(tab_tag,signal_tags)
        series = getActiveSeries(signal_tags)
        for i,signal in enumerate(active):
            date = signal['Date']
            new_time = [date + timedelta(seconds=val) for val in signal['X']]
            new_x = [d.timestamp() for d in new_time]
            updateXSignalbyIdx(new_x,tab_tag,series[i])
            
            dpg.configure_item(f"x_axis_{tab_tag}",scale=dpg.mvPlotScale_Time)
            dpg.configure_item(series[i], x=new_x)
                        
            for event in events:
                hour, minute, type = event
                idx = utl.find_closest_index(new_time,hour,minute)
                if idx != None: 
                    events_times[f"{hour}:{minute}"] = (type, idx)
                    scatter.append((new_x[int(idx)], type))
        if scatter:
            for i, type in scatter:
                dpg.add_vline_series(parent=f"y_axis_{tab_tag}", x=[i], label=type)
        else: 
            dpg.add_text("No Events in the present recordings!", parent=f"{tab_tag}_add_events")


    def create_file_dialog(window_id):
        with dpg.file_dialog(
            directory_selector=False, 
            show=True, 
            callback=read_txt, 
            width=700, 
            height=400,
            modal=True, 
            default_path="C:/Users/OCD/Desktop/LRodrigues/NeoDBS",
            user_data=window_id
        ) as dialog_id:
            dpg.add_file_extension(".txt", color=(0, 255, 0, 255), custom_text="[TEXT File]")


    create_file_dialog(window_id)

#--------------------------------------INDIVIDUAL TABS-----------------------------------------
'''For now ONLY individual analysis'''
def event_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    app_state['windows'][window_id]['Data'][tab_tag]['Signals'] = {'left': [], 'right': []}

    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)   
    dpg.add_text(f"Total events: {len(signals)}", parent=tab_tag, label = f"{tab_tag}_text_recordings")
    
    with dpg.group(label = f"{tab_tag}_group", parent=tab_tag, horizontal=True ):
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power (µV^2/Hz)", tag=f"y_axis_{tab_tag}")

            for idx, signal in enumerate(signals):
                date = utl.parse_datetime(signal['DateInitial'])

                for side in ['Left', 'Right']:
                    sign = signal[side]
                    label = f"day {date.day:02d}/{date.month} | {date.minute} | {side} | {signal['EventName']}"
                    x = sign['X']
                    y = sign['Y']
                    
                    # Create a unique series tag for each side
                    series_tag = f"{tab_tag}_series_{idx}_{side.lower()}"


                    while len(app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side.lower()]) <= idx:
                        app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side.lower()].append(None)  # Fill with placeholders

                    app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side.lower()][idx] = sign

                    # Add the line series for each side
                    dpg.add_line_series(x, y, label=label, parent=f"y_axis_{tab_tag}", tag=series_tag)#, fill=[1.0, 0, 0, 0.5]) --> define transparency?
                    signal_tags[series_tag] = True  # Track visibility
            
            mean_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
            dpg.add_scatter_series(x, mean_power, label="Mean Power", parent=f"y_axis_{tab_tag}", tag=f"{tab_tag}_mean")
            #dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 2, category=dpg.mvThemeCat_Plots,parent=f"{tab_tag}_mean")

        toggleDisplay2(signals,signal_tags,window_id,tab_tag)
          
    add_features_buttons(tab_tag, signal_tags)
    add_correlation_buttons(tab_tag)  

def timeline_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    dpg.add_text(f"Total days: {len(signals)}", parent=tab_tag)
    with dpg.group(label = f"{tab_tag}_group" , parent=tab_tag, horizontal=True):
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=500, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag=f"x_axis_{tab_tag}")
            y_left = dpg.add_plot_axis(dpg.mvYAxis, label="Mean LFP Power (µV^2/Hz)", tag=f"y_axis_{tab_tag}_left")
            #y_right = dpg.add_plot_axis(dpg.mvYAxis, label="Stimulation Amplitude (mA)", tag=f"y_axis_{tab_tag}_right")

            dpg.set_axis_limits_auto(y_left)
            #dpg.set_axis_limits_auto(y_right)

            for idx, signal in enumerate(signals):
                date = utl.parse_datetime(signal['Date'])

                for side in ['Left','Right']:   
                    sign = signal[side]
                    date = utl.parse_datetime(signal['Date'])
                    label_left = f"{side} - day {date.day:02d}/{date.month}"
                    label_right = f"{side} - stim"
                
                    try:
                        x = [utl.convert_to_timestamp(val) for val in sign['X']]
                        y = [float(val) for val in sign['Y']]
                        #stim = [float(val) for val in sign['Stim']]
                    except ValueError as e:
                        print(f"Error converting data for {label_left}: {e}")
                        continue  # Skip this plot if conversion fails'''


                    # LFP power
                    series_tag = f"{tab_tag}_series_{idx}_{side.lower()}_left"
                    dpg.add_line_series(x, y, label=label_left, parent=y_left, tag=series_tag)
                    signal_tags[series_tag] = True  # Track visibility
                    '''
                    # Stimulation
                    series_tag = f"{tab_tag}_series_{idx}_{side.lower()}_right"
                    dpg.add_line_series(x, stim, label=label_right, parent=y_right, tag=series_tag)
                    signal_tags[series_tag] = True  # Track visibility'''

        days = []
        for signal in signals: 
            date = utl.parse_datetime(signal['Date'])
            date = f"day {date.day:02d}/{date.month}"
            days.append(date)

        days = np.unique(days).tolist()
        sides = ['Left','Right']

        with dpg.group(label = f"{tab_tag}_buttons", parent=f"{tab_tag}_group",):
            toggleVisibility(signal_tags,parent=tab_tag, group=f"{tab_tag}_buttons", user_data = window_id)
            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_text('By day: ')
                    for day in days:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons", user_data=(day, window_id, tab_tag)) #check day
                with dpg.group():
                    dpg.add_text('By hemisphere: ')
                    for day in sides:
                        toggleType(signal_tags,parent=f"{tab_tag}_buttons", user_data=(day, window_id, tab_tag)) #check hemisphere
            #dpg.add_button(label='Normalize',callback=Volt2dB, user_data=(signal_tags,tab_tag),parent=f"{tab_tag}_buttons")

    add_features_buttons(tab_tag, signal_tags)
    add_correlation_buttons(tab_tag)

def setup_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    sense, calibration = signals   
    
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


    if sense:
        setup_off_tab()
    if calibration:
        setup_on_tab()

def survey_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    dpg.add_text(f"Total recordings: {len(signals)}", parent=tab_tag)
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (mV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"
            plot_td(signals,parent,tab_tag,signal_tags)

        toggleDisplay(signals, signal_tags, window_id, tab_tag)
    add_filters_buttons(tab_tag,signal_tags)
    add_features_buttons(tab_tag, signal_tags)
    add_correlation_buttons(tab_tag)

def streaming_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    dpg.add_text(f"Total recordings: {len(signals)}", parent=tab_tag)
    rdate = signals[0]['Date']
    dpg.add_text(f"Day: {rdate.day}/{rdate.month}/{rdate.year}", parent=tab_tag)
    channel = extract_channel_from_series_tag(signals[0]['Channel'])
    dpg.add_text(f"Channel: {channel.upper()}", parent=tab_tag)

    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):

        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (mV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"
            plot_td(signals,parent,tab_tag,signal_tags)

        toggleDisplay(signals, signal_tags, window_id, tab_tag)
            
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
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (mV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"
            plot_td(signals,parent,tab_tag,signal_tags)

        toggleDisplay(signals, signal_tags, window_id, tab_tag)
        #button_parent = f"{tab_tag}_buttons"
        with dpg.group(parent=f"{tab_tag}_buttons"):
            dpg.add_spacer(height=10)  # Optional: Adds some spacing
            dpg.add_button(label='Segment Signal', show=True)
        
    add_filters_buttons(tab_tag,signal_tags)
    add_features_buttons(tab_tag, signal_tags)
    add_correlation_buttons(tab_tag)

#--------------------------------------COMBINED TABS-----------------------------------------

def comb_event_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    print('COMBINED TAB EVENTS')

def comb_streaming_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}", closable=True)
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):

        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.bind_colormap(plot_tag, 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast,no_buttons = True)
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (mV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"

            for idx, file in enumerate(files):
                if mode in file['Modes']: 
                    signals = DH.getSignals(file['Data'],mode)
                    file['Data'][tab_tag]= {'Signals': []}
                    rdate = signals[0]['Date']
                    dpg.add_text(f"Day: {rdate.day}/{rdate.month}/{rdate.year}", parent=tab_tag)
                    channel = extract_channel_from_series_tag(signals[0]['Channel'])
                    dpg.add_text(f"Channel: {channel.upper()}", parent=tab_tag)
                    plot_td(signals,parent,tab_tag,signal_tags,files=idx)

        toggleDisplay(signals, signal_tags, window_id, tab_tag)
        with dpg.group(parent=tab_tag, tag = f"{tab_tag}_add_events"):
            dpg.add_button(label='Insert Streaming Events', parent=f"{tab_tag}_add_events", callback = insert_events, user_data=(window_id, tab_tag, signal_tags))
        add_filters_buttons(tab_tag,signal_tags)
        add_features_buttons(tab_tag, signal_tags)

#-----------------------------------COMBINED ANALISYS-------------------------------------

def create_multiple_window():
    window_id = len(app_state["windows"])  # Unique ID
    app_state["windows"][window_id] = {"Files": []}  # Track window state

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
            
                modes = DH.getModes(Data)
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
                dpg.add_button(label = mode, parent=f"mode_list_group_{window_id}",callback=open_tab_mode ,user_data=(mode,window_id),show=True)

        dpg.configure_item(f"mode_list_group_{window_id}", show = True)
   
    def open_tab_mode(sender,app_data,user_data): 
        mode, window_id = user_data

        signals = []
        files = app_state["windows"][window_id]["Files"]
        
        dpg.configure_item(item=f"open_file_btn_{window_id}",show=False)

        tab_tag = f"tab_{mode}_{window_id}"
        if dpg.does_item_exist(tab_tag): #check if its already created
            if not dpg.is_item_shown(tab_tag):  # If closed, show it again
                dpg.configure_item(tab_tag, show=True)
                '''maybe delete tab, create a new one from scrath enabling reset (?)'''
            return
        
        plot_tag = f"plot_{tab_tag}"
        signal_tags = {}

        match mode:
            case 'Setup': print('combined setup')

            case 'Survey': print('combined Survey')
                
            case 'Streaming': comb_streaming_tab(mode,tab_tag,window_id,plot_tag,files,signal_tags=signal_tags)
                
            case 'Indefinite': print('combined Indefinite')
        
            case 'Events': print('combined Events')
            
            case 'Timeline': print('combined Timeline')

        dpg.set_item_width(item=f"window_{window_id}",width=-1)
        dpg.set_item_height(item=f"window_{window_id}",height=-1)

        #dpg.add_tab(label=mode, tag=f"tab_{mode}_{window_id}",parent=f"tab_bar_window_{window_id}")
                    
    with dpg.window(label=f"Window {window_id + 1}", width=400, height=300, tag=f"window_{window_id}"):
        dpg.add_button(label="Add File", callback=lambda: dpg.show_item(f"file_dialog_{window_id}"))
        dpg.add_text("No file selected", tag=f"file_list_{window_id}")

        with dpg.group(tag=f"file_list_group_{window_id}"): pass
        
        dpg.add_text('', tag=f"modes_{window_id}", show=False) #Modes in 
        dpg.add_button(label="Load Files", callback=open_file_callback,
                       tag=f"open_file_btn_{window_id}", show=False, user_data=window_id)
        
        with dpg.group(horizontal=True,tag = f"mode_list_group_{window_id}"): pass
   
        with dpg.tab_bar(tag=f"tab_bar_window_{window_id}"): pass

    create_file_dialog(window_id)

#-----------------------------------INDIVIDUAL ANALISYS-----------------------------------
def create_individual_window():
    """Dynamically creates a new independent window."""
    window_id = len(app_state["windows"])  # Unique ID
    app_state["windows"][window_id] = {"Files": []}  # Track window state

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
            app_state['windows'][window_id]['Modes'] = DH.getModes(Data)

            
            if app_state['windows'][window_id]['Modes'] == ['None. Recording is Damaged!']: 
                dpg.set_value(f"modes_{window_id}", 'Recording is damaged! Choose another file.')
                dpg.configure_item(f"modes_{window_id}", show=True)
                modes = []
            else:

                
                date = DH.getSessionDate(Data)
                session_duration = DH.getSessionDuration(Data)
                initial_stim_status, final_stim_status = DH.getStimStatus(Data)
                #left, right = DH.getStimulationParameters(Data,'A')
                dpg.delete_item(item=f"session_parameteres_{window_id}",children_only=True)
                dpg.delete_item(item=f"mode_list_group_{window_id}",children_only=True)
                 
                
                dpg.add_text(f"Session date: {date}", parent=f"session_parameteres_{window_id}", show=True)
                dpg.add_text(f"Session duration: {session_duration}", parent=f"session_parameteres_{window_id}", show=True)
                dpg.add_text(f"Initial Stimulation: {initial_stim_status}", parent=f"session_parameteres_{window_id}", show=True)
                dpg.add_text(f"Final Stimulation: {final_stim_status}", parent=f"session_parameteres_{window_id}", show=True)
                dpg.configure_item(f"session_parameteres_{window_id}", show=True)
                #dpg.add_text(f"Stimulation parameters: {left['Electrodes']}", parent=f"session_parameteres_{window_id}", show=True)

                
                modes = app_state['windows'][window_id]['Modes']
                if modes != ['None. Recording is Damaged!']:
                    dpg.set_value(f"modes_{window_id}", 'Recording modes present in the file:')
                    dpg.configure_item(f"modes_{window_id}", show=True)
                    dpg.set_item_label(f"window_{window_id}", files[0]['name'])
                    

                for mode in modes:
                    dpg.add_button(label = mode, parent=f"mode_list_group_{window_id}",callback=open_tab_mode ,user_data=(mode,window_id),show=True)
                    
                dpg.configure_item(f"mode_list_group_{window_id}", show = True)
                app_state['windows'][window_id]['PreviousFilePath'] = file_path

    with dpg.window(label=f"Window {window_id + 1}", width=400, height=300, tag=f"window_{window_id}"): #individual window 
        dpg.add_button(label="File Selector", callback=lambda: dpg.show_item(f"file_dialog_{window_id}"), tag = f"file_selector_{window_id}")
        dpg.add_text("No file selected", tag=f"file_list_{window_id}")
        dpg.add_button(label="Open File", callback=open_file_callback,
                    tag=f"open_file_btn_{window_id}", show=False, user_data=window_id)
        with dpg.child_window(tag = f"session_parameteres_{window_id}", height=100, show=False): pass
        dpg.add_text('', tag=f"modes_{window_id}", show=False) #Modes in 
        with dpg.group(horizontal=True,tag = f"mode_list_group_{window_id}"): pass  
        with dpg.tab_bar(tag=f"tab_bar_window_{window_id}"): pass 
            
    create_file_dialog(window_id)  # Create a file dialog for this window
   
#---------------------------------------MAIN WINDOW---------------------------------------

dpg.create_context()

app_state = {"windows": {}}

with dpg.theme(tag="mean_plot_theme"):
    with dpg.theme_component(dpg.mvScatterSeries):
        dpg.add_theme_color(dpg.mvPlotCol_Line, (60, 150, 200), category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Square, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 2, category=dpg.mvThemeCat_Plots)

with dpg.window(label="NeoDBS", width=-1, height=-1, tag="Main"): #Main Window
    dpg.add_button(label="Individual Analysis", callback=create_individual_window)
    dpg.add_button(label="Combined Analysis", callback=create_multiple_window)


dpg.create_viewport(title="NeoDBS", width=1000, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Main", True)
dpg.start_dearpygui()
dpg.destroy_context()