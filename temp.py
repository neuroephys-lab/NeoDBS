import dearpygui.dearpygui as dpg

dpg.create_context()

with dpg.window(label="Main Window", width=500, height=400):
    
    with dpg.collapsing_header(label="Collapsing Section", default_open=True):
        
        with dpg.tab_bar():
            with dpg.tab(label="Tab 1"):
                dpg.add_button(label="Button in Tab 1", callback=lambda: print("Tab 1 Button Clicked"))
            
            with dpg.tab(label="Tab 2"):
                dpg.add_button(label="Button in Tab 2", callback=lambda: print("Tab 2 Button Clicked"))

dpg.create_viewport(title="Dear PyGui Example", width=500, height=400)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
