import dearpygui.dearpygui as dpg

# Callback function for menu items
def print_me(sender, app_data):
    print(f"Menu item {sender} clicked!")

# Initialize Dear PyGui context
dpg.create_context()

# Create a global menu bar at the viewport level (top of the application window)
with dpg.viewport_menu_bar():
    with dpg.menu(label="File"):
        dpg.add_menu_item(label="Save", callback=print_me)
        dpg.add_menu_item(label="Save As", callback=print_me)

# Create the main window with a menu bar inside
with dpg.window(label="Main Window", width=800, height=600):
    # Add a menu bar inside the main window
    with dpg.menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="Open", callback=print_me)
            dpg.add_menu_item(label="Close", callback=print_me)
        
        with dpg.menu(label="Edit"):
            dpg.add_menu_item(label="Undo", callback=print_me)
            dpg.add_menu_item(label="Redo", callback=print_me)
    
    # Create a child window inside the main window
    with dpg.child_window(label="Child Window", width=400, height=300):
        dpg.add_text("This is a child window with no menu bar.")
        # You can also add another menu bar inside this child window
        with dpg.menu_bar():
            with dpg.menu(label="Child Options"):
                dpg.add_menu_item(label="Option 1", callback=print_me)
                dpg.add_menu_item(label="Option 2", callback=print_me)
    
    dpg.add_text("This is the main window content.")

# Create the viewport and show the window
dpg.create_viewport(title="Window with Menu Bar Example", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
