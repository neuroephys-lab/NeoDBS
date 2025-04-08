import dearpygui.dearpygui as dpg

dpg.create_context()

dpg.show_implot_demo()

dpg.create_viewport(title="NeoDBS", width=1000, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()