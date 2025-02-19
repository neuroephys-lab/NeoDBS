import dearpygui.dearpygui as dpg

def create_button_theme():
    with dpg.theme(tag="button_theme"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 150, 255))  # Blue
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 200, 255))  # Lighter blue
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 15, 10)  # Large padding

def apply_theme_to_all_buttons():
    for button in dpg.get_all_items():
        if dpg.get_item_type(button) == "mvButton":  # Check if item is a button
            dpg.bind_item_theme(button, "button_theme")

dpg.create_context()
create_button_theme()

with dpg.window(label="Auto Theme All Buttons"):
    for i in range(5):
        dpg.add_button(label=f"Button {i+1}")  # Add buttons dynamically
    
    dpg.add_button(label="Apply Theme to All Buttons", callback=apply_theme_to_all_buttons)

dpg.create_viewport(title="Loop Styling", width=400, height=300)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
