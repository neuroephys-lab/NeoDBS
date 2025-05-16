
def DefaultFeatures(sender, app_data, user_data):
    tab_tag, signal_tags = user_data
    window_id = extract_window_id(tab_tag)
    wt = extract_type_window(window_id)
    parameter_values = {}

    parameter_values, documentation = fill_params_features(app_data)

    func = app_data

    tags = getActiveSeries(signal_tags)
    events = [getEventsbyTag(tab_tag,serie) for serie in tags]
    if all(e is None for e in events): events = None
    
    if events: mode = 'segment'
    else: mode = None
    
    tab_label = f"{tab_tag}_df_{func}"
    if not dpg.does_item_exist(f"{tab_tag}_features_bar"):
        dpg.add_tab_bar(parent=f"{tab_tag}_features", tag = f"{tab_tag}_features_bar")

    if dpg.does_item_exist(tab_label):
        dpg.delete_item(f"{tab_label}_plot_group")
    else:
        dpg.add_tab(label=f"Default {func}", parent=f"{tab_tag}_features_bar", tag=tab_label)  
    
    dates = []
    for tag in tags: 
        signal = getSignalbyIdx(window_id,tab_tag,tag,mode)
        dates.append(signal['Date'])
    dates = np.unique(dates)

    if len(dates)>1:
        plot_modes = ['Join Recordings', 'Separate Recordings']
    else: plot_modes = [None]  

    continue_flag = True
    if wt == 'Individual': mode = None
    elif mode == None and (func == 'spectrogram' or func == 'wavelet'): 
        dpg.add_text(default_value=f"{func} only available in Combined Analysis for Event-lock based signals", show= True, parent=tab_label)
        continue_flag = False

    if continue_flag == True:
        match func:
            case 'spectrogram': 
                if plot_modes[0] != None:
                    if not dpg.does_item_exist(f"{tab_label}_radio"): dpg.add_radio_button(items=plot_modes,label='Plot Mode', parent=tab_label, callback=choose, user_data=(tags, tab_label, func, tab_tag, parameter_values, mode), tag = f"{tab_label}_radio")
                else: plot_spectrogram_og(tags, tab_label, func, tab_tag, parameter_values, mode)
            
            case 'wavelet': 
                if plot_modes[0] != None:
                    if not dpg.does_item_exist(f"{tab_label}_radio"): dpg.add_radio_button(items=plot_modes,label='Plot Mode', parent=tab_label, callback=choose, user_data=(tags, tab_label, func, tab_tag, parameter_values, mode), tag = f"{tab_label}_radio")
                else: 
                    plot_wavelet(tags, tab_label, func, tab_tag, parameter_values, mode=mode)
            
            case _: plot_filtered_signal(signal_tags, tab_label, func, tab_tag, parameter_values)

def plot_filtered_signal(signal_tags, tab_label, func, tab_tag, parameter_values, mode = None):
    #tab_label = f"{tab_tag}_{func}"
    window_id = extract_window_id(tab_tag)
    tags = getActiveSeries(signal_tags)
    tables, events_tags, events_names, channels, ploted_tags, days = [], [], [], [], [], []
    comparing = False
    if dpg.does_item_exist(f"{tab_label}_bva"): 
        comparing = dpg.get_value(f"{tab_label}_bva")

    dpg.delete_item(f"{tab_label}_plot_group")

    if not 'Data' in app_state['windows'][window_id]:
        if 'Events' in app_state['windows'][window_id]['Files'][-1]['Data'][tab_tag].keys():
            mode = 'segment'
        else: mode = None
    else: mode = None

    with dpg.group(horizontal=True, parent = tab_label,tag=f"{tab_label}_plot_group"):
        with dpg.plot(label=f"Spectral Analysis - {func}", height=400, width=600, tag = f"{tab_label}_plot"):
            dpg.bind_colormap(f"{tab_label}_plot", 0)
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)") #tag=f"{tab_label}_x_axis"
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="LFP Power (µV^2/Hz)", tag= f"{tab_label}_y_axis")

            def contiguous_array(signal, func):
                if func == 'multitaper': 
                    mask = signal[1] <= 100
                    psd = np.ascontiguousarray(signal[0][mask])
                    freqs = np.ascontiguousarray(signal[1][mask])
                else:
                    mask = signal[0] <= 100
                    freqs = np.ascontiguousarray(signal[0][mask])
                    psd = np.ascontiguousarray(signal[1][mask])

                p = {'X': freqs, 'Y': psd}
                return p
            
            power = []
            max_p = 0
            for i,tag in enumerate(tags):
                if mode:
                    stream=getSignalbyIdx(window_id,tab_tag,tag,mode='segment')
                else: stream = getSignalbyIdx(window_id,tab_tag,tag)

                channels.append(stream['Channel']) 
                days.append(stream['Date'])
                series_label = dpg.get_item_configuration(tag)['label']


    	        #BEFORE AND AFTER PSD
                if comparing == True:
                    temp = []
                    zero = [i for i,x in enumerate(stream['X']) if x == 0.0][0]
                    pre_event = stream['Y'][:zero]
                    post_event = stream['Y'][zero:]
                    pre_event = apply_feat(func,parameter_values,pre_event)
                    post_event = apply_feat(func,parameter_values,post_event)
                    
                    #BEFORE-------------------------------------------------
                    p = contiguous_array(pre_event, func)      
                    b_label = 'Before ' + series_label              
                    dpg.add_line_series(p['X'],p['Y'], label=b_label, parent=y_axis, tag = f"{tab_label}_{b_label}_{func}_pre")
                    events_tags.append(f"{tab_label}_{b_label}_{func}_pre")
                    power.append(p)
                    temp.append(p)

                    #AFTER-------------------------------------------------
                    p = contiguous_array(post_event, func)      
                    a_label = 'After ' + series_label              
                    dpg.add_line_series(p['X'],p['Y'], label=a_label, parent=y_axis, tag = f"{tab_label}_{a_label}_{func}_post")
                    events_tags.append(f"{tab_label}_{a_label}_{func}_post")
                    power.append(p)
                    temp.append(p)
                    max_p = max(max_p,np.max(p['Y']))

                    events_names.append(f"{stream['Type']} {i}")
                    states = ['Before', 'After']
                    #TABLE CONTENT
                    full_power = np.sum(p['Y'])

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

                        tables.append(f"{tab_label}_{series_label}_table_{states[i]}")

                #NORMAL PSD
                if comparing == False:
                    y = stream['Y']
                    signal = apply_feat(func,parameter_values,y)
                        
                    p = contiguous_array(signal, func)   
                    power.append(p) 
                    freqs, psd = p['X'], p['Y']      
                    max_p = max(max_p,np.max(p['Y']))         
                    dpg.add_line_series(p['X'],p['Y'], label=series_label, parent=y_axis, tag = f"{tab_label}_{series_label}_{func}")
                    ploted_tags.append(f"{tab_label}_{series_label}_{func}")

                    if not dpg.does_item_exist(f"{tab_label}_{series_label}"):
                        dpg.add_collapsing_header(label = f'{series_label}', tag =f"{tab_label}_{series_label}", parent = tab_label)
                    else:
                        dpg.delete_item(f"{tab_label}_{series_label}", children_only=True)

                    #TABLE CONTENT
                    for band in bands.items():
                        info = extract_psd_features(p, band)
                        create_table(f"{tab_label}_{series_label}",f"{tab_label}_{series_label}_table", info, trial_label=band[0])

                    tables.append(f"{tab_label}_{series_label}_table")

                    updateSignalbyIdx(p,tab_tag,tag,func, mode=mode)
                    
                freqs, psd = p['X'], p['Y']
            
            if len(power)>1:
                
                flag = False
                for i in range(len(power)-1):
                    if len(power[i]['Y']) != len(power[i+1]['Y']): 
                        flag = True
                
                
                if flag == True: #checks if they DON'T have the same len

                    # Define 1-Hz bin edges from 0 to 125 Hz
                    bin_edges = np.arange(0, 100, 1)  # 0–1, 1–2, ..., 124–125
                    bin_centers = bin_edges[:-1] + 0.5

                    # Collect all binned PSDs
                    binned_psds = []

                    for p in power:
                        freqs = p['X']
                        psd = p['Y']
                        
                        binned = []
                        for i in range(len(bin_edges) - 1):
                            fmin, fmax = bin_edges[i], bin_edges[i+1]
                            mask = (freqs >= fmin) & (freqs < fmax)
                            if np.any(mask):
                                binned.append(np.mean(psd[mask]))
                            else:
                                binned.append(np.nan)  # No data in this bin

                        binned_psds.append(binned)

                    # Convert to NumPy array
                    binned_psds = np.array(binned_psds)
                    
                    # Compute mean PSD across trials (ignoring NaNs)
                    all_mean = np.nanmean(binned_psds, axis=0)
                    freqs = np.arange(0,len(all_mean),1)
                
                else: all_mean = np.mean([p['Y'] for p in power], axis=0)

                mean_power = {
                    'Y': all_mean,
                    'X': freqs
                }

                if not dpg.does_item_exist(f"{tab_label}_mean_metric"):
                    dpg.add_collapsing_header(label = 'MEAN POWER', tag =f"{tab_label}_mean_metric", parent = tab_label)
                else:
                    dpg.delete_item(f"{tab_label}_mean_metric", children_only=True)


                for band in bands.items():
                    info = extract_psd_features(mean_power, band)
                    create_table(f"{tab_label}_mean_metric",f"{tab_label}_mean_metric_table", info, trial_label=band[0])

                tables.append(f"{tab_label}_mean_metric_table")

                
                freqs = np.asarray(freqs, dtype=np.float32)
                all_mean = np.asarray(all_mean, dtype=np.float32)
                # all_mean = all_mean*max_p/np.max(all_mean) --> makes it like an envelope, not a mean
                dpg.add_line_series(freqs.tolist(), all_mean.tolist(), label="Mean Power", parent=y_axis, tag=f"{tab_label}_mean")

            dpg.set_axis_limits(x_axis,min(freqs),max(freqs))
            dpg.set_axis_limits(y_axis,min(psd),max(psd))

        def toggle(sender,app_data,user_data):
            axis = user_data
            power_temp = []
            for i, tag in enumerate(events_tags):
                key = str(dpg.get_item_label(sender))
                if axis!=None:
                    key = key.split(' ')[axis]
                if key in tag:
                    dpg.configure_item(tag,show=app_data)

                visibility = dpg.get_item_configuration(tag)['show']
                if visibility==True:
                    power_temp.append(power[i])

            mean_temp = np.mean([p['Y'] for p in power_temp], axis=0)
            dpg.configure_item(f"{tab_label}_mean",y=mean_temp)

        def toggle2(sender,app_data,user_data):
            _ = []
            ch = dpg.get_item_label(sender)
            for tag in ploted_tags:
                if ch in tag:
                    dpg.configure_item(tag, show=app_data)
                flag = dpg.get_item_configuration(tag)['show']
                if flag:
                    _.append(tag)

            array = [dpg.get_value(t)[1] for t in _]
            mean = np.mean(array, axis=0)
            dpg.configure_item(f"{tab_label}_mean",y=mean)


        with dpg.group(parent=f"{tab_tag}_buttons"):
            dpg.add_checkbox(label='Change to dB',callback=Volt2dB, user_data=(signal_tags,tab_tag,func, tab_label, tables), tag = f"{tab_label}_2db")
            if mode == 'segment': 
                dpg.add_checkbox(label='Before vs. After',callback=before_vs_after, user_data=(signal_tags,tab_label,func,tab_tag,parameter_values), tag = f"{tab_label}_bva", default_value=comparing)
            
            if comparing== True:
                dpg.add_separator()
                dpg.add_text('Toggle Streams')
                with dpg.group(parent=f"{tab_tag}_buttons", horizontal=True):   
                    with dpg.group(): #Before and After
                        dpg.add_text('When:')
                        dpg.add_checkbox(label='PSD Before', default_value=True, callback=toggle, user_data=-1)
                        dpg.add_checkbox(label='PSD After', default_value=True, callback=toggle, user_data=-1)
                    
                    with dpg.group(): #Per Event
                        dpg.add_text('Who:')
                        for i, name in enumerate(events_names): 
                            dpg.add_checkbox(label=name, callback=toggle, default_value=True)

                    with dpg.group(): #Per Type of Event
                        events_type = [name.split(' ')[0] for name in events_names]
                        events_type = np.unique(events_type)
                        dpg.add_text('What:')
                        for i, etype in enumerate(events_type):
                            dpg.add_checkbox(label=etype, callback=toggle, default_value=True)
            else:
                channels = np.unique(channels)
                days = np.unique(days)
                dpg.add_text('Toggle Streams')
                with dpg.group(parent=f"{tab_tag}_buttons", horizontal=True):  
                    if len(channels)>1: 
                        with dpg.group(): #channels
                            dpg.add_text('Channels: ')
                            for ch in channels:
                                dpg.add_checkbox(label=ch, callback=toggle2, default_value=True)
                    if len(days)>1:
                        with dpg.group(): #days
                            dpg.add_text('Recordings: ')
                            for d in days:
                                dpg.add_checkbox(label=d, callback=toggle2, default_value=True)
                    with dpg.group(): #side
                        dpg.add_text('Hemisphere: ')
                        sides = ['LEFT', 'RIGHT']
                        for d in sides:
                            dpg.add_checkbox(label=d, callback=toggle2, default_value=True)

    time.sleep(0.2)
    dpg.set_axis_limits_auto(x_axis)
    dpg.set_axis_limits_auto(y_axis)
