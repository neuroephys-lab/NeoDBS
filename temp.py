import dearpygui.dearpygui as dpg
import loadjson as load

app_state = {"windows": {}}

def file_dialog_callback(sender, app_data, user_data):
    window_id = user_data  # Get window-specific ID
    files = app_data['selections']  # Dict { "full_path": "file_name" }

    # Store full paths and filenames per window
    app_state["windows"][window_id]["Files"] = [
        {"name": file_name, "path": full_path} 
        for full_path, file_name in files.items()
    ]

    # Print full paths for debugging
    print([file["path"] for file in app_state["windows"][window_id]["Files"]])

    # Update text display with full paths
    file_list_text = "\n".join(file["path"] for file in app_state["windows"][window_id]["Files"]) if files else "No file selected"
    dpg.set_value(f"file_list_{window_id}", file_list_text)

    # Show or hide buttons depending on file count
    if len(files) > 1:
        dpg.configure_item(f"join_files_btn_{window_id}", show=True)
        dpg.configure_item(f"open_file_btn_{window_id}", show=False)
    else:
        dpg.configure_item(f"join_files_btn_{window_id}", show=False)
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
        default_path="C:/Users/OCD/Desktop/DATA/RN",
        user_data=window_id  # Pass window ID for tracking
    ):
        dpg.add_file_extension(".*")
        dpg.add_file_extension("*.json", color=(0, 255, 0, 255), custom_text="[JSON File]")

def open_file_callback(sender, app_data, user_data):
    window_id = user_data  # Get window-specific ID
    files = app_state["windows"][window_id]["Files"]
    file_path = files[0]['name']
    load.getData(file_path)

def create_window():
    """Dynamically creates a new independent window."""
    window_id = len(app_state["windows"])  # Unique ID
    app_state["windows"][window_id] = {"Files": []}  # Track window state

    with dpg.window(label=f"Window {window_id + 1}", width=400, height=300, tag=f"window_{window_id}"):
        dpg.add_button(label="File Selector", callback=lambda: dpg.show_item(f"file_dialog_{window_id}"))
        dpg.add_text("No file selected", tag=f"file_list_{window_id}")
        dpg.add_button(label="Open File", callback=open_file_callback,
                       tag=f"open_file_btn_{window_id}", show=False, user_data=window_id)
        dpg.add_button(label="Join Files", tag=f"join_files_btn_{window_id}", show=False)

    create_file_dialog(window_id)  # Create a file dialog for this window

dpg.create_context()

with dpg.window(label="Main Window", width=300, height=150, tag="Main"):
    dpg.add_button(label="Create New Window", callback=create_window)

dpg.create_viewport(title="NeoDBS", width=1000, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Main", True)
dpg.start_dearpygui()
dpg.destroy_context()
