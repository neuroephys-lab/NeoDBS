import dearpygui.dearpygui as dpg
import numpy as np

dpg.create_context()
dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()

# --- THEMES FOR SCATTER SERIES ---
# (Copied from previous working example for completeness)

# Define a theme for "small red circles"
with dpg.theme(tag="small_red_circle_theme"):
    with dpg.theme_component(dpg.mvScatterSeries):
        dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 3.0, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Circle, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, (255, 0, 0, 255), category=dpg.mvThemeCat_Plots)

# Define a theme for "large blue diamonds"
with dpg.theme(tag="large_blue_diamond_theme"):
    with dpg.theme_component(dpg.mvScatterSeries):
        dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 10.0, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Diamond, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, (0, 0, 255, 255), category=dpg.mvThemeCat_Plots)

# --- THEMES FOR LINE SERIES ---

# Theme for a default/thin line (0.5 weight), for comparison
with dpg.theme(tag="thin_green_line_theme"):
    with dpg.theme_component(dpg.mvLineSeries): # Target LineSeries
        # Line thickness
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 0.5, category=dpg.mvThemeCat_Plots)
        # Line color
        dpg.add_theme_color(dpg.mvPlotCol_Line, (0, 200, 0, 255), category=dpg.mvThemeCat_Plots) # Green

# Theme for a thicker line (1.0 weight), highlighted
with dpg.theme(tag="thick_magenta_line_theme"):
    with dpg.theme_component(dpg.mvLineSeries): # Target LineSeries
        # Line thickness
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 5, category=dpg.mvThemeCat_Plots)
        # Line color
        dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 0, 255, 255), category=dpg.mvThemeCat_Plots) # Magenta

# Theme for an even thicker line (1.0 weight - as it's the max), with a distinct color
with dpg.theme(tag="thick_cyan_line_theme"):
    with dpg.theme_component(dpg.mvLineSeries): # Target LineSeries
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.0, category=dpg.mvThemeCat_Plots) # Still 1.0 max
        dpg.add_theme_color(dpg.mvPlotCol_Line, (0, 255, 255, 255), category=dpg.mvThemeCat_Plots) # Cyan


with dpg.window(label="Plot Window", width=700, height=600): # Increased height for more plots
    with dpg.plot(label="Plot with Themed Lines & Markers", tag="my_plot"):
        # Create x and y data
        x_data = np.linspace(0, 10, 50)
        y_data_sin = np.sin(x_data)
        y_data_cos = np.cos(x_data)
        y_data_tan = np.tan(x_data * 0.1) # Use a different function for visual separation

        # Add a plot axis
        dpg.add_plot_axis(dpg.mvXAxis, label="x")
        with dpg.plot_axis(dpg.mvYAxis, label="y"):

           
            # --- LINE SERIES DEMO ---
            # Line 1: Default DearPyGui LineSeries (will have default thickness, autocolor)
            line_l1 = dpg.add_line_series(
                list(x_data), list(y_data_cos + 1.5), label="Line - Default (Autocolor)"
            )

            # Line 2: Thin Green Line
            line_l2 = dpg.add_line_series(
                list(x_data), list(y_data_cos + 1.0), label="Line - Thin Green"
            )
            dpg.bind_item_theme(line_l2, "thin_green_line_theme")

            # Line 3: Thick Magenta Line (highlighted)
            line_l3 = dpg.add_line_series(
                list(x_data), list(y_data_tan + 2.0), label="Line - Thick Magenta"
            )
            dpg.bind_item_theme(line_l3, "thick_magenta_line_theme")

            # Line 4: Another Thick Cyan Line
            line_l4 = dpg.add_line_series(
                list(x_data), list(y_data_tan + 1.5), label="Line - Thick Cyan"
            )
            dpg.bind_item_theme(line_l4, "thick_cyan_line_theme")


dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()