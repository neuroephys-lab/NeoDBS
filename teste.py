import scipy.signal as ss
import Preprocessing as pre
import dearpygui.dearpygui as dpg
import DataHandling as DH
import numpy as np

''' For feature extraction - get all scipy functions'''

#Spectral analysis
spectral_analysis_functions = ['periodogram','welch','coherence','spectrogram','stft'] 

#phase modulation, coherence (phase amplitude coupling) --> se tiver mais que 1 canal

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"
Data = DH.getData(file_path)
stream = DH.getSignals(Data, 'Streaming')[0]


# Dictionary to store user inputs
parameter_values = {}
input_fields = {}  # Store input field IDs


dpg.create_context()

with dpg.window(label="IIR Filter Designer", width=600, height=500):
    dpg.add_text("Select a filter function:")
    param_container = dpg.add_child_window(width=-1, height=300)  # Space to add inputs dynamically

    def create_input_fields(sender, app_data):
        """Dynamically create input fields for selected function."""
        global parameter_values, input_fields
        
        dpg.delete_item(param_container, children_only=True)  # Clear previous inputs
        params = pre.get_required_params(app_data)
        
        if not params:
            dpg.add_text("No parameters found", parent=param_container)
            return
        dpg.add_text("Required parameters: ", parent=param_container)
        parameter_values.clear()  # Reset parameter storage
        input_fields.clear()  # Reset input field storage

        for param, default in params.items():
            input_id = dpg.add_input_text(
                label=param, 
                default_value=str(default) if default is not None else "",
                parent=param_container
            )
            input_fields[param] = input_id  # Store input field reference

        # Add save button
        dpg.add_button(label="Save Parameters", callback=save_parameters, parent=param_container, user_data = app_data)

    def save_parameters(sender, app_data, user_data):
        """Saves input values to the dictionary and prints them."""
        global parameter_values
        parameter_values.clear()  # Reset before saving

        for param, input_id in input_fields.items():
            value = dpg.get_value(input_id)
            parameter_values[param] = value
            print(type(value))

        print("Saved Parameters:", parameter_values)
        dpg.add_button(label="Plot filtered signal", callback=apply_filt, parent=param_container, user_data=user_data)

    def apply_filt(sender, app_data, user_data):
        func = user_data

        x = stream['X']
        y = stream['Y']

        parameter_values['x'] = y
        
        # Assuming call_function takes the filter function and the user-provided parameters
        signal = pre.call_function(func, parameter_values)
        if signal:
            plot_filtered_signal(x, y, signal)
        else: print(signal)

    def plot_filtered_signal(x, y, filtered):
        with dpg.plot(label=f"Signals", height=400, width=600, parent =param_container ):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP amp (microV)", tag="y_axis")
            dpg.add_line_series(x, y, label="Raw", parent="y_axis")
        with dpg.plot(label=f"Spectral Analysis", height=400, width=600, parent =param_container ):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag="xx")
            dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power (dB)", tag="yy")
            dpg.add_line_series(np.ascontiguousarray(filtered[0]),np.ascontiguousarray(filtered[1]), label=f"Filtered", parent="yy")

            
    # Dropdown list for filters
    dpg.add_listbox(
        items=spectral_analysis_functions, 
        label="Filters", 
        callback=create_input_fields
    )

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()