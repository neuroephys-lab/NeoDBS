import dearpygui.dearpygui as dpg
import numpy as np
import re 
import DataHandling as DH # type: ignore
import utils as utl
import Preprocessing as pre

#-----------------------------------------UTILS----------------------------------------
def show_metadata():
    print('metadata')

def add_filter_buttons():
    print('Filter buttons')

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

                if dpg.does_item_exist(f"{tab_tag}_mean"):
                    mean_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
                    current = dpg.get_value(f"{tab_tag}_mean")
                    dpg.set_value(f"{tab_tag}_mean", [current[0], mean_power])

        dpg.add_checkbox(label="Select All", default_value=True, callback=toggle_all)

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

def toggleType(signal_tags, parent, user_data):
    # `user_data` will be the type to filter by (e.g., "day", "hemisphere", "event")
    type_filter, window_id, tab_tag = user_data  # This is the type (like "day", "hemisphere", or "event")
    
    with dpg.group(parent=parent):
        # Create a checkbox to toggle all matching series at once
        def toggle_filtered_series(sender, app_data):
            for series_tag in signal_tags:
                series_label = str(dpg.get_item_label(series_tag))

                if type_filter.lower() in series_label.lower():  # Check if the label contains the type
                    #dpg.set_value(series_tag, app_data)  # Show/Hide based on checkbox state
                    dpg.configure_item(series_tag, show=app_data)  # Actually toggle visibility

            if dpg.does_item_exist(f"{tab_tag}_mean"):
                mean_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
                current = dpg.get_value(f"{tab_tag}_mean")
                dpg.set_value(f"{tab_tag}_mean", [current[0], mean_power])

        dpg.add_checkbox(label=f"Toggle {type_filter}", default_value=True, callback=toggle_filtered_series)
         
def plot_td(signals, parent, tab_tag, signal_tags):

    extra =  len(signal_tags)

    for idx, signal in enumerate(signals):
        x = signal['X']
        y = signal['Y']
        date = signal['Date']
        channel = signal['Channel']
        
        series_tag = f"{tab_tag}_series_{idx + extra}"
        
        if not dpg.does_item_exist(series_tag):
            dpg.add_line_series(x, y, label=f"{channel} ({date})", parent=parent, tag=series_tag)
            signal_tags[series_tag] = True  # Track visibility
        else:
            print(f"Skipping duplicate series: {series_tag}")

        '''dpg.add_line_series(x, y, label=f"{channel} ({date})", parent=parent, tag=series_tag)
        signal_tags[series_tag] = True  # Track visibility'''

def extract_idx_from_series_tag(series_tag: str) -> int:
    match = re.search(r'_series_(\d+)_', series_tag)
    if match:
        return int(match.group(1))  # Extract and return the idx as an integer
    else:
        raise ValueError("Invalid series_tag format")
    
def extract_side_from_series_tag(series_tag: str) -> int:
    match = re.search(r'_(left|right)$', series_tag.lower())  # Match 'left' or 'right' at the end
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid series_tag format or missing side")

def getActiveSeries(signal_tags):
    active_tags = []

    for tag, visible in signal_tags.items():
        info = dpg.get_item_configuration(tag)
        if info['show'] == True: 
            active_tags.append(tag)

    #print(len(active_tags) , ' + ', len(signal_tags)-len(active_tags) ,' = ', len(active_tags))
    return active_tags

def getSignalbyIdx(window_id,tab_tag,series_tag):
    idx = extract_idx_from_series_tag(series_tag)
    return app_state['windows'][window_id]['Data'][tab_tag]['Signals'][idx]

def getSignalbyIdxSide(window_id,tab_tag,series_tag):
    idx = extract_idx_from_series_tag(series_tag)
    side = extract_side_from_series_tag(series_tag)
    return app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side][idx]

def getMeanActiveSeries(window_id,tab_tag,signal_tags):
    active_tags = getActiveSeries(signal_tags)
    active_signals = []
    for tag in active_tags:
        active = getSignalbyIdxSide(window_id,tab_tag,tag)
        active_signals.append(active)
    mean_power = pre.MeanSignal(active_signals)
    return mean_power

#--------------------------------------MODE TABS-----------------------------------------

def event_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    app_state['windows'][window_id]['Data'][tab_tag]['Signals'] = {'left': [], 'right': []}
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}")
    dpg.add_text(f"Total events: {len(signals)}", parent=tab_tag, label = f"{tab_tag}_text_recordings")
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True ):
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=600, tag=plot_tag):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power (dB)", tag=f"y_axis_{tab_tag}")

            for idx, signal in enumerate(signals):
                date = utl.parse_datetime(signal['DateInitial'])

                for side in ['Left', 'Right']:
                    sign = signal[side]
                    label = f"day {date.day}/{date.month} | {date.minute} | {side} | {signal['EventName']}"
                    x = sign['X']
                    y = sign['Y']
                    
                    # Create a unique series tag for each side
                    series_tag = f"{tab_tag}_series_{idx}_{side.lower()}"


                    while len(app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side.lower()]) <= idx:
                        app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side.lower()].append(None)  # Fill with placeholders

                    app_state['windows'][window_id]['Data'][tab_tag]['Signals'][side.lower()][idx] = sign

                    # Add the line series for each side
                    dpg.add_line_series(x, y, label=label, parent=f"y_axis_{tab_tag}", tag=series_tag)
                    signal_tags[series_tag] = True  # Track visibility

            
            mean_power = getMeanActiveSeries(window_id,tab_tag,signal_tags)
            dpg.add_scatter_series(x, mean_power, label="Mean Power", parent=f"y_axis_{tab_tag}", tag=f"{tab_tag}_mean")
            #dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 2, category=dpg.mvThemeCat_Plots,parent=f"{tab_tag}_mean")

        types = []
        for signal in signals: 
            types.append(signal['EventName'])
            date = utl.parse_datetime(signal['DateInitial'])
            date = f"day {date.day}/{date.month}"
            types.append(date)

        types = np.unique(types).tolist()

        types.append('Left')
        types.append('Right')
        
        with dpg.group(label = f"{tab_tag}_buttons", parent=f"{tab_tag}_group"):
            for types in types:
                toggleType(signal_tags,parent=f"{tab_tag}_buttons", user_data=(types, window_id, tab_tag)) #check Obsessions

            # Ensure visibility toggle works for both sides
            toggleVisibility(signal_tags,parent=tab_tag, group=f"{tab_tag}_buttons", user_data = window_id)
            '''Se quiser atualizar o texto (?)'''
            #active = getActiveSeries(signal_tags)
            #print(active)
            #dpg.set_value(item=f"{tab_tag}_text_recordings", value=f"Total events: {len(active)}")
        
def timeline_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}")
    dpg.add_text(f"Total days: {len(signals)}", parent=tab_tag)

    with dpg.group(label = f"{tab_tag}_group" , parent=tab_tag, horizontal=True):
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=500, tag=plot_tag):
            dpg.add_plot_legend()
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag=f"x_axis_{tab_tag}")
            y_left = dpg.add_plot_axis(dpg.mvYAxis, label="Mean LFP Power (dB)", tag=f"y_axis_{tab_tag}_left")
            #y_right = dpg.add_plot_axis(dpg.mvYAxis, label="Stimulation Amplitude (mA)", tag=f"y_axis_{tab_tag}_right")

            dpg.set_axis_limits_auto(y_left)
            #dpg.set_axis_limits_auto(y_right)

            for idx, signal in enumerate(signals):
                date = utl.parse_datetime(signal['Date'])

                for side in ['Left','Right']:   
                    sign = signal[side]
                    date = utl.parse_datetime(signal['Date'])
                    label_left = f"{side} - day {date.day}/{date.month}"
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

        types = []
        for signal in signals: 
            date = utl.parse_datetime(signal['Date'])
            date = f"day {date.day}/{date.month}"
            types.append(date)

        types = np.unique(types).tolist()

        types.append('Left')
        types.append('Right')

        with dpg.group(label = f"{tab_tag}_buttons", parent=f"{tab_tag}_group"):
            for types in types:
                toggleType(signal_tags,parent=f"{tab_tag}_buttons", user_data=(types, window_id, tab_tag)) #check Obsessions

            # Ensure visibility toggle works for both sides
            toggleVisibility(signal_tags,parent=tab_tag, group=f"{tab_tag}_buttons", user_data = window_id)
        
def setup_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    sense, calibration = signals   
            
    tab_tag_off = tab_tag + "_OFF"
    dpg.add_tab(label='Setup OFF', tag=tab_tag_off, parent=f"tab_bar_window_{window_id}")
    with dpg.group(parent=tab_tag_off, horizontal=True):  # STIM OFF
        
        plot_tag = f"plt_{tab_tag_off}"
        
        # Group for Plots (Stacked Vertically)
        with dpg.group(label = f"{tab_tag}_group"):
            # First plot (Stimulation OFF)
            with dpg.plot(label=f"{mode} SETUP - Stimulation OFF", height=400, width=-1, tag=f"{plot_tag}"):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag_off}")
                dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag_off}")

                parent = f"y_axis_{tab_tag_off}"
                plot_td(sense, parent, tab_tag_off, signal_tags)

        toggleVisibility(signal_tags, tab_tag_off, group = f"{tab_tag}_group",user_data=window_id)  # Place buttons next to the plots

    tab_tag_on = tab_tag + "_ON"
    dpg.add_tab(label='Setup ON', tag=tab_tag_on, parent=f"tab_bar_window_{window_id}")
    with dpg.group(parent=tab_tag_on, horizontal=True):  # STIM OFF
        signal_tags = {}
        plot_tag = f"plt_{tab_tag_on}"
        with dpg.group():
            # Second plot (Stimulation ON)
            with dpg.plot(label=f"{mode} SETUP - Stimulation ON", height=400, width=-1, tag=f"{plot_tag}"):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag_on}")
                dpg.add_plot_axis(dpg.mvYAxis, label="LFP (µV)", tag=f"y_axis_{tab_tag_on}")

                parent = f"y_axis_{tab_tag_on}"
                plot_td(calibration, parent, tab_tag_on, signal_tags)
        toggleVisibility(signal_tags, tab_tag_on,user_data=window_id,group = f"{tab_tag}_group")

def survey_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}")
    dpg.add_text(f"Total recordings: {len(signals)}", parent=tab_tag)
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group"):
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=-1, tag=plot_tag):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (mV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"
            plot_td(signals,parent,tab_tag,signal_tags)
            print(signal_tags)

        with dpg.group():
            toggleVisibility(signal_tags, tab_tag, group = f"{tab_tag}_group",user_data=window_id)

def streaming_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}")
    dpg.add_text(f"Total recordings: {len(signals)}", parent=tab_tag)
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group", horizontal=True):

        with dpg.plot(label=f"{mode} Signals", height=400, width=-1, tag=plot_tag):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (mV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"
            plot_td(signals,parent,tab_tag,signal_tags)
            print(signal_tags)

        with dpg.group():
            toggleVisibility(signal_tags, tab_tag, group = f"{tab_tag}_group",user_data=window_id)

def indefinite_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags):
    dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}")
    dpg.add_text(f"Total recordings: {len(signals)}", parent=tab_tag)
    with dpg.group(parent=tab_tag, label = f"{tab_tag}_group"):
        
        with dpg.plot(label=f"{mode} Signals", height=400, width=-1, tag=plot_tag):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP (mV)", tag=f"y_axis_{tab_tag}")
            
            parent = f"y_axis_{tab_tag}"
            plot_td(signals,parent,tab_tag,signal_tags)
            print(signal_tags)

        with dpg.group():
            toggleVisibility(signal_tags, tab_tag, group = f"{tab_tag}_group",user_data=window_id)

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
            dpg.add_file_extension("*.json", color=(0, 255, 0, 255), custom_text="[JSON File]")

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
            
                file['Data'] = Data
                file['Modes'] = DH.getModes(Data)
                if file['Modes'] == ['None. Recording is Damaged!']:
                    remove_file_callback('','',user_data=(window_id,idx))
                    dpg.add_text(f"File {file['name']} was removed due to being damaged!", parent = f"mode_list_group_{window_id}",show=True)
                    dpg.add_text("Try to load again!", parent = f"mode_list_group_{window_id}",show=True)
                    update_file_list(window_id)
                else:
                    modes = file['Modes']
                    for mode in modes:
                        if mode != ['None. Recording is Damaged!']:
                            all_modes.append(mode)
                        else: pass

            for mode in np.unique(all_modes):
                dpg.add_button(label = mode, parent=f"mode_list_group_{window_id}",callback=open_tab_mode ,user_data=(mode,window_id),show=True)

        dpg.configure_item(f"mode_list_group_{window_id}", show = True)
   
    def open_tab_mode(sender,app_data,user_data): 
        mode, window_id = user_data
        dpg.add_tab(label=mode, tag=f"tab_{mode}_{window_id}",parent=f"tab_bar_window_{window_id}")
                    
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
        tab_tag = f"tab_{mode}_{window_id}"

        if dpg.does_item_exist(tab_tag): #check if its already created
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
        
            case 'Events': event_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags)
            
            case 'Timeline': timeline_tab(mode,tab_tag,window_id,plot_tag,signals,signal_tags)
               
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
                #dpg.add_text(f"Stimulation parameters: {left['Electrodes']}", parent=f"session_parameteres_{window_id}", show=True)

                
                modes = app_state['windows'][window_id]['Modes']
                if modes != ['None. Recording is Damaged!']:
                    dpg.set_value(f"modes_{window_id}", 'Recording modes present in the file:')
                    dpg.configure_item(f"modes_{window_id}", show=True)
                    dpg.set_item_label(f"window_{window_id}", files[0]['name'])
                    
                else: 
                    modes = []
                    dpg.set_value(f"modes_{window_id}", 'Recording is Damaged! Choose another file!')

                for mode in modes:
                    dpg.add_button(label = mode, parent=f"mode_list_group_{window_id}",callback=open_tab_mode ,user_data=(mode,window_id),show=True)
                    
                dpg.configure_item(f"mode_list_group_{window_id}", show = True)
                app_state['windows'][window_id]['PreviousFilePath'] = file_path

    with dpg.window(label=f"Window {window_id + 1}", width=400, height=300, tag=f"window_{window_id}"): #individual window 
        dpg.add_button(label="File Selector", callback=lambda: dpg.show_item(f"file_dialog_{window_id}"))
        dpg.add_text("No file selected", tag=f"file_list_{window_id}")
        dpg.add_button(label="Open File", callback=open_file_callback,
                    tag=f"open_file_btn_{window_id}", show=False, user_data=window_id)
        dpg.add_text('', tag=f"modes_{window_id}", show=False) #Modes in 
        with dpg.group(tag = f"session_parameteres_{window_id}"): pass
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

with dpg.window(label="Main Window", width=300, height=150, tag="Main"): #Main Window
    dpg.add_button(label="Individual Analysis", callback=create_individual_window)
    dpg.add_button(label="Combined Analysis", callback=create_multiple_window)


dpg.create_viewport(title="NeoDBS", width=1000, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Main", True)
dpg.start_dearpygui()
dpg.destroy_context()