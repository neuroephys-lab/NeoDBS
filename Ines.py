'''INES'''

import dearpygui.dearpygui as dpg
from DataHandling import *


def verify_countinous_time(data):

    '''This function receives the data dictionary and returns the corrected version of it.

    The correction is necessary because some values from the beginning of a day are saved in the dictionary entry for a different day.

    For example, there may be LFP values from the first hour of day 24 stored under the dictionary key for day 25.

    Ines Pereira (up202107421)'''

    

    days = list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())

    for d in days:

        for j in reversed(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'][d]):

            if j['DateTime'][0:10] != d[0:10]: 

                for day_ in days:

                    if day_[0:10] == j['DateTime'][0:10]:

                        data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'][day_].insert(0,j)

                        data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'][d].pop(-1)

    

    return data



def info_electrodes(data):

    '''This function receives the data dictionary and returns important information to the user, including:

    - Group_id: indicates which of the four stimulation groups is being used.

    - measured_frequency_Hz: the frequency being measured in Timeline mode.

    - Rate_in_hertz: frequency used in the stimulation.

    - Pulse_width_in_microseconds: the duration of the stimulation pulse.

    - Suspend_amplitude_in_milliamps: the stimulation amplitude.

    - Stimulation_electrodes: the electrodes used for stimulation.

    - Sensing_electrodes: the electrodes used for data recording.

    Ines Pereira (up202107421)'''

    GroupHistory=data['Device']['GroupHistory']

    days_hemisphere_right = list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())

    for dic in GroupHistory:

        if dic['SessionDate'][0:10]==days_hemisphere_right[0][0:10]:

                Groups=dic["Groups"]

                for di in Groups:

                    if di.get("ActiveGroup")==True:

                        Group_id=di["GroupId"][-1]

                        ProgramSettings=di["ProgramSettings"]

                        Rate_in_hertz=ProgramSettings["RateInHertz"]

                        SensingChannel=ProgramSettings['SensingChannel']

                        measured_frequency_Hz = SensingChannel[0]["SensingSetup"]["FrequencyInHertz"]

                        Pulse_width_in_microseconds=SensingChannel[0]["PulseWidthInMicroSecond"]

                        Suspend_amplitude_in_miliamps=SensingChannel[0]["SuspendAmplitudeInMilliAmps"]

                        Stimulation_electrodes_1=SensingChannel[0]["ElectrodeState"]

                        Stimulation_electrodes=[]

                        for d in Stimulation_electrodes_1:

                            Stimulation_electrodes.append(re.split('\.|_',d['Electrode'])[-1]+'-'+d["ElectrodeStateResult"].split('.')[-1])

                        Sensing_electrodes=SensingChannel[0]["Channel"]

                        Sensing_electrodes=Sensing_electrodes.split('.')[-1]

    return Group_id, measured_frequency_Hz, Rate_in_hertz, Pulse_width_in_microseconds, Suspend_amplitude_in_miliamps, Stimulation_electrodes, Sensing_electrodes



def mark_event(data):

    '''This function receives the data dictionary and returns two vectors.

    The vector 'mark_obcessio' contains the date and time of each obsession, in datetime format.

    The vector 'mark_compulsion' contains the date and time of each compulsion, also in datetime format.

    Ines Pereira (up202107421)'''

    LfpFrequencySnapshotEvents = data['Events']['LfpFrequencySnapshotEvents']

    mark_obcession=[]

    mark_compulsion=[]

    days=[]

    for day in list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys()):

        days.append(day[:10])

    for event in LfpFrequencySnapshotEvents:

        if event["DateTime"][:10] in days:

            if event["EventName"]== "Obsessao":

                mark_obcession.append(datetime.strptime(event["DateTime"], "%Y-%m-%dT%H:%M:%SZ"))

            if event["EventName"]== "Compulsao":

                mark_compulsion.append(datetime.strptime(event["DateTime"], "%Y-%m-%dT%H:%M:%SZ"))

    return mark_obcession, mark_compulsion 



def right_hemisphere(data,days):

    '''This function processes data from the right hemisphere of the brain.

    It receives a data dictionary and a list of days to be included in the graph.

    The function returns a dictionary containing:

    - X: time values (including the added points)

    - Y: LFP values (including the added points)

    - X_missing: time points added to account for missing data

    - Y_missing: LFP values added to account for missing data

    Ines Pereira (up202107421)'''

    days_hemisphere_right=list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())

    #days will contain all the days that were choosen to be in plot 

    days_of_search=days

    time_format_somado=[]

    LFP_somado=[]

    red_LFP=[]

    red_time=[]

    if isinstance(days_of_search, list):

        for chosen_day in days_of_search:

            for s in days_hemisphere_right:

                if chosen_day in s:

                    key_chosen_day = s

                    break 

            info_chosen_day= data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'][key_chosen_day]

            size_chosen_day = len(info_chosen_day)

            time_format=[0]*size_chosen_day

            LFP=[0]*size_chosen_day

            i=size_chosen_day

            for t in info_chosen_day:

                LFP[i-1]=int(t['LFP'])

                time_format[i-1]=datetime.fromisoformat(t['DateTime'].rstrip('Z'))

                i=i-1

            #adding the missing points

            index_n_pontos_extra=[]

            for s in range(len(time_format)-1):

                dif=time_format[s+1]-time_format[s]

                dif=dif.seconds

                if dif > 660:

                    n_pontos_extra=(dif//600) - 1

                    index_n_pontos_extra.append(s)

                    index_n_pontos_extra.append(n_pontos_extra)

            n_saltos=[]

            n_saltos=len(index_n_pontos_extra)//2

            LFP_acrescentar=[]

            for i in range(n_saltos):

                index_ponto_acrescentar=index_n_pontos_extra[i*2]

                numero_pontos_acrescentar=index_n_pontos_extra[i*2+1]

                #adding points in y-axis

                min_ponto_acrescentar=LFP[index_ponto_acrescentar]

                max_ponto_acrescentar=LFP[index_ponto_acrescentar+1]

                media_ponto_acrescentar=(min_ponto_acrescentar+max_ponto_acrescentar)/2

                LFP_acrescentar=[media_ponto_acrescentar]*numero_pontos_acrescentar

                LFP[index_ponto_acrescentar+1:index_ponto_acrescentar+1]=LFP_acrescentar

                red_LFP.extend(LFP_acrescentar)

                #adding points in x-axis

                tempo=time_format[index_ponto_acrescentar]

                for j in range(1,numero_pontos_acrescentar+1):

                    tempo=tempo + timedelta(minutes=10)

                    time_format.insert(index_ponto_acrescentar+j,tempo)

                    red_time.append(tempo)

            time_format_somado.extend(time_format)

            LFP_somado.extend(LFP)

    elif isinstance(days_of_search, str):

        for s in days_hemisphere_right:

                if days_of_search in s:

                    key_chosen_day = s

                    break 

        info_chosen_day= data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'][key_chosen_day]

        size_chosen_day = len(info_chosen_day)

        time_format=[0]*size_chosen_day

        LFP=[0]*size_chosen_day

        i=size_chosen_day

        for t in info_chosen_day:

            LFP[i-1]=int(t['LFP'])

            time_format[i-1]=datetime.fromisoformat(t['DateTime'].rstrip('Z'))

            i=i-1

        #adding the missing points

        index_n_pontos_extra=[]

        for s in range(len(time_format)-1):

            dif=time_format[s+1]-time_format[s]

            dif=dif.seconds

            if dif > 660:

                n_pontos_extra=(dif//600) - 1

                index_n_pontos_extra.append(s)

                index_n_pontos_extra.append(n_pontos_extra)

        n_saltos=[]

        n_saltos=len(index_n_pontos_extra)//2

        LFP_acrescentar=[]

        for i in range(n_saltos):

            index_ponto_acrescentar=index_n_pontos_extra[i*2]

            numero_pontos_acrescentar=index_n_pontos_extra[i*2+1]

            #adding points in y-axis

            min_ponto_acrescentar=LFP[index_ponto_acrescentar]

            max_ponto_acrescentar=LFP[index_ponto_acrescentar+1]

            media_ponto_acrescentar=(min_ponto_acrescentar+max_ponto_acrescentar)/2

            LFP_acrescentar=[media_ponto_acrescentar]*numero_pontos_acrescentar

            LFP[index_ponto_acrescentar+1:index_ponto_acrescentar+1]=LFP_acrescentar

            red_LFP.extend(LFP_acrescentar)

            #adding points in x-axis

            tempo=time_format[index_ponto_acrescentar]

            for j in range(1,numero_pontos_acrescentar+1):

                tempo=tempo + timedelta(minutes=10)

                time_format.insert(index_ponto_acrescentar+j,tempo)

                red_time.append(tempo)

        time_format_somado.extend(time_format)

        LFP_somado.extend(LFP)

    new_dic = {'X': time_format_somado, 'Y':LFP_somado,'X_missing':red_time,'Y_missing':red_LFP}   

    return new_dic



def left_hemisphere(data, days):

    '''This function processes data from the left hemisphere of the brain.

    It receives a data dictionary and a list of days to be included in the graph.

    The function returns a dictionary containing:

    - X: time values (including the added points)

    - Y: LFP values (including the added points)

    - X_missing: time points added to account for missing data

    - Y_missing: LFP values added to account for missing data

    Ines Pereira (up202107421)'''

    days_hemisphere_left=list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Left'].keys())

    #days will contain all the days that were choosen to be in plot 

    days_of_search=days 

    time_format_somado=[]

    LFP_somado=[]

    red_LFP=[]

    red_time=[]

    if isinstance(days_of_search, list):

        for day in days_of_search:

            chosen_day = day

            for s in days_hemisphere_left:

                if chosen_day in s:

                    key_chosen_day = s

                    break 

            info_chosen_day = data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Left'][key_chosen_day]

            size_chosen_day = len(info_chosen_day)

            time_format=[0]*size_chosen_day

            LFP=[0]*size_chosen_day

            i=size_chosen_day

            for t in info_chosen_day:

                LFP[i-1]=int(t['LFP'])

                time_format[i-1]=datetime.fromisoformat(t['DateTime'].rstrip('Z'))

                i=i-1

            #adding the missing points 

            index_n_pontos_extra=[]

            for s in range(len(time_format)-1):

                dif=time_format[s+1]-time_format[s]

                dif=dif.seconds

                if dif > 660:

                    n_pontos_extra=(dif//600) - 1

                    index_n_pontos_extra.append(s)

                    index_n_pontos_extra.append(n_pontos_extra)

            n_saltos=len(index_n_pontos_extra)//2

            LFP_acrescentar=[]

            for i in range(n_saltos):

                index_ponto_acrescentar=index_n_pontos_extra[i*2]

                numero_pontos_acrescentar=index_n_pontos_extra[i*2+1]

                #adding the missing points in y-axis

                min_ponto_acrescentar=LFP[index_ponto_acrescentar]

                max_ponto_acrescentar=LFP[index_ponto_acrescentar+1]

                media_ponto_acrescentar=(min_ponto_acrescentar+max_ponto_acrescentar)/2

                LFP_acrescentar=[media_ponto_acrescentar]*numero_pontos_acrescentar

                LFP[index_ponto_acrescentar+1:index_ponto_acrescentar+1]=LFP_acrescentar

                red_LFP.extend(LFP_acrescentar)

                #adding the missing points in x-axis

                tempo=time_format[index_ponto_acrescentar]

                for j in range(1,numero_pontos_acrescentar+1):

                    tempo=tempo + timedelta(minutes=10)

                    time_format.insert(index_ponto_acrescentar+j,tempo)

                    red_time.append(tempo)

            time_format_somado.extend(time_format)

            LFP_somado.extend(LFP)        

    elif isinstance(days_of_search, str):

        for s in days_hemisphere_left:

                if days_of_search in s:

                    key_chosen_day = s

                    break 

        info_chosen_day = data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Left'][key_chosen_day]

        size_chosen_day = len(info_chosen_day)

        time_format=[0]*size_chosen_day

        LFP=[0]*size_chosen_day

        i=size_chosen_day

        for t in info_chosen_day:

            LFP[i-1]=int(t['LFP'])

            time_format[i-1]=datetime.fromisoformat(t['DateTime'].rstrip('Z'))

            i=i-1

        #adding the missing points 

        index_n_pontos_extra=[]

        for s in range(len(time_format)-1):

            dif=time_format[s+1]-time_format[s]

            dif=dif.seconds

            if dif > 660:

                n_pontos_extra=(dif//600) - 1

                index_n_pontos_extra.append(s)

                index_n_pontos_extra.append(n_pontos_extra)

        n_saltos=len(index_n_pontos_extra)//2

        LFP_acrescentar=[]

        for i in range(n_saltos):

            index_ponto_acrescentar=index_n_pontos_extra[i*2]

            numero_pontos_acrescentar=index_n_pontos_extra[i*2+1]

            #adding the missing points in y-axis

            min_ponto_acrescentar=LFP[index_ponto_acrescentar]

            max_ponto_acrescentar=LFP[index_ponto_acrescentar+1]

            media_ponto_acrescentar=(min_ponto_acrescentar+max_ponto_acrescentar)/2

            LFP_acrescentar=[media_ponto_acrescentar]*numero_pontos_acrescentar

            LFP[index_ponto_acrescentar+1:index_ponto_acrescentar+1]=LFP_acrescentar

            red_LFP.extend(LFP_acrescentar)

            #adding the missing points in x-axis

            tempo=time_format[index_ponto_acrescentar]

            for j in range(1,numero_pontos_acrescentar+1):

                tempo=tempo + timedelta(minutes=10)

                time_format.insert(index_ponto_acrescentar+j,tempo)

                red_time.append(tempo)

        time_format_somado.extend(time_format)

        LFP_somado.extend(LFP)  

    new_dic = {'X': time_format_somado, 'Y':LFP_somado,'X_missing':red_time,'Y_missing':red_LFP}  

    return new_dic



def chart_LFP_time(right_dic,left_dic,mark_obcession,mark_compulsion):

    '''This function generates two graphs of LFP values over time, one for each hemisphere of the brain.

    It receives the data dictionary generated by the function right_hemisphere,

    the data dictionary generated by the function left_hemisphere,

    and the vectors generated by the functions mark_obcession and mark_compulsion.

    Each graph displays the LFP signal over time for its respective hemisphere,

    with vertical lines marking the moments of obsessions and compulsions.

    In these graphs, the signals from different days are shown side by side along the time axis, not overlaid.

    Ines Pereira (up202107421)'''

    dpg.create_context()

    # Converting datetime to number of days since begining of data 

    base_date = min(right_dic['X'])

    right_dic['X'] = [date.timestamp() for date in right_dic['X']]

    right_dic['X_missing'] = [date.timestamp() for date in right_dic['X_missing']]

    left_dic['X'] = [date.timestamp() for date in left_dic['X']]

    left_dic['X_missing'] = [date.timestamp() for date in left_dic['X_missing']]



    mark_obcession = [date.timestamp() for date in mark_obcession]

    mark_compulsion = [date.timestamp() for date in mark_compulsion]



    with dpg.window(label="LFP vs Time", pos=(0, 0),tag="Right"):

        

        with dpg.plot(label="LFP vs Time for Right Hemisphere", height=350, width=1500):

            dpg.add_plot_legend()

            side='right'

            

            # Add axes

            x_axis_id = dpg.add_plot_axis(dpg.mvXAxis, label="Time (days)",tag=f"X_axis_not_overlaid_{side}")

            y_axis_id = dpg.add_plot_axis(dpg.mvYAxis, label="LFP",tag=f"Y_axis_not_overlaid_{side}")



            #For the x axis to be in time 

            dpg.configure_item(f"X_axis_not_overlaid_{side}", scale=dpg.mvPlotScale_Time)



            # Add line series to this y-axis

            dpg.add_scatter_series(right_dic['X'], right_dic['Y'], label="LFP vs Time", parent=f"X_axis_not_overlaid_{side}", tag = "LFP_time_right")

            dpg.add_scatter_series(right_dic['X_missing'], right_dic['Y_missing'], label="Added Points", parent=f"X_axis_not_overlaid_{side}", tag="added_points_LFP_time_right")



            #marking the obcessions and compulsions with a line in the graphic of the right hemisphere

            dpg.add_inf_line_series(mark_obcession, label="Obcession", parent=f"X_axis_not_overlaid_{side}")

            dpg.add_inf_line_series(mark_compulsion, label="Compulsion", parent=f"X_axis_not_overlaid_{side}")



            #To create a checkbox to remove the outliers

            dpg.add_checkbox(label="Remove outliers with standard deviations (std) (number of std=3)", default_value=False, callback=toggle_remove_outliers, tag = f"remove_outliers_right", user_data=side, parent= "Right") 

        dpg.add_drag_float(min_value=0, max_value=100, speed=0.2, callback=toggle_remove_outliers_2, default_value=1, user_data=side,label="How many std above the mean are considered outliers? Enter a value above 0.")

        dpg.add_input_float(label="Threshold. Enter a value above 0.", callback=toggle_threshold, format="%.06f", user_data=side)

        dpg.add_checkbox(label="Remove outliers with root mean square (RMS) (number of RMS=3)", default_value=False, callback=toggle_rms, tag = f"remove_outliers_rms_right", user_data=side, parent= "Right") 

        dpg.add_drag_float(min_value=0, max_value=100, speed=0.2, callback=toggle_rms_2, default_value=1, user_data=side,label="How many times the RMS above the RMS value is considered an outlier? Enter a value above 0.")

        dpg.add_checkbox(label="Remove outliers with Interquartile Range (IQR) (limit -> Q3+1.5*IQR)", default_value=False, callback=toggle_iqr, tag = f"remove_outliers_iqr_right", user_data=side, parent= "Right") 



        with dpg.plot(label="LFP vs Time for Left Hemisphere", height=350, width=1500):

            dpg.add_plot_legend()

            side='left'



            # Add axes

            x_axis_id = dpg.add_plot_axis(dpg.mvXAxis, label="Time (days)",tag=f"X_axis_not_overlaid_{side}")

            y_axis_id = dpg.add_plot_axis(dpg.mvYAxis, label="LFP",tag=f"Y_axis_not_overlaid_{side}")



            #For the x axis to be in time 

            dpg.configure_item(f"X_axis_not_overlaid_{side}", scale=dpg.mvPlotScale_Time)



            # Add line series to this y-axis

            dpg.add_scatter_series(left_dic['X'], left_dic['Y'], label="LFP vs Time", parent=f"X_axis_not_overlaid_{side}", tag = "LFP_time_left")

            dpg.add_scatter_series(left_dic['X_missing'], left_dic['Y_missing'], label="Added Points", parent=f"X_axis_not_overlaid_{side}",tag="added_points_LFP_time_left")



            #marking the obcessions and compulsions with a line in the graphic of the left hemisphere

            dpg.add_inf_line_series(mark_obcession, label="Obcession", parent=f"X_axis_not_overlaid_{side}")

            dpg.add_inf_line_series(mark_compulsion, label="Compulsion", parent=f"X_axis_not_overlaid_{side}")



            #To create a checkbox to remove the outliers

            dpg.add_checkbox(label="Remove outliers with standard deviations (std) (number of std=3)", default_value=False, callback=toggle_remove_outliers, tag = f"remove_outliers_left", user_data=side, parent= "Right") 

        dpg.add_drag_float(min_value=0, max_value=100, speed=0.2, callback=toggle_remove_outliers_2, default_value=1, user_data=side,label="How many std above the mean are considered outliers? Enter a value above 0.")

        dpg.add_input_float(label="Threshold. Enter a value above 0.", callback=toggle_threshold, format="%.06f", user_data=side)

        dpg.add_checkbox(label="Remove outliers with root mean square (RMS) (number of RMS=3)", default_value=False, callback=toggle_rms, tag = f"remove_outliers_rms_left", user_data=side, parent= "Right") 

        dpg.add_drag_float(min_value=0, max_value=100, speed=0.2, callback=toggle_rms_2, default_value=1, user_data=side,label="How many times the RMS above the RMS value is considered an outlier? Enter a value above 0.")

        dpg.add_checkbox(label="Remove outliers with Interquartile Range (IQR) (limit -> Q3+1.5*IQR)", default_value=False, callback=toggle_iqr, tag = f"remove_outliers_iqr_left", user_data=side, parent= "Right") 



    dpg.create_viewport(title='Continous time', width=1600, height=1000)

    dpg.setup_dearpygui()

    dpg.show_viewport()

    dpg.start_dearpygui()

    dpg.destroy_context()



def toggle_mean(sender,app_data,user_data):

    '''This function is called whenever the user enables the "Mean and Standard Deviation" checkbox in the LFP vs. time visualization window, where signals from different days are overlaid.

    When the checkbox is active, the function displays a line representing the mean and a shaded area representing the standard deviation on the graph.

    When the checkbox is inactive, both the mean line and the shaded standard deviation area are hidden from the plot.

    Ines Pereira (up202107421)'''

    just_days, side = user_data

    mean_tag = f"mean_chart_{side}" 

    std_tag = f"mean_std_shade_{side}"

    dpg.configure_item(mean_tag, show=app_data)

    dpg.configure_item(std_tag, show=app_data)



    #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated

    dpg.fit_axis_data('y_axis_id_right')

    dpg.fit_axis_data('x_axis_id_right')



    #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated

    dpg.fit_axis_data('y_axis_id_left')

    dpg.fit_axis_data('x_axis_id_left')



def toggle_plot(sender,app_data,user_data):

    '''This function is called whenever the user enables the "Select All" checkbox in the LFP vs. time visualization window, where signals from different days are overlaid.

    When the checkbox is active, all graphs corresponding to each individual day are displayed.

    When the checkbox is inactive, none of the individual daily signals are shown.

    Ines Pereira (up202107421)'''

    days, maxi, side = user_data

    for day in range(0,maxi):

        plot_tag = f"day_{day}_{side}" 

        scatter_tag = f"day_{day}_{side}_added"

        checkbox_tag = f"{day}_checkbox_{side}"

        dpg.configure_item(plot_tag, show=app_data)

        dpg.configure_item(scatter_tag, show=app_data)

        dpg.set_value(checkbox_tag, app_data)



    if  side == 'right':

        days_mean=[]

        for just_day in range(0,maxi):

            plot_tag = f"{just_day}_checkbox_{side}"

            if dpg.get_value(plot_tag) == True:

                days_mean.append(days[just_day])



        if app_data == True:

            mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_right(data,days_mean)

            down_mean_days=[a-a*0.05 for a in mean_days]

            up_mean_days=[a+a*0.05 for a in mean_days]

            dpg.configure_item("mean_chart_right",x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days)

            dpg.configure_item("mean_std_shade_right",x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days)



    if  side == 'left':

        days_mean=[]

        for just_day in range(0,maxi):

            plot_tag = f"{just_day}_checkbox_{side}"

            if dpg.get_value(plot_tag) == True:

                days_mean.append(days[just_day])



        if app_data == True:

            mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_left(data,days_mean)

            down_mean_days=[a-a*0.05 for a in mean_days]

            up_mean_days=[a+a*0.05 for a in mean_days]

            dpg.configure_item("mean_chart_left",x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days)

            dpg.configure_item("mean_std_shade_left",x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days)

            

    #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated

    dpg.fit_axis_data('y_axis_id_right')

    dpg.fit_axis_data('x_axis_id_right')



    #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated

    dpg.fit_axis_data('y_axis_id_left')

    dpg.fit_axis_data('x_axis_id_left')



def toggleType(signal_tags, parent, user_data):

    '''This function is used when the user interacts with a checkbox corresponding to a specific day in the LFP vs. time visualization window, where signals from different days are overlaid.

    When the checkbox for a specific day is unchecked, the signal for that day is removed from the graph.

    When the checkbox is checked again, the signal for that day is displayed once more.

    This allows the user to dynamically control which daily signals are visible in the plot.

    Ines Pereira (up202107421)'''

    checkboxes = {}

    maxi, type_filter, side = user_data #type_filter = number of selected days 



    with dpg.group(parent=parent):

        # Create a checkbox to toggle all matching series at once

        series = []



        def toggle_filtered_series(sender, app_data, user_data, side):

            maxi, type_filter, signal_tags, side = user_data

            global  days

            b=0

            for series_tag in signal_tags:

                series_label = str(dpg.get_item_label(series_tag))

                if (str(type_filter) in series_tag.lower()) and (str(side) in series_tag.lower()) and (b<2):  # Check if the label contains the type

                    b+=1

                    dpg.configure_item(series_tag, show=app_data)

                    series.append(series_tag)

            if  side == 'right':

                days_mean=[]

                for just_day in range(0,maxi):

                    plot_tag = f"{just_day}_checkbox_{side}"

                    if dpg.get_value(plot_tag) == True:

                        days_mean.append(days[just_day])



                mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_right(data,days_mean)

                down_mean_days=[a-a*0.05 for a in mean_days]

                up_mean_days=[a+a*0.05 for a in mean_days]

                dpg.configure_item("mean_chart_right",x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days)

                dpg.configure_item("mean_std_shade_right",x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days)



                #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated

                dpg.fit_axis_data('y_axis_id_right')

                dpg.fit_axis_data('x_axis_id_right')

            

            if side == 'left':

                days_mean=[]

                for just_day in range(0,maxi):

                    plot_tag = f"{just_day}_checkbox_{side}"

                    if dpg.get_value(plot_tag) == True:

                        days_mean.append(days[just_day])

                mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_left(data,days_mean)

                down_mean_days=[a-a*0.05 for a in mean_days]

                up_mean_days=[a+a*0.05 for a in mean_days]

                dpg.configure_item("mean_chart_left",x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days)

                dpg.configure_item("mean_std_shade_left",x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days)



                #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated

                dpg.fit_axis_data('y_axis_id_left')

                dpg.fit_axis_data('x_axis_id_left')



        checkbox = dpg.add_checkbox(label=str(days[type_filter][:10]), default_value=True, callback=toggle_filtered_series, user_data=(maxi, type_filter, signal_tags, side), parent=parent, tag = f"{type_filter}_checkbox_{side}")



        for serie in series: checkboxes[serie] = checkbox



def toggle_deselect_added(sender,app_data,user_data):

    '''This function is called whenever the user enables the "Deselect added points" checkbox in the LFP vs. time visualization window, where signals from different days are overlaid.

    When the checkbox is active, the locations where additional points were inserted are not marked with circles.

    When the checkbox is inactive, those added points are visually marked with circles on the graph.

    Ines Pereira (up202107421)'''

    just_days, side = user_data

    for just_day in range(0,just_days): 

        scatter_tag = f"day_{just_day}_{side}_added"

        dpg.configure_item(scatter_tag, show=not app_data)



    #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated

    dpg.fit_axis_data('y_axis_id_right')

    dpg.fit_axis_data('x_axis_id_right')



    #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated

    dpg.fit_axis_data('y_axis_id_left')

    dpg.fit_axis_data('x_axis_id_left')



def toggle_remove_outliers(sender,app_data,user_data):

    '''This function is called whenever the user clicks on the checkbox "Remove outliers with standard deviations (std) (number of std=3)" in the LFP vs. time visualization window, where signals from different days are aligned in time without overlap.

    When the checkbox is active, the points are considered outliers if their values are above the average plus three times the standard deviation.

    When the checkbox is inactive, no point is considered an outlier.

    Ines Pereira (up202107421)'''

    side=user_data

    dic = f'{side}_dic'

    side_hemisphere = f'{side}_hemisphere'

    dic = globals()[f'{side}_hemisphere'](data, days)

    dic['X'] = [date.timestamp() for date in dic['X']]

    dici = dic.copy()

    if app_data == True:

        mean_for_outliers=np.mean(dici['Y'])

        std_for_outliers=np.std(dici['Y'], ddof=1)

        num_std = 3

        limit_outliers = mean_for_outliers+num_std*std_for_outliers

        old_value = mean_for_outliers

        for i in range(len(dici['Y'])):

            if dici['Y'][i] > limit_outliers:

                dici['Y'][i] = old_value

            if dici['Y'][i] < limit_outliers:

                old_value=dici['Y'][i]

        dpg.configure_item(f"LFP_time_{side}",x = dici['X'], y = dici['Y'])

        dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")

        dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")

        dpg.configure_item(f"added_points_LFP_time_{side}", show=not app_data)

    else:

        dpg.configure_item(f"LFP_time_{side}",x = dic['X'], y = dic['Y'])

        dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")

        dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")

        dpg.configure_item(f"added_points_LFP_time_{side}", show=not app_data)



def toggle_remove_outliers_2(_,app_data,user_data):

    '''This function is called whenever the user changes the value on the drag float with label "How many std above the mean are considered outliers? Enter a value above 0." in the LFP vs. time visualization window, where signals from different days are aligned in time without overlap.

    When the drag float is active, the points are considered outliers if their values are above the average plus x times the standard deviation. X is the value of the drag float.

    When the drag float is inactive, no point is considered an outlier.

    Ines Pereira (up202107421)'''

    side=user_data

    dic = f'{side}_dic'

    dic = globals()[f'{side}_hemisphere'](data, days)

    dic['X'] = [date.timestamp() for date in dic['X']]

    dici = dic.copy()

    num_std = app_data

    mean_for_outliers=np.mean(dici['Y'])

    std_for_outliers=np.std(dici['Y'], ddof=1)

    limit_outliers = mean_for_outliers+num_std*std_for_outliers

    old_value = mean_for_outliers

    for i in range(len(dici['Y'])):

        if dici['Y'][i] > limit_outliers:

            dici['Y'][i] = old_value  

        if dici['Y'][i] < limit_outliers:

            old_value=dici['Y'][i]

            

    dpg.configure_item(f"LFP_time_{side}",x = dici['X'], y = dici['Y'])

    dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")

    dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")

    dpg.configure_item(f"added_points_LFP_time_{side}", show=False)



def toggle_threshold(_,app_data,user_data):

    '''This function is called whenever the user changes the value of the box to add float with label "Threshold. Enter a value above 0." in the LFP vs. time visualization window, where signals from different days are aligned in time without overlap.

    When the box is active, the points are considered outliers if their values are above the threshhold in the box.

    When the box is inactive, no point is considered an outlier.

    Ines Pereira (up202107421)'''

    side=user_data

    dic = f'{side}_dic'

    dic = globals()[f'{side}_hemisphere'](data, days)

    dic['X'] = [date.timestamp() for date in dic['X']]

    dici = dic.copy()

    if app_data<0:

        old_value=0

        num_threshold=0

    else:

        num_threshold = app_data

        old_value = app_data

    for i in range(len(dici['Y'])):

        if dici['Y'][i] > num_threshold:

            dici['Y'][i] = old_value    

        if dici['Y'][i] < num_threshold:

            old_value=dici['Y'][i]

            

    dpg.configure_item(f"LFP_time_{side}",x = dici['X'], y = dici['Y'])

    dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")

    dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")

    dpg.configure_item(f"added_points_LFP_time_{side}", show=False)



def toggle_rms(sender,app_data,user_data):

    '''This function is called whenever the user clicks on the checkbox "Remove outliers with root mean square (RMS) (number of RMS=3)" in the LFP vs. time visualization window, where signals from different days are aligned in time without overlap.

    When the checkbox is active, the points are considered outliers if their values are above the RMS plus three times the RMS.

    When the checkbox is inactive, no point is considered an outlier.

    Ines Pereira (up202107421)'''

    side=user_data

    dic = f'{side}_dic'

    dic = globals()[f'{side}_hemisphere'](data, days)

    dic['X'] = [date.timestamp() for date in dic['X']]

    dici = dic.copy()

    if app_data == True:

        rms = np.sqrt(np.mean(np.array(dici['Y'])**2))

        num_rms = 3

        limit_outliers_rms = rms+num_rms*rms

        old_value = rms

        for i in range(len(dici['Y'])):

            if dici['Y'][i] > limit_outliers_rms:

                dici['Y'][i] = old_value

            if dici['Y'][i] < limit_outliers_rms:

                old_value=dici['Y'][i]

        dpg.configure_item(f"LFP_time_{side}",x = dici['X'], y = dici['Y'])

        dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")

        dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")

        dpg.configure_item(f"added_points_LFP_time_{side}", show=not app_data)

    else:

        dpg.configure_item(f"LFP_time_{side}",x = dic['X'], y = dic['Y'])

        dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")

        dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")

        dpg.configure_item(f"added_points_LFP_time_{side}", show=not app_data)



def toggle_rms_2(_,app_data,user_data):

    '''This function is called whenever the user changes the value on the drag float with label "How many times the RMS above the RMS value is considered an outlier? Enter a value above 0." in the LFP vs. time visualization window, where signals from different days are aligned in time without overlap.

    When the drag float is active, the points are considered outliers if their values are above the RMS plus x times the RMS. X is the value of the drag float.

    When the drag float is inactive, no point is considered an outlier.

    Ines Pereira (up202107421)'''

    side=user_data

    dic = f'{side}_dic'

    dic = globals()[f'{side}_hemisphere'](data, days)

    dic['X'] = [date.timestamp() for date in dic['X']]

    dici = dic.copy()

    num_rms = app_data

    rms = np.sqrt(np.mean(np.array(dici['Y'])**2))

    limit_outliers_rms = rms+num_rms*rms

    old_value = rms

    for i in range(len(dici['Y'])):

        if dici['Y'][i] > limit_outliers_rms:

            dici['Y'][i] = old_value  

        if dici['Y'][i] < limit_outliers_rms:

            old_value=dici['Y'][i]

            

    dpg.configure_item(f"LFP_time_{side}",x = dici['X'], y = dici['Y'])

    dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")

    dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")

    dpg.configure_item(f"added_points_LFP_time_{side}", show=False)



def toggle_iqr(sender,app_data,user_data):

    '''This function is called whenever the user clicks on the checkbox "Remove outliers with Interquartile Range (IQR) (limit -> Q3+1.5*IQR)" in the LFP vs. time visualization window, where signals from different days are aligned in time without overlap.

    When the checkbox is active, the points are considered outliers if their values are above Q3+1.5*IQR (third quartile plus 1.5 times the interquartile range).

    When the checkbox is inactive, no point is considered an outlier.

    Ines Pereira (up202107421)'''

    side=user_data

    dic = f'{side}_dic'

    dic = globals()[f'{side}_hemisphere'](data, days)

    dic['X'] = [date.timestamp() for date in dic['X']]

    dici = dic.copy()

    if app_data == True:

        q1 = np.percentile(dici['Y'], 25)

        q3 = np.percentile(dici['Y'], 75)

        iqr = q3 - q1

        num_iqr = 1.5

        limit_outliers_iqr = q3 + num_iqr * iqr

        old_value = np.median(dici['Y'])

        for i in range(len(dici['Y'])):

            if dici['Y'][i] > limit_outliers_iqr:

                dici['Y'][i] = old_value

            if dici['Y'][i] < limit_outliers_iqr:

                old_value=dici['Y'][i]

        dpg.configure_item(f"LFP_time_{side}",x = dici['X'], y = dici['Y'])

        dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")

        dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")

        dpg.configure_item(f"added_points_LFP_time_{side}", show=not app_data)

    else:

        dpg.configure_item(f"LFP_time_{side}",x = dic['X'], y = dic['Y'])

        dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")

        dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")

        dpg.configure_item(f"added_points_LFP_time_{side}", show=not app_data)



def overlaid_days_average_right(data,days):

    '''This function is used for the right hemisphere of the brain.

    It receives the data dictionary and a list of days to be used for the mean calculation.

    It computes the mean of the LFP values across the selected days in 10-minute intervals,

    and also calculates the standard deviation for each of those intervals.

    It returns four vectors:

    - The mean LFP values at each 10-minute interval,

    - The mean minus the standard deviation at each 10-minute interval,

    - The mean plus the standard deviation at each 10-minute interval,

    - The corresponding time points, from 0 to 24 hours, in 10-minute steps.

    Ines Pereira (up202107421)'''

    time_groups_10_min=[]

    support={}

    for i in range(1,145): #from 1 to 144

        time_groups_10_min.append(i*600)

    for i in range(len(time_groups_10_min)):

        support[str(i)]=[]

    for day in days:

        dic = (right_hemisphere(data, day))

        X=dic['X']

        Y=dic['Y']

        x_in_hours=[]

        base_date = min(X)

        base_date = base_date.replace(hour=0, minute=0, second=0)

        x_in_hours = [(date - base_date).total_seconds() for date in X]

        for i in range(len(x_in_hours)):

            for j in range(len(time_groups_10_min)):

                if x_in_hours[i] < time_groups_10_min[j]:

                    if str(j) in support:

                        support[str(j)].append(Y[i])

                    else:

                        support[str(j)]=[Y[i]]

                    break

    mean_days = []

    mean_less_std_days = []

    mean_plus_std_days =  []

    for a in support:

        if len(support[str(a)])==0:

            mean = 0

            std = 0

            mean_less_std =mean - std

            mean_plus_std = mean + std 

            mean_days.append(mean)

            mean_less_std_days.append(mean_less_std)

            mean_plus_std_days.append(mean_plus_std)

        elif len(support[str(a)])==1:

            mean = np.mean(support[str(a)])

            std = 0

            mean_less_std =mean - std

            mean_plus_std = mean + std 

            mean_days.append(mean)

            mean_less_std_days.append(mean_less_std)

            mean_plus_std_days.append(mean_plus_std)

        else:

            mean = np.mean(support[str(a)])

            std = np.std(support[str(a)], ddof=1)

            mean_less_std =mean - std

            mean_plus_std = mean + std 

            mean_days.append(mean)

            mean_less_std_days.append(mean_less_std)

            mean_plus_std_days.append(mean_plus_std)

    return mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min



def overlaid_days_average_left(data, days):

    '''This function is used for the right hemisphere of the brain.

    It receives the data dictionary and a list of days to be used for the mean calculation.

    It computes the mean of the LFP values across the selected days in 10-minute intervals,

    and also calculates the standard deviation for each of those intervals.

    It returns four vectors:

    - The mean LFP values at each 10-minute interval,

    - The mean minus the standard deviation at each 10-minute interval,

    - The mean plus the standard deviation at each 10-minute interval,

    - The corresponding time points, from 0 to 24 hours, in 10-minute steps.

    Ines Pereira (up202107421)'''

    time_groups_10_min=[]

    support={}

    for i in range(1,145): #from 1 to 144

        time_groups_10_min.append(i*600)

    for i in range(len(time_groups_10_min)):

        support[str(i)]=[]

    for day in days:

        dic = (left_hemisphere(data, day))

        X=dic['X']

        Y=dic['Y']

        x_in_hours=[]

        base_date = min(X)

        base_date = base_date.replace(hour=0, minute=0, second=0)

        x_in_hours = [(date - base_date).total_seconds() for date in X]

        for i in range(len(x_in_hours)):

            for j in range(len(time_groups_10_min)):

                if x_in_hours[i] < time_groups_10_min[j]:

                    if str(j) in support:

                        support[str(j)].append(Y[i])

                    else:

                        support[str(j)]=[Y[i]]

                    break

    mean_days = []

    mean_less_std_days = []

    mean_plus_std_days =  []

    for a in support:

        if len(support[str(a)])==0:

            mean = 0

            std = 0

            mean_less_std =mean - std

            mean_plus_std = mean + std 

            mean_days.append(mean)

            mean_less_std_days.append(mean_less_std)

            mean_plus_std_days.append(mean_plus_std)

        elif len(support[str(a)])==1:

            mean = np.mean(support[str(a)])

            std = 0

            mean_less_std =mean - std

            mean_plus_std = mean + std 

            mean_days.append(mean)

            mean_less_std_days.append(mean_less_std)

            mean_plus_std_days.append(mean_plus_std)

        else:

            mean = np.mean(support[str(a)])

            std = np.std(support[str(a)], ddof=1)

            mean_less_std =mean - std

            mean_plus_std = mean + std 

            mean_days.append(mean)

            mean_less_std_days.append(mean_less_std)

            mean_plus_std_days.append(mean_plus_std)

    return mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min



def chart_overlaid_days(data,days):

    '''This function creates two graphs, one for each hemisphere of the brain.

    In each graph, the LFP values are plotted against time, with the signals from different days overlaid.

    The x-axis represents time, ranging from 0 to 24 hours, and the y-axis represents the LFP values.

    Each graph also includes a line representing the mean and a shaded area corresponding to the standard deviation.

    Ines Pereira (up202107421)'''

    signal_tags = []

    right_dic_overlaid_days=[]

    left_dic_overlaid_days=[]

    for day in days:

        right_dic_overlaid_days.append(right_hemisphere(data, day))

        left_dic_overlaid_days.append(left_hemisphere(data, day))

    dpg.create_context()



    # Converting datetime to number of seconds since begining of data for right hemisphere and left hemisphere

    for d in right_dic_overlaid_days:

        base_date = min(d['X'])

        base_date = base_date.replace(hour=0, minute=0, second=0)

        d['X'] = [(date - base_date).total_seconds() for date in d['X']]

        d['X_missing'] = [(date - base_date).total_seconds() for date in d['X_missing']]

    for d_left in left_dic_overlaid_days:

        base_date = min(d_left['X'])

        d_left['X'] = [(date - base_date).total_seconds() for date in d_left['X']]

        d_left['X_missing'] = [(date - base_date).total_seconds() for date in d_left['X_missing']]



    #Create a theme for the mean and std 

    with dpg.theme() as alpha_theme:

        with dpg.theme_component(0):

            dpg.add_theme_style(dpg.mvPlotStyleVar_FillAlpha, 0.5, category=dpg.mvThemeCat_Plots)



    with dpg.window(label="Right Hemisphere", pos=(0, 0), tag='right'):

        

        with dpg.plot(label="LFP vs Time for Right Hemisphere", height=350, width=1500, tag="plot_right"):

            dpg.add_plot_legend()



            # Add axes

            x_axis_id = dpg.add_plot_axis(dpg.mvXAxis, label="Time (hours)", tag='x_axis_id_right')

            y_axis_id = dpg.add_plot_axis(dpg.mvYAxis, label="LFP", tag='y_axis_id_right')



            #For the x axis to be in time 

            dpg.configure_item('x_axis_id_right', scale=dpg.mvPlotScale_Time)



            a=0

            for right_dic in right_dic_overlaid_days:

                

                # Add line series to this y-axis

                dpg.add_line_series(right_dic['X'], right_dic['Y'], label=str(days[a][:10])+' - LFP vs Time', parent=x_axis_id, tag = f"day_{a}_right")

                dpg.add_scatter_series(right_dic['X_missing'], right_dic['Y_missing'], label=str(days[a][:10])+' - Added Points', parent=x_axis_id, tag = f"day_{a}_right_added")               

                signal_tags.append(f"day_{a}_right")

                signal_tags.append(f"day_{a}_right_added")

                a+=1



            dpg.fit_axis_data('y_axis_id_right')

            dpg.fit_axis_data('x_axis_id_right')



            #To create graphic with mean and standard deviation

            mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_right(data,days)

            down_mean_days=[a-a*0.05 for a in mean_days]

            up_mean_days=[a+a*0.05 for a in mean_days]

            dpg.add_shade_series(x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days, label='Mean', parent=y_axis_id, tag="mean_chart_right")  

            dpg.add_shade_series(x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days, label="Standard Deviation", parent=y_axis_id, tag="mean_std_shade_right")

            #Apply theme to shade

            dpg.bind_item_theme("mean_std_shade_right", alpha_theme)



            maxi=a

            for i in range(0,a):

                toggleType(signal_tags, parent='right', user_data=(maxi,i,'right')) #maxi is the number of selected days in the beggining

            

            dpg.add_checkbox(label="Select All", default_value=True, callback=toggle_plot, tag = f"right_all", parent='right', user_data=(days, a,'right'))

            #To create a checkbox for the mean and standard deviation charts 

            dpg.add_checkbox(label="Mean and Standard Deviation", default_value=True, callback=toggle_mean, tag = f"mean_checkbox_right", parent='right', user_data=(a,'right'))

            #To create a checkbox to deselect the added points

            dpg.add_checkbox(label="Deselect Added Points", default_value=False, callback=toggle_deselect_added, tag = f"deselect_added_checkbox_right", parent='right', user_data=(a,'right')) 



    with dpg.window(label="Left Hemisphere", pos=(0, 450), tag='left'):

    

        with dpg.plot(label="LFP vs Time for Left Hemisphere", height=350, width=1500, tag="plot_left"):

            dpg.add_plot_legend()



            # Add axes

            x_axis_id = dpg.add_plot_axis(dpg.mvXAxis, label="Time (hours)", tag='x_axis_id_left')

            y_axis_id = dpg.add_plot_axis(dpg.mvYAxis, label="LFP", tag='y_axis_id_left')

            

            #For the x axis to be in time 

            dpg.configure_item('x_axis_id_left', scale=dpg.mvPlotScale_Time)



            a=0

            for left_dic in left_dic_overlaid_days:

                

                # Add line series to this y-axis

                dpg.add_line_series(left_dic['X'], left_dic['Y'], label=str(days[a][:10])+' - LFP vs Time', parent=x_axis_id ,tag = f"day_{a}_left" )

                dpg.add_scatter_series(left_dic['X_missing'], left_dic['Y_missing'], label=str(days[a][:10])+' - Added Points', parent=x_axis_id, tag = f"day_{a}_left_added")                

                signal_tags.append(f"day_{a}_left")

                signal_tags.append(f"day_{a}_left_added")

                a+=1

            

            dpg.fit_axis_data('y_axis_id_left')

            dpg.fit_axis_data('x_axis_id_left')



            #To create graphic with mean and standard deviation

            mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_left(data, days)

            down_mean_days=[a-a*0.05 for a in mean_days]

            up_mean_days=[a+a*0.05 for a in mean_days]

            dpg.add_shade_series(x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days, label='Mean', parent=y_axis_id, tag="mean_chart_left")  

            dpg.add_shade_series(x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days, label="Standard Deviation", parent=y_axis_id, tag="mean_std_shade_left")

            dpg.bind_item_theme("mean_std_shade_left", alpha_theme)

            maxi=a

            for i in range(0,a):

                toggleType(signal_tags, parent='left', user_data=(maxi, i,'left')) #maxi is the number of selected days in the beggining



            dpg.add_checkbox(label="Select All", default_value=True, callback=toggle_plot, tag = f"left_all", parent='left', user_data=(days, a,'left'))

            #To create a checkbox for the mean and standard deviation charts 

            dpg.add_checkbox(label="Mean and Standard Deviation", default_value=True, callback=toggle_mean, tag = f"mean_checkbox_left", parent='left', user_data=(a,'left'))

            #To create a checkbox to deselect the added points

            dpg.add_checkbox(label="Deselect Added Points", default_value=False, callback=toggle_deselect_added, tag = f"deselect_added_checkbox_left", parent='left', user_data=(a,'left')) 



    dpg.create_viewport(title='Continous time', width=1600, height=1000)

    dpg.setup_dearpygui()

    dpg.show_viewport()

    dpg.start_dearpygui()

    dpg.destroy_context()



def ask_days_window(possible_days):

    '''This function creates the first window displayed to the user.

    In this window, the user can select the days to be analyzed using one of two methods:

    by choosing a starting day and specifying how many consecutive days to include,

    or by manually selecting individual days through checkboxes.

    Ines Pereira (up202107421)'''

    dpg.create_context(width=1500, height=1500)

    with dpg.window(label="You can select one day and how many days from that day you want or select the days you want to analyse one by one",tag='tag_ask_days_window', width=1500, height=1500, pos=(0,0)):

        dpg.add_text("Change the number of the days or the starting day!",show=False, tag='warning_option1' )

        dpg.add_text("You selected more than one day so the chosen days will be the days you selected!",show=False, tag='warning_option2' )

        dpg.add_text("Select the starting day you want",show=False, tag='warning_option3' )

        dpg.add_text("You can not close the window because your chosen days are not valid!",show=False, tag='warning_option4' )

        dpg.add_text(f'Chosed days: {days}',show=False, tag='chosed_days')

        dpg.add_drag_int(min_value=1, max_value=len(possible_days), speed=0.03, callback=toggle_ask_days, default_value=1, user_data=possible_days, tag='drag_num_days')

        for i in range(len(possible_days)):

            dpg.add_checkbox(default_value=False, callback=toggle_ask_days, tag=f'check_days_{i}', label=possible_days[i], user_data=possible_days)

        dpg.add_button(label="Done", callback=toggle_close_window)

    dpg.create_viewport(title='Choose the days', width=1500, height=1500)

    dpg.setup_dearpygui()

    dpg.show_viewport()

    dpg.start_dearpygui()

    dpg.destroy_context()



def toggle_ask_days(_, app_data, user_data):

    '''This function is called whenever the user checks or unchecks a checkbox in the visualization window to select which days to display.

    It is also called whenever the user adjusts the slicer to choose the number of days to visualize.

    The function generates the list of selected days to be displayed and performs validation to ensure that the chosen combination of days is valid and does not result in any conflicts.

    Ines Pereira (up202107421)'''

    num_of_days=dpg.get_value('drag_num_days')

    possible_days=user_data

    flag_ask_days=0

    dpg.configure_item(f"warning_option4",show=False)

    global days

    days=[]

    for i in range(len(possible_days)):

        state = dpg.get_value(f'check_days_{i}')

        if state == True:

            flag_ask_days+=1

    if flag_ask_days > 1:

        dpg.configure_item(f"warning_option2",show=True) 

        dpg.configure_item(f"warning_option1",show=False) 

        dpg.configure_item(f"warning_option3",show=False) 

        dpg.configure_item('drag_num_days',show=False)

        for i in range(len(possible_days)):

            state = dpg.get_value(f'check_days_{i}')

            if state == True:

                days.append(possible_days[i])  

        dpg.set_value('chosed_days',f'Chosed days: {days}') 

        dpg.configure_item('chosed_days',show=True) 

    elif flag_ask_days==0:

        days=[]

        dpg.configure_item(f"warning_option3",show=True) 

        dpg.configure_item(f"warning_option1",show=False)

        dpg.configure_item(f"warning_option2",show=False)  

        dpg.configure_item('drag_num_days',show=True)  

        dpg.configure_item('chosed_days',show=False) 

    elif flag_ask_days==1:

        dpg.configure_item(f"warning_option2",show=False) 

        dpg.configure_item(f"warning_option3",show=False)  

        dpg.configure_item('drag_num_days',show=True) 

        for i in range(len(possible_days)):

            state = dpg.get_value(f'check_days_{i}')

            if state == True:

                if (len(possible_days)-i) < num_of_days:

                    dpg.configure_item(f"warning_option1",show=True) 

                    dpg.configure_item('chosed_days',show=False) 

                    days=[]

                else:

                    days=possible_days[i:i+num_of_days]

                    dpg.configure_item(f"warning_option1",show=False) 

                    dpg.set_value('chosed_days',f'Chosed days: {days}') 

                    dpg.configure_item('chosed_days',show=True) 



def toggle_close_window():

    '''This function is called whenever the user clicks the "Done" button in the day selection window.

    It verifies whether a valid list of selected days exists.

    If a valid list is found, the window is closed.

    If not, a warning is displayed to inform the user that the selected days are not valid.'''

    global days

    if days == []:

        dpg.configure_item(f"warning_option4",show=True) 

    else:

        all_days=list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())

        for i in range(len(days)):

            for j in range(len(all_days)):

                if days[i] == all_days[j][:10]:

                    days[i]=all_days[j]

        dpg.delete_item('tag_ask_days_window')



def chart_obcession_compulsion(mark_obcession, mark_compulsion, right_dic, left_dic):

    '''This function generates four graphs of LFP values over time, two for each hemisphere of the brain, one for compulsions and one for obcessions.

    It receives the data dictionary generated by the function right_hemisphere (considering all days),

    the data dictionary generated by the function left_hemisphere (considering all days),

    and the vectors generated by the functions mark_obcession and mark_compulsion.

    Each graph displays the LFP signal over time for its respective hemisphere and symptom,

    the number of hours before and after the symptoms can be choosed by the user.

    In these graphs the signals are overlaid.

    Ines Pereira (up202107421)'''

    options = {

    "obcession": mark_obcession,

    "compulsion": mark_compulsion}

    # clean - without obcessions/compulsions that were marked with less then 1 minute intervale 

    options_clean = {

    "obcession": [],

    "compulsion": []}

    symptom = 'obcession'



    for i in range(len(options[symptom])-1): #to not consider obcessions/compulsions that were marked with less then 1 minute intervale 

        dif = options[symptom][i+1] - options[symptom][i]

        dif_sec = dif.total_seconds()

        if (dif_sec > 60) and (i==0):

            options_clean[symptom].append(options[symptom][i])

            options_clean[symptom].append(options[symptom][i+1])

        if (dif_sec <= 60) and (i==0):

            options_clean[symptom].append(options[symptom][i])

        if (dif_sec > 60) and (i!=0) :

            options_clean[symptom].append(options[symptom][i+1])



    symptom = 'compulsion'



    for i in range(len(options[symptom])-1): #to not consider obcessions/compulsions that were marked with less then 1 minute intervale 

        dif = options[symptom][i+1] - options[symptom][i]

        dif_sec = dif.total_seconds()

        if (dif_sec > 60) and (i==0):

            options_clean[symptom].append(options[symptom][i])

            options_clean[symptom].append(options[symptom][i+1])

        if (dif_sec > 60) and (i!=0) :

            options_clean[symptom].append(options[symptom][i+1])



    options_window= {

    "right": {"obcession":[],

    "compulsion": []},

    "left": {"obcession": [],

    "compulsion": []}}

    

    options_side = {

    "right": right_dic,

    "left": left_dic}

 

    time_span_hours=1 #time in hours 

    time_span=time_span_hours*3600 #time in seconds



    sides=['right', 'left']

    symptoms = ['obcession', 'compulsion']



    for side in sides:

        for symptom in symptoms:

            for i in range(len(options_clean[symptom])):

                window_time=[]

                window_LFP=[]

                for j in range(len(options_side[side]['X'])):

                    dif_X = options_side[side]['X'][j] - options_clean[symptom][i] 

                    dif_X_sec = dif_X.total_seconds()

                    if (dif_X_sec <= time_span) and (dif_X_sec >= -time_span):

                        window_time.append(dif_X_sec + 86400)

                        window_LFP.append(options_side[side]['Y'][j])

                options_window[side][symptom].append({"X": window_time,"Y": window_LFP})



    dpg.create_context()

    size_window_h=0

    size_window_v=0



    #Create a theme for the mean and std 

    with dpg.theme() as alpha_theme:

        with dpg.theme_component(0):

            dpg.add_theme_style(dpg.mvPlotStyleVar_FillAlpha, 0.5, category=dpg.mvThemeCat_Plots)



    for side in sides:

        for symptom in symptoms:

            with dpg.window(label=f"{side} hemisphere - {symptom}", pos=(size_window_h, size_window_v), tag=f'{side}_{symptom}'):

                dpg.add_text(f'Choose how many hours before and after you want to analyze the {symptom} signal:')

                dpg.add_drag_int(min_value=1, max_value=12, speed=0.02, callback=toggle_time_span, default_value=1, tag=f'drag_time_span_{side}_{symptom}', user_data=(options_clean, options_side, options_window, side, symptom)) #, user_data=possible_days

                with dpg.plot(label=f"LFP vs Time for {symptom} in {side} hemisphere", height=350, width=1500, tag=f"plot_{side}_{symptom}"):

                    dpg.add_plot_legend()



                    # Add axes

                    dpg.add_plot_axis(dpg.mvXAxis, label="Time (hours)", tag=f'x_axis_id_{side}_{symptom}')

                    dpg.add_plot_axis(dpg.mvYAxis, label="LFP", tag=f'y_axis_id_{side}_{symptom}')



                    #For the x axis to be in time 

                    dpg.configure_item(f'x_axis_id_{side}_{symptom}', scale=dpg.mvPlotScale_Time)

                    num_of_symptoms=[]

                    b=0

                    for side_symptom in options_window[side][symptom]:

                        

                        # Add line series to this y-axis

                        dpg.add_line_series(side_symptom['X'], side_symptom['Y'], label=str(options_clean[symptom][b])+' - LFP vs Time', parent=f'y_axis_id_{side}_{symptom}', tag = f"day_{b}_{side}_{symptom}")

                        num_of_symptoms.append(b)

                        b+=1

                    size_window_h+=450



                    mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min=average_obcession_compulsion(side, symptom, options_window,num_of_symptoms)

                    down_mean_days=[a-a*0.05 for a in mean_days]

                    up_mean_days=[a+a*0.05 for a in mean_days]

                    dpg.add_shade_series(x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days, label='Mean', parent=f'x_axis_id_{side}_{symptom}', tag=f"mean_{side}_{symptom}")  

                    dpg.add_shade_series(x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days, label="Standard Deviation", parent=f'y_axis_id_{side}_{symptom}', tag=f"mean_std_{side}_{symptom}")

                    #Apply theme to shade

                    dpg.bind_item_theme(f"mean_std_{side}_{symptom}", alpha_theme)



                    dpg.fit_axis_data(f'y_axis_id_{side}_{symptom}')

                    dpg.fit_axis_data(f'x_axis_id_{side}_{symptom}')



                    warning_symptoms=''

                    for i in range(len(options_clean[symptom])):

                        flag_1=0

                        warning_symptoms=f'{warning_symptoms}\nFor the {symptom} of day {options_clean[symptom][i].date()} and time {options_clean[symptom][i].time()}:'

                        for j in range(len(options_clean['obcession'])):

                            dif_X = options_clean['obcession'][j] - options_clean[symptom][i] 

                            dif_X_sec = dif_X.total_seconds()

                            if (dif_X_sec <= time_span) and (dif_X_sec >= -time_span) and (dif_X_sec != 0):

                                flag_1+=1

                                warning_symptoms=f"{warning_symptoms}\nThere is an overlaping with the obcession of day {options_clean['obcession'][j].date()} and time {options_clean['obcession'][j].time()}."

                        for j in range(len(options_clean['compulsion'])):

                            dif_X = options_clean['compulsion'][j] - options_clean[symptom][i] 

                            dif_X_sec = dif_X.total_seconds()

                            if (dif_X_sec <= time_span) and (dif_X_sec >= -time_span) and (dif_X_sec != 0):

                                flag_1+=1

                                warning_symptoms=f"{warning_symptoms}\nThere is an overlaping with the compulsion of day {options_clean['compulsion'][j].date()} and time {options_clean['compulsion'][j].time()}."

                        if flag_1==0:

                            warning_symptoms=f"{warning_symptoms}\nThere is no overlaping with other signals."

                    

                for c in range(b):

                    dpg.add_checkbox(default_value=True, label=f'{str(options_clean[symptom][c])}',tag = f"checkbox_day_{c}_{side}_{symptom}", callback=toggle_checkbox_symptoms, user_data=(c, b,side, symptom, options_window))

                dpg.add_checkbox(default_value=True, label=f'Select all',tag = f"checkbox_select_all_{side}_{symptom}", callback=toggle_checkbox_select_all, user_data=(b, side, symptom, options_window))

                dpg.add_checkbox(default_value=True, label=f'Mean and Standard Deviation',tag = f"checkbox_mean_{side}_{symptom}", callback=toggle_checkbox_mean, user_data=(b, side, symptom, options_window))

                dpg.add_text(warning_symptoms, tag = f"warning_{side}_{symptom}")

        size_window_v+=450

        size_window_h=0



    dpg.create_viewport(title='analysis of obsessions and compulsions', width=1600, height=1000)

    dpg.setup_dearpygui()

    dpg.show_viewport()

    dpg.start_dearpygui()

    dpg.destroy_context()



def toggle_time_span(_,app_data,user_data):

    '''This function is called whenever the user changes the value on the drag float to choose the number of hours to analyse in the visualization window to analyse the obcessions and compulsions.

    The value in the drag float is the number of hours before and after to be analysed.

    Ines Pereira (up202107421)'''

    options_clean, options_side, options_window, side, symptom = user_data

    time_span_hours=app_data #time in hours 

    time_span=time_span_hours*3600 #time in seconds

    b=len(options_clean[symptom])

    options_window[side][symptom]=[]

    for i in range(len(options_clean[symptom])):

        window_time=[]

        window_LFP=[]

        for j in range(len(options_side[side]['X'])):

            dif_X = options_side[side]['X'][j] - options_clean[symptom][i]

            dif_X_sec = dif_X.total_seconds()  

            if (dif_X_sec <= time_span) and (dif_X_sec >= -time_span):      

                window_time.append(dif_X_sec + 86400)

                window_LFP.append(options_side[side]['Y'][j])

        options_window[side][symptom].append({"X": window_time,"Y": window_LFP})

        

        dpg.configure_item(f"day_{i}_{side}_{symptom}", x=window_time, y=window_LFP)



    warning_symptoms=''

    for i in range(len(options_clean[symptom])):

        flag_1=0

        warning_symptoms=f'{warning_symptoms}\nFor the {symptom} of day {options_clean[symptom][i].date()} and time {options_clean[symptom][i].time()}:'

        for j in range(len(options_clean['obcession'])):

            dif_X = options_clean['obcession'][j] - options_clean[symptom][i] 

            dif_X_sec = dif_X.total_seconds()

            if (dif_X_sec <= time_span) and (dif_X_sec >= -time_span) and (dif_X_sec != 0):

                flag_1+=1

                warning_symptoms=f"{warning_symptoms}\nThere is an overlaping with the obcession of day {options_clean['obcession'][j].date()} and time {options_clean['obcession'][j].time()}."

        for j in range(len(options_clean['compulsion'])):

            dif_X = options_clean['compulsion'][j] - options_clean[symptom][i] 

            dif_X_sec = dif_X.total_seconds()

            if (dif_X_sec <= time_span) and (dif_X_sec >= -time_span) and (dif_X_sec != 0):

                flag_1+=1

                warning_symptoms=f"{warning_symptoms}\nThere is an overlaping with the compulsion of day {options_clean['compulsion'][j].date()} and time {options_clean['compulsion'][j].time()}."

        if flag_1==0:

            warning_symptoms=f"{warning_symptoms}\nThere is no overlaping with other signals."

    dpg.set_value(f"warning_{side}_{symptom}", warning_symptoms)



    num_of_symptoms=[]

    for i in range(b):

        if dpg.get_value(f"checkbox_day_{i}_{side}_{symptom}") == True:

            num_of_symptoms.append(i)

    mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min=average_obcession_compulsion(side, symptom, options_window, num_of_symptoms)

    down_mean_days=[a-a*0.05 for a in mean_days]

    up_mean_days=[a+a*0.05 for a in mean_days]

    dpg.configure_item(f"mean_{side}_{symptom}",x = time_groups_10_min, y1=up_mean_days, y2=down_mean_days )

    dpg.configure_item(f"mean_std_{side}_{symptom}", x = time_groups_10_min, y1=mean_plus_std_days, y2=mean_less_std_days)

    dpg.fit_axis_data(f'y_axis_id_{side}_{symptom}')

    dpg.fit_axis_data(f'x_axis_id_{side}_{symptom}')



def toggle_checkbox_symptoms(_,app_data,user_data):

    '''This function is called when the user interacts with a checkbox corresponding to a specific symptom in the visualization window to analyse the obcessions and compulsions.

    When the checkbox for a specific symptom is unchecked, the signal for that symptom is removed from the graph.

    When the checkbox is checked again, the signal for that symptom is displayed once more.

    This allows the user to dynamically control which symptom signals are visible in the plot.

    Ines Pereira (up202107421)'''

    c, b, side, symptom, options_window=user_data

    num_of_symptoms=[]

    for i in range(b):

        if dpg.get_value(f"checkbox_day_{i}_{side}_{symptom}") == True:

            num_of_symptoms.append(i)

    mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min=average_obcession_compulsion(side, symptom, options_window, num_of_symptoms)

    down_mean_days=[a-a*0.05 for a in mean_days]

    up_mean_days=[a+a*0.05 for a in mean_days]

    dpg.configure_item(f"mean_{side}_{symptom}",x = time_groups_10_min, y1=up_mean_days, y2=down_mean_days )

    dpg.configure_item(f"mean_std_{side}_{symptom}", x = time_groups_10_min, y1=mean_plus_std_days, y2=mean_less_std_days)

    dpg.configure_item(f"day_{c}_{side}_{symptom}", show=app_data)

    dpg.fit_axis_data(f'y_axis_id_{side}_{symptom}')

    dpg.fit_axis_data(f'x_axis_id_{side}_{symptom}')



def toggle_checkbox_select_all(_,app_data,user_data):

    '''This function is called whenever the user clicks the "Select All" checkbox in the visualization window to analyse the obcessions and compulsions.

    When the checkbox is active, all graphs corresponding to each individual symptom are displayed.

    When the checkbox is inactive, none of the individual symptom signals are shown.

    Ines Pereira (up202107421)'''

    b, side, symptom, options_window=user_data

    num_of_symptoms=[]

    for i in range(b):

        num_of_symptoms.append(i)

        dpg.configure_item(f"day_{i}_{side}_{symptom}", show=app_data)

        dpg.set_value(f"checkbox_day_{i}_{side}_{symptom}", app_data)

    if app_data==True:

        mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min=average_obcession_compulsion(side, symptom, options_window, num_of_symptoms)

        down_mean_days=[a-a*0.05 for a in mean_days]

        up_mean_days=[a+a*0.05 for a in mean_days]

        dpg.configure_item(f"mean_{side}_{symptom}",x = time_groups_10_min, y1=up_mean_days, y2=down_mean_days )

        dpg.configure_item(f"mean_std_{side}_{symptom}", x = time_groups_10_min, y1=mean_plus_std_days, y2=mean_less_std_days)

    dpg.fit_axis_data(f'y_axis_id_{side}_{symptom}')

    dpg.fit_axis_data(f'x_axis_id_{side}_{symptom}')



def average_obcession_compulsion(side, symptom, options_window, num_of_symptoms):

    '''This function is used for each side of the brain and for each symptom (obcession and compulsion).

    It computes the mean of the LFP values across the selected time span in 10-minute intervals,

    and also calculates the standard deviation for each of those intervals.

    It returns four vectors:

    - The mean LFP values at each 10-minute interval,

    - The mean minus the standard deviation at each 10-minute interval,

    - The mean plus the standard deviation at each 10-minute interval,

    - The corresponding time points in 10-minute steps.

    Ines Pereira (up202107421)'''

    time_groups_10_min=[]

    support={}

    num_hours = dpg.get_value(f'drag_time_span_{side}_{symptom}')

    for i in range(int(145-(num_hours*60*60)/600),int(144+(num_hours*60*60)/600 + 1)): #from 1 to (num_hours*2*60*60)/600 

        time_groups_10_min.append(i*600)

    for i in range(len(time_groups_10_min)):

        support[str(i)]=[]

    for i in num_of_symptoms:

        dicti=options_window[side][symptom][i]

        dic = dicti.copy()

        X=dic['X']       

        Y=dic['Y']

        for i in range(len(X)):

            for j in range(len(time_groups_10_min)):

                if X[i] < time_groups_10_min[j]:

                    if str(j) in support:

                        support[str(j)].append(Y[i])

                    else:

                        support[str(j)]=[Y[i]]

                    break

    mean_days = []

    mean_less_std_days = []

    mean_plus_std_days =  []

    for a in support:

        if len(support[str(a)]) > 1:

            mean =np.mean(support[str(a)])

            std = np.std(support[str(a)], ddof=1)

            mean_less_std =mean - std

            mean_plus_std = mean + std 

            mean_days.append(mean)

            mean_less_std_days.append(mean_less_std)

            mean_plus_std_days.append(mean_plus_std)

        elif len(support[str(a)]) == 0:

            mean_days.append(0)

            mean_less_std_days.append(0)

            mean_plus_std_days.append(0)

        elif len(support[str(a)]) == 1:

            mean =np.mean(support[str(a)])

            mean_days.append(mean)

            mean_less_std_days.append(mean)

            mean_plus_std_days.append(mean)

    return mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min



def toggle_checkbox_mean(_,app_data,user_data):

    '''This function is called whenever the user clicks the "Mean and Standard Deviation" checkbox in the visualization window to analyse the obcessions and compulsions.

    When the checkbox is active, the function displays a line representing the mean and a shaded area representing the standard deviation on the graph.

    When the checkbox is inactive, both the mean line and the shaded standard deviation area are hidden from the plot.

    Ines Pereira (up202107421)'''

    b, side, symptom, options_window=user_data

    if app_data==True:

        num_of_symptoms=[]

        for i in range(b):

            if dpg.get_value(f"checkbox_day_{i}_{side}_{symptom}") == True:

                num_of_symptoms.append(i)

        mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min=average_obcession_compulsion(side, symptom, options_window, num_of_symptoms)

        down_mean_days=[a-a*0.05 for a in mean_days]

        up_mean_days=[a+a*0.05 for a in mean_days]

        dpg.configure_item(f"mean_{side}_{symptom}",x = time_groups_10_min, y1=up_mean_days, y2=down_mean_days )

        dpg.configure_item(f"mean_std_{side}_{symptom}", x = time_groups_10_min, y1=mean_plus_std_days, y2=mean_less_std_days)

        dpg.configure_item(f"mean_{side}_{symptom}", show=app_data)

        dpg.configure_item(f"mean_std_{side}_{symptom}", show=app_data)

    else:

        dpg.configure_item(f"mean_{side}_{symptom}", show=app_data)

        dpg.configure_item(f"mean_std_{side}_{symptom}", show=app_data)



    dpg.fit_axis_data(f'y_axis_id_{side}_{symptom}')

    dpg.fit_axis_data(f'x_axis_id_{side}_{symptom}')












file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"


data = getData(file_path) 



data = verify_countinous_time(data)



mark_obcession, mark_compulsion = mark_event(data) #mark_obcession and mark_compulsion are lists of datetime 



possible_days = [key[:10] for key in data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys()]



days=[]



ask_days_window(possible_days)



#print (days)



right_dic = right_hemisphere(data, days)



left_dic = left_hemisphere(data, days)



chart_LFP_time(right_dic,left_dic,mark_obcession,mark_compulsion)



chart_overlaid_days(data,days)



print(info_electrodes(data))



right_dic_all_days = right_hemisphere(data, possible_days)



left_dic_all_days = left_hemisphere(data, possible_days)



chart_obcession_compulsion(mark_obcession, mark_compulsion, right_dic_all_days, left_dic_all_days)
