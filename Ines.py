
def convert_to_db(value):
    """Convert a value to dB scale using 10 * log10."""
     # if isinstance(value, (list, np.ndarray)):
     #     return [round(10 * np.log10(v +1e-6), 2) for v in value]
    if isinstance(value, (list, np.ndarray,tuple)):  # Handle peak values (power, frequency)
        return (round(10 * np.log10(value[0]+1e-6), 2), value[1])
    elif isinstance(value, (int, float)):
        return round(10 * np.log10(value+1e-6), 2)
    return value  # Return unchanged if it's a string or invalid type
 
def convert_from_db(value):
 
    """Convert a dB value back to linear scale using 10^(dB/10)."""
     # if isinstance(value, (list, np.ndarray,tuple)):  
     #     return [round(10**(v / 10), 2) if v != float('-inf') else 0 for v in value]
 
    if isinstance(value, (list, np.ndarray,tuple)):  # Handle peak values (power, frequency)
        return (round(10**(value[0] / 10), 2) if value[0] != float('-inf') else 0, value[1])
    elif isinstance(value, (int, float)):
        return round(10**(value / 10), 2) if value != float('-inf') else 0
    return value  # Return unchanged if it's a string or invalid type
 
def create_table(tab_label,table_tag,features, trial_label = "New Trial"):

    def add_row():
        with dpg.table_row(parent=table_tag):
            dpg.add_input_text(default_value=trial_label, width=-1)                          
            for band, value in features.items():
                if isinstance(value, (list, np.ndarray, tuple)):  # Check if value is a list or NumPy array
                    if len(value) == 1:  # Single-element array
                        dpg.add_text(f"{float(value[0]):.2f}")  # Convert to float for clean display
                    else:  # Multiple values
                        rounded_values = [float(v) for v in np.round(value, 2)]  # Convert each np.float64 to float
                        dpg.add_text(f"{rounded_values}")  # Display clean list
                elif isinstance(value, str):
                    dpg.add_text(value)
                else:  # Single number case
                    dpg.add_text(f"{float(value):.2f}")  # Ensure it's a clean float

    with dpg.group(parent=tab_label):
                        
        if not dpg.does_item_exist(table_tag):
            with dpg.table(header_row=True, borders_innerH=True, borders_innerV=True, borders_outerH=True, borders_outerV=True, tag=table_tag,label='Relative Band Power'):
                dpg.add_table_column(label="Trial", width=100)                          
                for band in features.keys():
                    dpg.add_table_column(label=band, width=100)
        add_row()
        if not dpg.does_item_exist(f"{table_tag}_save"):
            dpg.add_button(label='Save table', tag = f"{table_tag}_save", callback=save_table_to_file, user_data=(table_tag, 'csv'), parent=tab_label)

def update_table(table_tag, type):
    """Update the table by replacing values with their dB equivalents."""

    if not dpg.does_item_exist(table_tag):
        print(f"Table {table_tag} does not exist!")
        return
 
    children = dpg.get_item_children(table_tag, slot=1)  # Get table rows
 
    if not children:
        print(f"No rows found in {table_tag}.")
 
        return
    
    for row_id in children:  # Iterate through rows
        row_children = dpg.get_item_children(row_id, slot=1)  # Get row items
 
        for i in range(1, len(row_children)):  # Skip first column (Trial)

            value = eval(dpg.get_value(row_children[i]))
            if type == 'dB':
                db_value = convert_to_db(value)
            else: db_value = convert_from_db(value)
          
            if isinstance(db_value, list):  # List case
                dpg.set_value(row_children[i], str(db_value))

            elif isinstance(db_value, tuple):  # Peak case (power, frequency)
                dpg.set_value(row_children[i], f"({db_value[0]}, {value[1]})")
 
            else:  # Single number case
                dpg.set_value(row_children[i], f"{db_value:.2f}")

'''como usei:'''
if not dpg.does_item_exist(f"{tab_label}_{series_label}"):
    dpg.add_collapsing_header(label = f'{series_label}', tag =f"{tab_label}_{series_label}", parent = tab_label)
else:
    dpg.delete_item(f"{tab_label}_{series_label}", children_only=True)

for i,p in enumerate(temp):
    freqs, psd = p['X'], p['Y']
    for b, v in bands.items():
        band = {b: v}
        #mean power per band
        pc = ft.mean_power_all_bands(p, band)
        std = ft.std_dev_streams(p, band)
        mean = {'Mean Power (mean, std. dev)': [np.round(pc[b],2), np.round(std[b],2)]}

        #normalized mean power
        norm_mean = {'% Mean Power (mean, std. dev)': [np.round(pc[b]*100/full_power,2), np.round(std[b],2)]}

        #auc
        params = pre.get_required_params('simpson', module='si')
        param_auc = {}
        for name, param in params.items(): param_auc[name] = param
        mask = (freqs >= v[0]) & (freqs <= v[1])
        param_auc['y'] = psd[mask]
        simpson = pre.call_function('simpson', param_dict=param_auc, module='si')
        auc = {'Sum Power (AUC)': f"{np.round(simpson,2)}"}

        #normalized auc
        norm_auc = {'% Sum Power (AUC)': f"{np.round(simpson*100/full_power,2)}"}

        #peak power
        peak = ft.peak_per_band(p, band)
        picos = {'Peak Power (power, frequency)': p for p in peak.values()}


        info = mean | norm_mean| auc | norm_auc| picos

        if not dpg.does_item_exist(f"{tab_label}_{series_label}_{states[i]}"): dpg.add_text(f"{states[i]}", parent=f"{tab_label}_{series_label}", tag = f"{tab_label}_{series_label}_{states[i]}")
        create_table(f"{tab_label}_{series_label}",f"{tab_label}_{series_label}_table_{states[i]}", info, trial_label=b)