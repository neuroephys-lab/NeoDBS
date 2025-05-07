import DataHandling as DH
import utils as utl
import dearpygui.dearpygui as dpg

base_directory = "C:\\Users\\OCD\\Desktop\\DATA\\RN"  # Change this to your folder path

file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-10-14\\Report_Json_Session_Report_20241125T161803.json"

Data = DH.getData(file_path)

impedance = DH.getImpedance(Data)
if not isinstance(impedance, str):
    status, l, r = impedance

def build_result_table(session_name, session_data):
    # Collect unique electrodes
    electrodes1 = sorted(set(entry["Electrode1"] for entry in session_data))
    electrodes2 = sorted(set(entry["Electrode2"] for entry in session_data))

    # Build lookup
    result_dict = {
        (entry["Electrode2"], entry["Electrode1"]): entry["ResultValue"]
        for entry in session_data
    }

    # Determine min and max for normalization
    all_values = [v for v in result_dict.values()]
    vmin, vmax = min(all_values), max(all_values)
    def normalize(val):
        return (val - vmin) / (vmax - vmin) if vmax > vmin else 0.5

    def value_to_color(value):
        t = normalize(value)
        r = int(255 * t)
        g = int(255 * (1 - t))
        b = 100
        return (r, g, b, 255)
    
    

    with dpg.table(header_row=True, borders_innerH=True, borders_innerV=True,
                   borders_outerH=True, borders_outerV=True, resizable=True, policy=dpg.mvTable_SizingStretchProp):
        # Header
        dpg.add_table_column(label="SenSight")
        for e1 in electrodes1:
            label = utl.after_underscore(e1)
            if label == e1:
                label = utl.after_point(e1)
            dpg.add_table_column(label=label)

        # Rows
        for e2 in electrodes2:
            with dpg.table_row():
                dpg.add_text(utl.after_underscore(e2))
                for e1 in electrodes1:
                    val = result_dict.get((e2, e1), "")
                    if e2 == e1:
                        val = '-'
                    elif val == "":
                        val = result_dict.get((e1, e2), "")
                    dpg.add_text(str(val))

    # with dpg.plot(tag = f'{session_name}'):
    #     dpg.add_plot_legend()
    #     x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
    #     y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

    #     dpg.add_heat_series(all_values, rows=len(electrodes1), cols=len(electrodes2),
    #                             scale_min=vmin, scale_max=vmax, 
    #                             parent=y_axis)
                                            
                    
    #     dpg.bind_colormap(f'{session_name}', dpg.mvPlotColormap_Jet)


# Setup GUI
dpg.create_context()
dpg.create_viewport(title="Electrode Result Tables", width=1200, height=800)

with dpg.window(label="Monopolar", width=-1, height=-1):
    build_result_table("Monopolar", l["Monopolar"])
with dpg.window(label="Bipolar", width=-1, height=-1):
    build_result_table("Bipolar", l["Bipolar"])

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()