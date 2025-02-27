import dearpygui.dearpygui as dpg
import numpy as np
import BRAVO 
import DataHandling as DH # type: ignore
import utils as utl

#-----------------------------------------GENERAL----------------------------------------
app_state = {"windows": {}}

def show_metadata():
    print('metadata')

def toggleVisibility(signal_tags, parent):
    # Create a group for visibility controls
    with dpg.group(parent=parent):
        dpg.add_text("Choose signals:")
        checkboxes = {}
        
        def toggle_all(sender, app_data):
            for tag, checkbox in checkboxes.items():
                dpg.set_value(checkbox, app_data)
                dpg.configure_item(tag, show=app_data)

        dpg.add_checkbox(label="Select All", default_value=True, callback=toggle_all)

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

            checkbox = dpg.add_checkbox(label=label, default_value=visible,
                                        callback=toggle_visibility, user_data=series_tag)
            checkboxes[series_tag] = checkbox
           
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

    def open_tab_mode(sender, app_data, user_data): 
        mode, window_id = user_data
        tab_tag = f"tab_{mode}_{window_id}"

        dpg.add_tab(label=mode, tag=tab_tag, parent=f"tab_bar_window_{window_id}")
        
        Data = app_state['windows'][window_id]['Data']

        signals = DH.getSignals(Data,mode)

        plot_tag = f"plot_{tab_tag}"
        signal_tags = {}

        def plot_td(signals, parent):
            for idx, signal in enumerate(signals):
                x = signal['X']
                y = signal['Y']
                date = signal['Date']
                channel = signal['Channel']
                
                series_tag = f"{tab_tag}_series_{idx}"
                dpg.add_line_series(x, y, label=f"{channel} ({date})", parent=parent, tag=series_tag)
                signal_tags[series_tag] = True  # Track visibility
            
        if mode =='Setup' :
            with dpg.group(parent=tab_tag):
                #dpg.add_text(f"Total recordings: {len(signals)}")

                with dpg.plot(label=f"{mode} Signals", height=400, width=-1, tag=plot_tag):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
                    dpg.add_plot_axis(dpg.mvYAxis, label="LFP (mV)", tag=f"y_axis_{tab_tag}")

                    sense, calibration = signals

                    parent = f"y_axis_{tab_tag}"
                    plot_td(sense, parent)
                    toggleVisibility(signal_tags,tab_tag)

                    plot_td(calibration, parent)
                    toggleVisibility(signal_tags,tab_tag)


        if mode in ['Streaming', 'Indefinite','Survey']:
            with dpg.group(parent=tab_tag):
                dpg.add_text(f"Total recordings: {len(signals)}")

                with dpg.plot(label=f"{mode} Signals", height=400, width=-1, tag=plot_tag):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{tab_tag}")
                    dpg.add_plot_axis(dpg.mvYAxis, label="LFP (mV)", tag=f"y_axis_{tab_tag}")
                    
                    parent = f"y_axis_{tab_tag}"
                    plot_td(signals,parent)

                toggleVisibility(signal_tags,tab_tag)
        
        if mode == 'Events':
            with dpg.group(parent=tab_tag):
                dpg.add_text(f"Total events: {len(signals)}")

                with dpg.plot(label=f"{mode} Signals", height=400, width=-1, tag=plot_tag):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag=f"x_axis_{tab_tag}")
                    dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power (dB)", tag=f"y_axis_{tab_tag}")

                    for idx, signal in enumerate(signals):
                        date = utl.parse_datetime(signal['DateInitial'])

                        for side in ['Left', 'Right']:
                            sign = signal[side]
                            label = f"{side} - day {date.day}/{date.month} | {date.minute} | {signal['EventName']}"
                            x = sign['X']
                            y = sign['Y']
                            
                            # Create a unique series tag for each side
                            series_tag = f"{tab_tag}_series_{idx}_{side.lower()}"
                            
                            # Add the line series for each side
                            dpg.add_line_series(x, y, label=label, parent=f"y_axis_{tab_tag}", tag=series_tag)
                            signal_tags[series_tag] = True  # Track visibility

                    # Ensure visibility toggle works for both sides
                    toggleVisibility(signal_tags,parent=tab_tag)
            
        if mode == 'Timeline':
            with dpg.group(parent=tab_tag):
                dpg.add_text(f"Total days: {len(signals)}")

                with dpg.plot(label=f"{mode} Signals", height=400, width=-1, tag=plot_tag):
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
                                print(f"Error converting data for {label}: {e}")
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

                    # Ensure visibility toggle works for both sides
                    toggleVisibility(signal_tags,parent=tab_tag)

            
    def open_file_callback(sender, app_data, user_data):
        window_id = user_data  # Get window-specific ID
        files = app_state["windows"][window_id]["Files"]
        print(files)
        file_path = files[0]['path']
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


    with dpg.window(label=f"Window {window_id + 1}", width=400, height=300, tag=f"window_{window_id}"):
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

with dpg.window(label="Main Window", width=300, height=150, tag="Main"):
    dpg.add_button(label="Individual Analysis", callback=create_individual_window)
    dpg.add_button(label="Combined Analysis", callback=create_multiple_window)


dpg.create_viewport(title="NeoDBS", width=1000, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Main", True)
dpg.start_dearpygui()
dpg.destroy_context()