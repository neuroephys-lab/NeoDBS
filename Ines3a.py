from DataHandling import *
import dearpygui.dearpygui as dpg
import statistics

'''INES'''

def verify_countinous_time(data):
    '''
    Verifies continuos time: if the point belongs to the respective day (some points are lost in days)
    '''
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
    '''
    get info from Active Group if timeline continuous --> doesnt use the previous function
    '''
    GroupHistory=data['Device']['GroupHistory']
    days_hemisphere_right = list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())
    for dic in GroupHistory:
        if dic['SessionDate'][0:10]==days_hemisphere_right[0][0:10]:
                Groups=dic["Groups"]
                #print(Groups[1])
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
    '''
    This function recieves the data dictionary and returns 2 vetors.
    The vector mark_obcession contains the day and time that each obcession happened, this information is in datetime format 
    The vector mark_compulsion contains the day and time that each compulsion happened, this information is in datetime format

    '''
    #Inês Pereira (up202107421)
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
    '''
    This function is for the right hemisphere of the brain
    This function recieves the information in dictionary data and also the days that will appear in the graphic
    This function returns a dictionary, the dictionary have x - time, Y - LFP, 
    X_missing - points in x-axis that will be added due to missing information, 
    Y_missing - points in y-axis that will be added due to missing information
    '''
    #Inês Pereira (up202107421)
    days_hemisphere_right=list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())
    #days will contain all the days that were choosen to be in plot 
    days_of_search=days
    
    time_format_somado=[]
    LFP_somado=[]
    red_LFP=[]
    red_time=[]

    if isinstance(days_of_search, list): #this for cycle needs to be changed so it is a search for key
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
                    #change this to a dictionary so it is [{'pos':s, 'n_extra': n_pontos_extra}]

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
        for s in days_hemisphere_right: #in case of a single day
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
            if dif > 660: #why 660?
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
    '''
    This function is for the left hemisphere of the brain
    This function recieves the information in dictionary data and also the days that will appear in the graphic
    This function returns a dictionary, the dictionary have x - time, Y - LFP, 
    X_missing - points in x-axis that will be added due to missing information, 
    Y_missing - points in y-axis that will be added due to missing information

    Inês Pereira (up202107421)
    '''
    
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

    dpg.create_context()


    # Converting datetime to number of days since begining of data 
    base_date = min(right_dic['X'])
    right_dic['X'] = [date.timestamp() for date in right_dic['X']]
    right_dic['X_missing'] = [date.timestamp() for date in right_dic['X_missing']]
    left_dic['X'] = [date.timestamp() for date in left_dic['X']]
    left_dic['X_missing'] = [date.timestamp() for date in left_dic['X_missing']]

    mark_obcession = [date.timestamp() for date in mark_obcession]
    mark_compulsion = [date.timestamp() for date in mark_compulsion]



    with dpg.window(label="LFP vs Time", pos=(0, 0),tag="Right",):
        
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


            #marking the obcessions and compulsions with a triangle in the graphic of the right hemisphere
            '''max_y_right = max(right_dic['Y'])

            for x in range(len(mark_obcession)):
                dpg.draw_polygon(points=[(mark_obcession[x], max_y_right), (mark_obcession[x]-0.1, 1.1*max_y_right), (mark_obcession[x]+0.1, 1.1*max_y_right),(mark_obcession[x], max_y_right)], color=(0, 255, 0, 255), tag=f'obcession_{x}_{side}')
            for x in range(len(mark_compulsion)):
                dpg.draw_polygon(points=[(mark_compulsion[x], 0.9*max_y_right), (mark_compulsion[x]-0.1, max_y_right), (mark_compulsion[x]+0.1, max_y_right),(mark_compulsion[x], 0.9*max_y_right)], color=(255, 0, 0, 255), tag=f'compulsion_{x}_{side}')'''
            
            #To create a checkbox to remove the outliers
            dpg.add_checkbox(label="Remove outliers (number of std = 3)", default_value=False, callback=toggle_remove_outliers, tag = f"remove_outliers_right", user_data=side, parent= "Right") 
        dpg.add_drag_float(min_value=0, max_value=100, speed=0.2, callback=toggle_remove_outliers_2, default_value=1, user_data=side,label="How many standard deviation above average to consider an outlier?")

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
            

            #marking the obcessions and compulsions with a triangle in the graphic of the left hemisphere
            '''max_y_left = max(left_dic['Y'])
            
            for x in range(len(mark_obcession)):
                dpg.draw_polygon(points=[(mark_obcession[x], max_y_left), (mark_obcession[x]-0.1, 1.1*max_y_left), (mark_obcession[x]+0.1, 1.1*max_y_left),(mark_obcession[x], max_y_left)], color=(0, 255, 0, 255), tag=f'obcession_{x}_{side}')
            for x in range(len(mark_compulsion)):
                dpg.draw_polygon(points=[(mark_compulsion[x], 0.9*max_y_left), (mark_compulsion[x]-0.1, max_y_left), (mark_compulsion[x]+0.1, max_y_left),(mark_compulsion[x], 0.9*max_y_left)], color=(255, 0, 0, 255), tag=f'compulsion_{x}_{side}')
'''
            #To create a checkbox to remove the outliers
            dpg.add_checkbox(label="Remove outliers (number of std = 3)", default_value=False, callback=toggle_remove_outliers, tag = f"remove_outliers_left", user_data=side, parent= "Right") 
        dpg.add_drag_float(min_value=0, max_value=100, speed=0.2, callback=toggle_remove_outliers_2, default_value=1, user_data=side,label="How many standard deviation above average to consider an outlier?")

    dpg.create_viewport(title='Continous time', width=1600, height=1000)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

def toggle_mean(sender,app_data,user_data):
    #days_mean=[]
    just_days, side = user_data
    '''for just_day in range(1,just_days+1):
        plot_tag = f"{just_day}_checkbox_{side}"
        #print(plot_tag)
        if dpg.get_value(plot_tag) == True:
            days_mean.append(list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())[just_day-1])

    #print ('days_mean is  ',days_mean)

    mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_right(data,days_mean)
    dpg.configure_item("mean_chart_right",x=time_groups_10_min, y=mean_days)
    dpg.configure_item("mean_less_std_right",x=time_groups_10_min, y=mean_less_std_days)
    dpg.configure_item("mean_plus_std_right",x=time_groups_10_min, y=mean_plus_std_days)'''
    mean_tag = f"mean_chart_{side}" 
    std_tag = f"mean_std_shade_{side}"
    #plus_tag = f"mean_plus_std_{side}"
    dpg.configure_item(mean_tag, show=app_data)
    dpg.configure_item(std_tag, show=app_data)
    #dpg.configure_item(plus_tag, show=app_data)

'''def toggle_mean_left(sender,app_data,user_data):
    days_mean=[]
    just_days, side = user_data
    for just_day in range(1,just_days+1):
        plot_tag = f"{just_day}_checkbox_{side}"
        #print(plot_tag)
        if dpg.get_value(plot_tag) == True:
            days_mean.append(list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Left'].keys())[just_day-1])

    #print ('days_mean is  ',days_mean)

    mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_left(data,days_mean)
    dpg.configure_item("mean_chart_left",x=time_groups_10_min, y=mean_days)
    dpg.configure_item("mean_less_std_left",x=time_groups_10_min, y=mean_less_std_days)
    dpg.configure_item("mean_plus_std_left",x=time_groups_10_min, y=mean_plus_std_days)
    plot_tag = f"mean_chart_{side}" 
    less_tag = f"mean_less_std_{side}"
    plus_tag = f"mean_plus_std_{side}"
    dpg.configure_item(plot_tag, show=app_data)
    dpg.configure_item(less_tag, show=app_data)
    dpg.configure_item(plus_tag, show=app_data)'''

#ckeckbox to select all
def toggle_plot(sender,app_data,user_data):
    days, side = user_data
    for day in range(0,days):
        plot_tag = f"day_{day}_{side}" 
        scatter_tag = f"day_{day}_{side}_added"
        checkbox_tag = f"{day}_checkbox_{side}"
        dpg.configure_item(plot_tag, show=app_data)
        dpg.configure_item(scatter_tag, show=app_data)
        dpg.set_value(checkbox_tag, app_data)
        #Tentativa da media ir para zero quando se desseleciona todos mas nao fez muito sentido 
        '''mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_right(data,days_mean)
        down_mean_days=[a-a*0.05 for a in mean_days]
        up_mean_days=[a+a*0.05 for a in mean_days]
    time_groups_10_min=[]
    for i in range(1,145): #from 1 to 144
        time_groups_10_min.append(i*600)
    y_zeros = [0]*len(time_groups_10_min)
    dpg.configure_item("mean_chart_right",x = time_groups_10_min, y1=y_zeros, y2=y_zeros)
    dpg.configure_item("mean_std_shade_right",x = time_groups_10_min, y1=y_zeros, y2=y_zeros)
    #dpg.configure_item("mean_chart_right",x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days)
    #dpg.configure_item("mean_std_shade_right",x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days)
    #dpg.configure_item("mean_plus_std_right",x=time_groups_10_min, y=mean_plus_std_days)'''

    #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated
    dpg.fit_axis_data('y_axis_id_right')
    dpg.fit_axis_data('x_axis_id_right')

def toggleType(signal_tags, parent, user_data):

    checkboxes = {}
    maxi, type_filter, side = user_data #type_filter = number of selected days 

    
    with dpg.group(parent=parent):
        # Create a checkbox to toggle all matching series at once
        series = []
             
        def toggle_filtered_series(sender, app_data, user_data, side):
            maxi, type_filter, signal_tags, side = user_data
            global  days
            print('aaaaaaaaa')
            b=0
            print('tp is ',type_filter)
            for series_tag in signal_tags:
                series_label = str(dpg.get_item_label(series_tag))
                print (series_tag, '|', series_label)
                print('tp is ',type_filter)
                if (str(type_filter) in series_tag.lower()) and (str(side) in series_tag.lower()) and (b<2):  # Check if the label contains the type
                    b+=1
                    print('im in position c')
                    dpg.configure_item(series_tag, show=app_data)
                    series.append(series_tag)
            print ('side is ',side)
            if  side == 'right':
                days_mean=[]
            
                for just_day in range(0,maxi):
                    plot_tag = f"{just_day}_checkbox_{side}"
                    #print(plot_tag)
                    print('im in position a')
                    if dpg.get_value(plot_tag) == True:
                        #days_mean.append(list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())[just_day])
                        days_mean.append(days[just_day])
                        print('im in position b')

                print ('days_mean is  ',days_mean)

                mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_right(data,days_mean)
                down_mean_days=[a-a*0.05 for a in mean_days]
                up_mean_days=[a+a*0.05 for a in mean_days]
                dpg.configure_item("mean_chart_right",x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days)
                dpg.configure_item("mean_std_shade_right",x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days)
                #dpg.configure_item("mean_plus_std_right",x=time_groups_10_min, y=mean_plus_std_days)

                #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated
                dpg.fit_axis_data('y_axis_id_right')
                dpg.fit_axis_data('x_axis_id_right')
            

            if side == 'left':
                days_mean=[]
                print ('side is left')
                for just_day in range(0,maxi):
                    plot_tag = f"{just_day}_checkbox_{side}"
                    #print(plot_tag)
                    if dpg.get_value(plot_tag) == True:
                        #days_mean.append(list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Left'].keys())[just_day])
                        days_mean.append(days[just_day])

                print ('days_mean is  ',days_mean)
                print('mean days are', days_mean)
                mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min = overlaid_days_average_left(data,days_mean)
                down_mean_days=[a-a*0.05 for a in mean_days]
                up_mean_days=[a+a*0.05 for a in mean_days]
                dpg.configure_item("mean_chart_left",x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days)
                dpg.configure_item("mean_std_shade_left",x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days)
                #dpg.configure_item("mean_plus_std_left",x=time_groups_10_min, y=mean_plus_std_days)

                #Everytime a plot line is added or removed the x-axis and y-axis limits are recalculated
                dpg.fit_axis_data('y_axis_id_left')
                dpg.fit_axis_data('x_axis_id_left')


        print('THE tp is', type_filter)
        checkbox = dpg.add_checkbox(label=str(days[type_filter][:10]), default_value=True, callback=toggle_filtered_series, user_data=(maxi, type_filter, signal_tags, side), parent=parent, tag = f"{type_filter}_checkbox_{side}")

        for serie in series: checkboxes[serie] = checkbox

def toggle_deselect_added(sender,app_data,user_data):
    just_days, side = user_data

    for just_day in range(0,just_days): 
        scatter_tag = f"day_{just_day}_{side}_added"
        dpg.configure_item(scatter_tag, show=not app_data)

def toggle_remove_outliers(sender,app_data,user_data):
    #dici=right_hemisphere(data,days)
    #right_dic = user_data
    side=user_data
    dic = f'{side}_dic'
    side_hemisphere = f'{side}_hemisphere'
    dic = globals()[f'{side}_hemisphere'](data, days)
    base_date = min(dic['X'])
    dic['X'] = [date.timestamp() for date in dic['X']]
    #marking when the obcessions and compulsions happened with a triangle 
    '''mark_obcession, mark_compulsion = mark_event(data)
    mark_obcession = [(date - base_date).total_seconds() / 86400.0 for date in mark_obcession]
    mark_compulsion = [(date - base_date).total_seconds() / 86400.0 for date in mark_compulsion]'''
    dici = dic.copy()
    #breakpoint()
    if app_data == True:
        #dici=user_data
        mean_for_outliers=statistics.mean(dici['Y'])
        std_for_outliers=statistics.stdev(dici['Y'])
        num_std = 3 #default value for outliers
        limit_outliers = mean_for_outliers+num_std*std_for_outliers
        # print(limit_outliers)
        # print(mean_for_outliers)
        old_value = mean_for_outliers

        for i in range(len(dici['Y'])):
            if dici['Y'][i] > limit_outliers:
                dici['Y'][i] = old_value
            if dici['Y'][i] < limit_outliers:
                old_value=dici['Y'][i]

        #marking when the obcessions and compulsions happened with a triangle 
        '''max_y = max(dici['Y'])
        for x in range(len(mark_obcession)):
            dpg.configure_item(f"obcession_{x}_{side}",points=[(mark_obcession[x], max_y), (mark_obcession[x]-0.1, 1.1*max_y), (mark_obcession[x]+0.1, 1.1*max_y),(mark_obcession[x], max_y)])
        for x in range(len(mark_compulsion)):
            dpg.configure_item(f"compulsion_{x}_{side}",points=[(mark_compulsion[x], 0.9*max_y), (mark_compulsion[x]-0.1, max_y), (mark_compulsion[x]+0.1, max_y),(mark_compulsion[x], 0.9*max_y)])'''
        
        dpg.configure_item(f"LFP_time_{side}",x = dici['X'], y = dici['Y'])
        dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")
        dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")
        dpg.configure_item(f"added_points_LFP_time_{side}", show=not app_data)
    else:
        #marking when the obcessions and compulsions happened with a triangle 
        '''max_y = max(dici['Y'])
        for x in range(len(mark_obcession)):
            dpg.configure_item(f"obcession_{x}_{side}",points=[(mark_obcession[x], max_y), (mark_obcession[x]-0.1, 1.1*max_y), (mark_obcession[x]+0.1, 1.1*max_y),(mark_obcession[x], max_y)])
        for x in range(len(mark_compulsion)):
            dpg.configure_item(f"compulsion_{x}_{side}",points=[(mark_compulsion[x], 0.9*max_y), (mark_compulsion[x]-0.1, max_y), (mark_compulsion[x]+0.1, max_y),(mark_compulsion[x], 0.9*max_y)])'''

        dpg.configure_item(f"LFP_time_{side}",x = dic['X'], y = dic['Y'])
        dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")
        dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")
        dpg.configure_item(f"added_points_LFP_time_{side}", show=not app_data)

def toggle_remove_outliers_2(_,app_data,user_data):
    #dici=right_hemisphere(data,days)
    #right_dic = user_data
    side=user_data
    dic = f'{side}_dic'
    side_hemisphere = f'{side}_hemisphere'
    dic = globals()[f'{side}_hemisphere'](data, days)
    base_date = min(dic['X'])
    dic['X'] = [date.timestamp() for date in dic['X']]
    #marking when the obcessions and compulsions happened with a triangle 
    '''mark_obcession, mark_compulsion = mark_event(data)
    mark_obcession = [(date - base_date).total_seconds() / 86400.0 for date in mark_obcession]
    mark_compulsion = [(date - base_date).total_seconds() / 86400.0 for date in mark_compulsion]'''
    dici = dic.copy()
    #breakpoint()
    num_std = app_data
    #print(num_std)
    #if app_data == True:
        #dici=user_data
    mean_for_outliers=statistics.mean(dici['Y'])
    std_for_outliers=statistics.stdev(dici['Y'])
    limit_outliers = mean_for_outliers+num_std*std_for_outliers
    #print(limit_outliers)
    # print(limit_outliers)
    # print(mean_for_outliers)
    old_value = mean_for_outliers

    for i in range(len(dici['Y'])):
        if dici['Y'][i] > limit_outliers:
            dici['Y'][i] = old_value
            
        if dici['Y'][i] < limit_outliers:
            old_value=dici['Y'][i]
            

    #marking when the obcessions and compulsions happened with a triangle 
    '''max_y = max(dici['Y'])
    for x in range(len(mark_obcession)):
        dpg.configure_item(f"obcession_{x}_{side}",points=[(mark_obcession[x], max_y), (mark_obcession[x]-0.1, 1.1*max_y), (mark_obcession[x]+0.1, 1.1*max_y),(mark_obcession[x], max_y)])
    for x in range(len(mark_compulsion)):
        dpg.configure_item(f"compulsion_{x}_{side}",points=[(mark_compulsion[x], 0.9*max_y), (mark_compulsion[x]-0.1, max_y), (mark_compulsion[x]+0.1, max_y),(mark_compulsion[x], 0.9*max_y)])'''
        
    dpg.configure_item(f"LFP_time_{side}",x = dici['X'], y = dici['Y'])
    dpg.fit_axis_data(f"Y_axis_not_overlaid_{side}")
    dpg.fit_axis_data(f"X_axis_not_overlaid_{side}")
    dpg.configure_item(f"added_points_LFP_time_{side}", show=False)

'''def toggle_all(sender, app_data, user_data):
    checkboxes = user_data
    print('aaaaaa')
    print(checkboxes)
    for tag, checkbox in checkboxes.items():
        dpg.set_value(checkbox, app_data)
        dpg.configure_item(tag, show=app_data)'''

def overlaid_days_average_right(data,days):
    right_dic_overlaid_days=[]
    left_dic_overlaid_days=[]
    time_groups_10_min=[]
    support={}

    for i in range(1,145): #from 1 to 144
        time_groups_10_min.append(i*600)

    for i in range(len(time_groups_10_min)):
        support[str(i)]=[]

    for day in days:
        dic = (right_hemisphere(data, day))
        #print (dic)
        X=dic['X']
        Y=dic['Y']
        x_in_hours=[]
        base_date = min(X)
        base_date = base_date.replace(hour=0, minute=0, second=0)
        #x_in_hours = [date.timestamp() for date in X]
        x_in_hours = [(date - base_date).total_seconds() for date in X]
        #print(len(time_groups_10_min))
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
        mean = statistics.mean(support[str(a)])
        std = statistics.stdev(support[str(a)])
        mean_less_std =mean - std
        mean_plus_std = mean + std 
        mean_days.append(mean)
        mean_less_std_days.append(mean_less_std)
        mean_plus_std_days.append(mean_plus_std)

    return mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min

def overlaid_days_average_left(data, days):
    right_dic_overlaid_days=[]
    left_dic_overlaid_days=[]
    time_groups_10_min=[]
    support={}
    for i in range(1,145): #from 1 to 144
        time_groups_10_min.append(i*600)

    for i in range(len(time_groups_10_min)):
        support[str(i)]=[]

    for day in days:
        dic = (left_hemisphere(data, day))
        #print (dic)
        X=dic['X']
        Y=dic['Y']
        x_in_hours=[]
        base_date = min(X)
        base_date = base_date.replace(hour=0, minute=0, second=0)
        x_in_hours = [(date - base_date).total_seconds() for date in X]
        #print(len(time_groups_10_min))
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
        mean = statistics.mean(support[str(a)])
        std = statistics.stdev(support[str(a)])
        mean_less_std =mean - std
        mean_plus_std = mean + std 
        mean_days.append(mean)
        mean_less_std_days.append(mean_less_std)
        mean_plus_std_days.append(mean_plus_std)

    return mean_days, mean_less_std_days, mean_plus_std_days, time_groups_10_min

def chart_overlaid_days(data,days):
    signal_tags = []
    right_dic_overlaid_days=[]
    left_dic_overlaid_days=[]
    for day in days:
        right_dic_overlaid_days.append(right_hemisphere(data, day))
        left_dic_overlaid_days.append(left_hemisphere(data, day))
    dpg.create_context()
    
    #print(left_dic_overlaid_days[0])

    # Converting datetime to number of seconds since begining of data for right hemisphere and left hemisphere
    for d in right_dic_overlaid_days:
        #print(d)
        base_date = min(d['X'])
        #print(base_date)
        base_date = base_date.replace(hour=0, minute=0, second=0)
        d['X'] = [(date - base_date).total_seconds() for date in d['X']]
        d['X_missing'] = [(date - base_date).total_seconds() for date in d['X_missing']]
    for d_left in left_dic_overlaid_days:
        base_date = min(d_left['X'])
        d_left['X'] = [(date - base_date).total_seconds() for date in d_left['X']]
        d_left['X_missing'] = [(date - base_date).total_seconds() for date in d_left['X_missing']]

        '''d['X'] = [date.timestamp() for date in d['X']]
        d['X_missing'] = [date.timestamp() for date in d['X_missing']]'''

    #Create a theme for the mean and std 
    with dpg.theme() as alpha_theme:
        with dpg.theme_component(0):
            dpg.add_theme_style(dpg.mvPlotStyleVar_FillAlpha, 0.5, category=dpg.mvThemeCat_Plots)


    with dpg.window(label="Right Hemisphere", pos=(0, 0), tag='right'):
        
        #Create a theme for the mean and std 
        '''with dpg.theme() as alpha_theme:
            with dpg.theme_component(0):
                dpg.add_theme_style(dpg.mvPlotStyleVar_FillAlpha, 0.5, category=dpg.mvThemeCat_Plots)'''
        
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
            #dpg.add_line_series(time_groups_10_min, mean_days, label='mean right hemisphere', parent=x_axis_id, tag = "mean_chart_right")
            dpg.add_shade_series(x = time_groups_10_min, y1=down_mean_days, y2=up_mean_days, label='Mean', parent=y_axis_id, tag="mean_chart_right")  
            #dpg.add_line_series(time_groups_10_min, mean_less_std_days, label='mean - std', parent=x_axis_id, tag = "mean_less_std_right")
            #dpg.add_line_series(time_groups_10_min, mean_plus_std_days, label='mean + std', parent=x_axis_id, tag = "mean_plus_std_right")
            dpg.add_shade_series(x = time_groups_10_min, y1=mean_less_std_days, y2=mean_plus_std_days, label="Standard Deviation", parent=y_axis_id, tag="mean_std_shade_right")
            #Apply theme to shade
            dpg.bind_item_theme("mean_std_shade_right", alpha_theme)

            maxi=a
            for i in range(0,a):
                toggleType(signal_tags, parent='right', user_data=(maxi,i,'right')) #maxi is the number of selected days in the beggining
                #print (i, '|', signal_tags)
               


            dpg.add_checkbox(label="Select All", default_value=True, callback=toggle_plot, tag = f"right_all", parent='right', user_data=(a,'right'))
            #To create a checkbox for the mean and standard deviation charts 
            dpg.add_checkbox(label="Mean and Standard Deviation", default_value=True, callback=toggle_mean, tag = f"mean_checkbox_right", parent='right', user_data=(a,'right'))
            #To create a checkbox to deselect the added points
            dpg.add_checkbox(label="Deselect Added Points", default_value=False, callback=toggle_deselect_added, tag = f"deselect_added_checkbox_right", parent='right', user_data=(a,'right')) 
            #To create a checkbox to remove the outliers
            #dpg.add_checkbox(label="Remove outliers", default_value=False, callback=toggle_remove_outliers, tag = f"remove_outliers_right", parent='right', user_data=(a,'right')) 
            

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
            '''dpg.add_line_series(time_groups_10_min, mean_days, label='mean left hemisphere', parent=x_axis_id, tag = "mean_chart_left")   
            dpg.add_line_series(time_groups_10_min, mean_less_std_days, label='mean - std', parent=x_axis_id, tag = "mean_less_std_left")
            dpg.add_line_series(time_groups_10_min, mean_plus_std_days, label='mean + std', parent=x_axis_id, tag = "mean_plus_std_left")'''
            dpg.bind_item_theme("mean_std_shade_left", alpha_theme)
            maxi=a
            for i in range(0,a):
                toggleType(signal_tags, parent='left', user_data=(maxi, i,'left')) #maxi is the number of selected days in the beggining

            dpg.add_checkbox(label="Select All", default_value=True, callback=toggle_plot, tag = f"left_all", parent='left', user_data=(a,'left'))
            #To create a checkbox for the mean and standard deviation charts 
            dpg.add_checkbox(label="Mean and Standard Deviation", default_value=True, callback=toggle_mean, tag = f"mean_checkbox_left", parent='left', user_data=(a,'left'))
            #To create a checkbox to deselect the added points
            dpg.add_checkbox(label="Deselect Added Points", default_value=False, callback=toggle_deselect_added, tag = f"deselect_added_checkbox_left", parent='left', user_data=(a,'left')) 
            

    
    dpg.create_viewport(title='Continous time', width=1600, height=1000)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

        




    #X = time_groups_10_min


    
    



            


    

        #left_dic_overlaid_days.append(left_hemisphere(data, day))

def ask_days_window(possible_days):
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
                #print(days)     
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
                    #print(days)
                    dpg.configure_item(f"warning_option1",show=False) 
                    dpg.set_value('chosed_days',f'Chosed days: {days}') 
                    dpg.configure_item('chosed_days',show=True) 

def toggle_close_window():
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
    options = {
    "obcession": mark_obcession,
    "compulsion": mark_compulsion}
    # clean - without obcessions / compulsions that were marked with less then 1 minute intervale 
   
    options_clean = {
    "obcession": [],
    "compulsion": []}
    
    symptom = 'obcession'

    for i in range(len(options[symptom])-1): #to not consider obcessions / compulsions that were marked with less then 1 minute intervale 
        dif = options[symptom][i+1] - options[symptom][i]
        dif_sec = dif.total_seconds()
        if (dif_sec > 60) and (i==0):
            options_clean[symptom].append(options[symptom][i])
            options_clean[symptom].append(options[symptom][i+1])
        if (dif_sec > 60) and (i!=0) :
            options_clean[symptom].append(options[symptom][i+1])


    symptom = 'compulsion'

    for i in range(len(options[symptom])-1): #to not consider obcessions / compulsions that were marked with less then 1 minute intervale 
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


    side='right'
    symptom = 'obcession'

    for i in range(len(options_clean[symptom])):
        dif = 1200
        for j in range(len(options_side[side]['X'])):
            dif_X = options_clean[symptom][i] - options_side[side]['X'][j]
            dif_X = dif_X.total_seconds()
            if dif_X >= 0:
                flag=1
            else:
                flag=0
            dif_X_sec = abs(dif_X)
            if dif_X_sec < dif:
                dif = dif_X_sec
                closer_time_index = j 
                if flag==1:
                    window_time = options_side[side]['X'][j-5:j+6+1]
                    window_LFP = options_side[side]['Y'][j-5:j+6+1]
                if flag==0:
                    window_time = options_side[side]['X'][j-6:j+5+1]
                    window_LFP = options_side[side]['Y'][j-6:j+5+1]

        options_window[side][symptom].append({"time": window_time,"LFP": window_LFP})


    side='right'
    symptom = 'compulsion'

    for i in range(len(options_clean[symptom])):
        dif = 1200
        for j in range(len(options_side[side]['X'])):
            dif_X = options_clean[symptom][i] - options_side[side]['X'][j]
            dif_X = dif_X.total_seconds()
            if dif_X >= 0:
                flag=1
            else:
                flag=0
            dif_X_sec = abs(dif_X)
            if dif_X_sec < dif:
                dif = dif_X_sec
                closer_time_index = j 
                if flag==1:
                    window_time = options_side[side]['X'][j-5:j+6+1]
                    window_LFP = options_side[side]['Y'][j-5:j+6+1]
                if flag==0:
                    window_time = options_side[side]['X'][j-6:j+5+1]
                    window_LFP = options_side[side]['Y'][j-6:j+5+1]

        options_window[side][symptom].append({"time": window_time,"LFP": window_LFP})


    side='left'
    symptom = 'obcession'

    for i in range(len(options_clean[symptom])):
        dif = 1200
        for j in range(len(options_side[side]['X'])):
            dif_X = options_clean[symptom][i] - options_side[side]['X'][j]
            dif_X = dif_X.total_seconds()
            if dif_X >= 0:
                flag=1
            else:
                flag=0
            dif_X_sec = abs(dif_X)
            if dif_X_sec < dif:
                dif = dif_X_sec
                closer_time_index = j 
                if flag==1:
                    window_time = options_side[side]['X'][j-5:j+6+1]
                    window_LFP = options_side[side]['Y'][j-5:j+6+1]
                if flag==0:
                    window_time = options_side[side]['X'][j-6:j+5+1]
                    window_LFP = options_side[side]['Y'][j-6:j+5+1]

        options_window[side][symptom].append({"time": window_time,"LFP": window_LFP})
  
   
  
    side='left'
    symptom = 'compulsion'

    for i in range(len(options_clean[symptom])):
        dif = 1200
        for j in range(len(options_side[side]['X'])):
            dif_X = options_clean[symptom][i] - options_side[side]['X'][j]
            dif_X = dif_X.total_seconds()
            if dif_X >= 0:
                flag=1
            else:
                flag=0
            dif_X_sec = abs(dif_X)
            if dif_X_sec < dif:
                dif = dif_X_sec
                closer_time_index = j 
                if flag==1:
                    window_time = options_side[side]['X'][j-5:j+6+1]
                    window_LFP = options_side[side]['Y'][j-5:j+6+1]
                if flag==0:
                    window_time = options_side[side]['X'][j-6:j+5+1]
                    window_LFP = options_side[side]['Y'][j-6:j+5+1]

        options_window[side][symptom].append({"time": window_time,"LFP": window_LFP})


# file_path = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"

file_path = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2024-10-14\\Report_Json_Session_Report_20241125T162143.json"

data = getData(file_path) 

data = verify_countinous_time(data)

mark_obcession, mark_compulsion = mark_event(data) #mark_obcession and mark_compulsion are lists of datetime 
#print(mark_obcession) 

#days=['2024-10-24','2024-10-25','2024-10-26','2024-10-27','2024-10-28','2024-10-29','2024-10-30','2024-10-31','2024-11-01','2024-11-02','2024-11-03','2024-11-04','2024-11-05','2024-11-06','2024-11-07','2024-11-08']
possible_days = [key[:10] for key in data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys()]
#days = list(data['Timeline']['LFPTrendLogs']['HemisphereLocationDef.Right'].keys())
#days=['2024-10-28','2024-10-29','2024-10-30']

days=[]

ask_days_window(possible_days)

print (days)

right_dic = right_hemisphere(data, days)

left_dic = left_hemisphere(data, days)

chart_LFP_time(right_dic,left_dic,mark_obcession,mark_compulsion)

chart_overlaid_days(data,days)

print(info_electrodes(data))

#this function is to have graphic of 1 hour before and after compulsion/obsession but I am still working on it 
#chart_obcession_compulsion(mark_obcession, mark_compulsion, right_dic, left_dic)


