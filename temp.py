def plot_spectrogram_individual(tags, tab_label, func, tab_tag, parameter_values, mode = None):
    window_id = extract_window_id(tab_tag)

    global_min = float("inf")
    global_max = float("-inf")

    all_Sxx = []
    per_rec = {}

    #initialize lists of signals per date
    for tag in tags: 
        date = getSignalbyIdx(window_id,tab_tag,tag,mode=mode)['Date']
        date = f"{date.day:02d}/{date.month:02d} - {date.hour:02d}:{date.minute:02d}"
        per_rec[date] = {}

    for tag in tags:
        stream = getSignalbyIdx(window_id,tab_tag,tag,mode=mode)
        stream_events = getEventsbyTag(tab_tag,tag)
        y = stream['Y']
        parameter_values['x'] = np.array(y)
        date = stream['Date']
        channel = stream['Channel']
        date = f"{date.day:02d}/{date.month:02d} - {date.hour:02d}:{date.minute:02d}"
        signal = pre.call_function(func, parameter_values)

        frequencies, times, Sxx = signal
        per_rec[date] = {channel: signal, 'Events': stream_events}
        Sxx_log = 10 * np.log10(Sxx + 1e-10)  # Convert to dB scale
        Sxx_log = np.flipud(Sxx_log)

        global_min = min(global_min, Sxx_log.min())
        global_max = max(global_max, Sxx_log.max())     
        all_Sxx.append(Sxx_log)
    
    num_plots = len(per_rec.keys())
    num_cols = 1
    num_rows = num_plots

    with dpg.group(horizontal=True, parent=f"{tab_label}", tag=f"{tab_label}_plot_group"):

        dpg.add_colormap_scale(tag=f"{tab_label}_colormap_scale", label="Density", colormap=dpg.mvPlotColormap_Jet,
                                            min_scale = global_min, max_scale=global_max, height=400*num_rows)
        
        def mean_spectrogram(signals, file = None):  

            if isinstance(signals,dict):  
                all_Sxx = []

                events = signals['Events']
                signals.pop('Events',None)
                all_Sxx = [sxx for _, sxx in signals.items()]
            else: 
                all_Sxx = signals
                events = None

            if file == None: 
                title = "Mean Spectrogram"
                subplot_tag = f"{tab_label}_mean"
                mean_Sxx_log = np.mean(np.stack(all_Sxx), axis=0)
            else: 
                all_Sxx = [s[2] for s in all_Sxx]
                mean_Sxx_log = np.mean(np.stack(all_Sxx), axis=0)
                title =f"Mean Spectrogram - File {file}"
                subplot_tag = f"{tab_label}_mean_{file}"
                mean_Sxx_log = 10 * np.log10(mean_Sxx_log + 1e-10)
                mean_Sxx_log = np.flipud(mean_Sxx_log)
            
            shapes = [s.shape for s in all_Sxx]
            times = all_Sxx[0][1]
            if not all(shape == shapes[0] for shape in shapes):
                e = "All spectrograms must have the same time length to compute the mean."
                dpg.add_text(e, parent=f"{tab_label}_plot_group")
                raise ValueError(e)

            with dpg.plot(label=title, width=500, height=400, tag=subplot_tag, parent=f"{tab_label}_merged"):
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Frequency (Hz)")

                # Optional: reuse label_pairs and freq_pairs from earlier, or recalculate
                label_pairs,freq_pairs = (), ()
                if mode:
                    emin = int(dpg.get_value(f"{tab_tag}_emin"))
                    emax = int(dpg.get_value(f"{tab_tag}_emax"))
                    for i in np.arange(0, mean_Sxx_log.shape[0], 0.1):
                        label_pairs += ((f"{(i*(emin+emax)-emin):.1f}", i),)
                else:
                    for i in np.arange(0, mean_Sxx_log.shape[0], 0.1):
                        label_pairs += ((f"{i*len(times):.1f}", i),)
                    
                for i in np.arange(0, mean_Sxx_log.shape[1],0.1): freq_pairs += ((f"{i*125:.0f}", i),) 

                dpg.set_axis_ticks(x_axis, label_pairs)
                dpg.set_axis_ticks(y_axis, freq_pairs)

                dpg.add_heat_series(mean_Sxx_log.flatten(), rows=mean_Sxx_log.shape[0], cols=mean_Sxx_log.shape[1],
                                    scale_min=global_min, scale_max=global_max,
                                    parent=y_axis, format="")
                dpg.bind_colormap(subplot_tag, dpg.mvPlotColormap_Jet)

                if events != None:
                    for event in events:
                        stamp = [event['Idx']/(len(times)*250)] #spectrogram axis is in reality from 0 to 1, and the columns are time based, not sample
                        type = event['Type']
                        dpg.add_plot_legend()
                        dpg.add_inf_line_series(x=stamp,label=f'{type}',parent=y_axis)
                        
                 
        if dpg.does_item_exist(f"{tab_label}_merged"):dpg.delete_item(f"{tab_label}_merged")

        with dpg.subplots(rows=num_rows, columns=num_cols, label="Spectrograms", width=800, height=400*num_rows, tag = f"{tab_label}_merged"):

            if len(per_rec.keys())>1:
                for file, signals in per_rec.items():
                    mean_spectrogram(signals, file=file)
            else:
                mean_spectrogram(all_Sxx)