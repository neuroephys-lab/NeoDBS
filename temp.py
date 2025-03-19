import dearpygui.dearpygui as dpg

dpg.create_context()

# Function to add a new tab dynamically
dpg.show_implot_demo()

    

dpg.create_viewport(title="Dear PyGui Example", width=500, height=400)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
