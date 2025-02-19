import dearpygui.dearpygui as dpg
import BRAVO 
import DataHandling as DH # type: ignore

app_state = {"windows": {}}

def create_multiple_window():
    window_id = len(app_state["windows"])  # Unique ID
    app_state["windows"][window_id] = {"Files": []}  # Track window state

    def file_dialog_callback(sender, app_data, user_data):
        window_id = user_data  # Get window-specific ID
        files = app_data['selections']  # Dict { "full_path": "file_name" }
        for file in files:
            app_state["windows"][window_id]["Files"].append(
                {"name": file, "path": files[file]})
            print(app_state["windows"][window_id]["Files"])


        file_list_text = "\n".join(file["path"] for file in app_state["windows"][window_id]["Files"]) if files else "No file selected"
        dpg.set_value(f"file_list_{window_id}", file_list_text)

        dpg.configure_item(f"open_file_btn_{window_id}", show=True)
        dpg.configure_item(f"join_files_btn_{window_id}", show=True)

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
        file_path = files[0]['path']
        Data = DH.getData(file_path)
        

        app_state['windows'][window_id]['Data'] = Data
        app_state['windows'][window_id]['Modes'] = DH.getModes(Data)

        modes = app_state['windows'][window_id]['Modes']
        dpg.set_value(f"modes_{window_id}", modes)
        dpg.configure_item(f"modes_{window_id}", show=True)
        dpg.set_item_label(f"window_{window_id}", f"Combined {window_id}")

    def join_file_callback(sender, app_data, user_data):
        window_id = user_data  # Get window-specific ID
        files = app_state["windows"][window_id]["Files"]
        for i in range(len(files)):
            file_path = files[i]['path']
            Data = DH.getData(file_path)
            app_state["windows"][window_id]["Files"][i]['Data'] = Data

        jsons = []
        for i in range(len(files)):
            jsons.append(app_state["windows"][window_id]["Files"][i]['Data'])
        merged = BRAVO.concatenateJSONs(jsons)
        print(DH.getModes(merged))


    with dpg.window(label=f"Window {window_id + 1}", width=400, height=300, tag=f"window_{window_id}"):
        dpg.add_button(label="File Selector", callback=lambda: dpg.show_item(f"file_dialog_{window_id}"))
        dpg.add_text("No file selected", tag=f"file_list_{window_id}")
        dpg.add_button(label="Open File", callback=open_file_callback,
                       tag=f"open_file_btn_{window_id}", show=False, user_data=window_id)
        dpg.add_button(label="Join Files", tag=f"join_files_btn_{window_id}", show=False, user_data=window_id,callback=join_file_callback)
        
    create_file_dialog(window_id)

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

                # Print full paths for debugging
                print([file["path"] for file in app_state["windows"][window_id]["Files"]])

                # Update text display with full paths
                file_list_text = "\n".join(file["path"] for file in app_state["windows"][window_id]["Files"]) if files else "No file selected"
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

    def open_file_callback(sender, app_data, user_data):
        window_id = user_data  # Get window-specific ID
        files = app_state["windows"][window_id]["Files"]
        print(files)
        file_path = files[0]['path']
        Data = DH.getData(file_path)
        

        app_state['windows'][window_id]['Data'] = Data
        app_state['windows'][window_id]['Modes'] = DH.getModes(Data)

        modes = app_state['windows'][window_id]['Modes']
        dpg.set_value(f"modes_{window_id}", modes)
        dpg.configure_item(f"modes_{window_id}", show=True)
        dpg.set_item_label(f"window_{window_id}", files[0]['name'])

    with dpg.window(label=f"Window {window_id + 1}", width=400, height=300, tag=f"window_{window_id}"):
        dpg.add_button(label="File Selector", callback=lambda: dpg.show_item(f"file_dialog_{window_id}"))
        dpg.add_text("No file selected", tag=f"file_list_{window_id}")
        dpg.add_button(label="Open File", callback=open_file_callback,
                       tag=f"open_file_btn_{window_id}", show=False, user_data=window_id)
        dpg.add_text('', tag=f"modes_{window_id}", show=False) #Modes in 

    create_file_dialog(window_id)  # Create a file dialog for this window

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
