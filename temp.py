import dearpygui.dearpygui as dpg

# Create a context
dpg.create_context()

with dpg.window(label="Main Window", tag="main"):
    
    # Create a tab bar
    with dpg.tab_bar():
        
        # Add a tab
        with dpg.tab(label="Tab 1"):
            dpg.add_text("This is inside Tab 1")

        # Add another tab
        with dpg.tab(label="Tab 2"):
            dpg.add_text("This is inside Tab 2")

        # Add a tab button (this appears alongside the tabs)
        dpg.add_tab_button(label="Extra Button")

# Create and show viewport
dpg.create_viewport(title="Dear PyGui Example", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()

dpg.start_dearpygui()
dpg.destroy_context()



'''
    screenshot.save(f"plots\\{plot_tag}_image.png")  # Save the image
    print(f"Plot saved as '{plot_tag}_image.png'")

# Button to trigger save
with dpg.window(label="Controls", pos=(650, 100)):
    dpg.add_button(label="Save Plot", callback=save_plot, user_data='my_plot')

'''