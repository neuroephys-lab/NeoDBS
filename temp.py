import DataHandling as DH
import dearpygui.dearpygui as dpg
import numpy as np

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-12-05\\Report_Json_Session_Report_20250212T121745.json"
Data = DH.getData(file_path)
events = DH.getSignals(Data, 'Events')


dpg.create_context()

hover_text = dpg.generate_uuid()  # Unique ID for tooltip text
tooltip_window = dpg.generate_uuid()  # Unique ID for tooltip window

def check_hover(sender, app_data):
    """Detects if the cursor is near a peak and updates the tooltip."""
    mouse_x, mouse_y = dpg.get_mouse_pos(local=False)  # Get absolute mouse position

    for event in events:
        for side in ["Left", "Right"]:
            stream = event[side]
            peak_idx = np.argmax(stream["Y"])  # Find peak index
            peak_f = stream["X"][peak_idx]  # Frequency at peak
            peak_power = stream["Y"][peak_idx]  # Power at peak

            # Convert data point to screen space
            peak_pos = dpg.get_plot_mouse_pos()  # Get mouse pos relative to plot
            plot_x, plot_y = peak_pos[0], peak_pos[1]

            # Check if mouse is close to peak
            if abs(plot_x - peak_f) < 3 and abs(plot_y - peak_power) < 3:
                dpg.set_value(hover_text, f"Peak Power: {peak_power:.2f} dB\nFrequency: {peak_f:.2f} Hz")
                dpg.configure_item(tooltip_window, show=True)
                dpg.set_item_pos(tooltip_window, mouse_x + 10, mouse_y + 10)  # Move tooltip to cursor
                return

    dpg.configure_item(tooltip_window, show=False)  # Hide if not hovering a peak

# Create the plot
with dpg.window(label="Tutorial", tag="plot_window"):
    with dpg.plot(label="Events", height=-1, width=-1):
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="Power (dB)", tag="y_axis")

        for event in events:
            for side in ["Left", "Right"]:
                stream = event[side]
                peak_idx = np.argmax(stream["Y"])
                peak_f = stream["X"][peak_idx]
                peak_power = stream["Y"][peak_idx]

                dpg.add_line_series(stream["X"], stream["Y"], label=f"{event['EventName']} {side}", parent="y_axis")
                dpg.add_scatter_series([peak_f], [peak_power], label=f"{side} Peak", parent="y_axis")

# Tooltip (hidden by default)
with dpg.window(label="Peak Info", show=False, tag=tooltip_window, no_title_bar=True, no_resize=True, no_move=True):
    dpg.add_text("", tag=hover_text)

# Add a mouse move handler to check hover dynamically
with dpg.handler_registry():
    dpg.add_mouse_move_handler(callback=check_hover)

dpg.create_viewport(title="FEATURES", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

'''dpg.create_context()

with dpg.window(label="Tutorial"):
    # create plot
    with dpg.plot(label="Events", height=400, width=400):
        # optionally create legend
        dpg.add_plot_legend()

        # REQUIRED: create x and y axes
        dpg.add_plot_axis(dpg.mvXAxis, label="x")
        dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")


dpg.create_viewport(title='FEATURES', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()'''