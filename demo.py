import dearpygui.dearpygui as dpg # type: ignore
import dearpygui.demo as demo # type: ignore

'''
DEMO


The main script must always:

    - Create the context create_context
    - Create the viewport create_viewport
    - Setup dearpygui setup_dearpygui
    - Show the viewport show_viewport
    - Start dearpygui start_dearpygui
    - Clean up the context destroy_context


A DPG app will have an overall structure as follows:

        - Setup: 
            - create + destroy CONTEXT
            - create + show VIEWPORT
            - setup + start DPG 

        - Context:
            1. create_context (must be the first line, or else the app doesn't run)
            last. destroy_context

        - Viewport: THE WINDOW
            1. create_viewport
            2. show_viewport

        - Render Loop: 
            1. start_dearpygui: handles the render loop 

            it may be needed to call it manually, to update the window as it needs:
            replace start_dearpygui by:
                # below replaces, start_dearpygui()
                while dpg.is_dearpygui_running():
                    # insert here any code you would like to run in the render loop
                    # you can manually stop by using stop_dearpygui()
                    print("this will run every frame")
                    dpg.render_dearpygui_frame()


        - Items: buttons, registries, windows
            create item: dpg.add_***
            - each item has a tag (int or string) --> it is returned when creating item
            - can be created at runtime

            - UI Items: any item with visual (UI) component
                - all UI items have a value. if not filled: default_value
                - set_value
                - handlers: listen to events --> dpg.item_handler_registry(tag="window of interest")

            - Containers: items that can hold other items: window, groups, registries
            dpg.show_item_registry() - SHOWS all item info
            
        - Primary Window: main window.
            - fills the viewport
            - be drawn behinf other windows

    utils:
    - show_style_editor()
    - dpg.show_metrics()
    ADD A FONT: 
        with dpg.handler_registry():
            font = dpg.add_font("path/to/your/font.ttf", size=20, default=True)
    - set_global_font()
    - dpg.set_item_pos(): fix a window

'''
print('DEMO')

'''
DEMO 


dpg.create_context()
dpg.create_viewport(title='Custom Title', width=600, height=600)

demo.show_demo()

dpg.setup_dearpygui()
dpg.show_viewport()

'''

