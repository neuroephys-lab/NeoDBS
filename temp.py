import DataHandling as DH
import dearpygui.dearpygui as dpg
import utils as utl
import numpy as np
from datetime import datetime
'''
BASE

dpg.create_context()
with dpg.window():

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
'''

# # file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"
# file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
# # file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"
# Data = DH.getData(file_path=file)
# events = DH.getSignals(Data,'Events')
# temp = DH.getEventLog(Data)
# daylight_savings = DH.extract_time_offset(Data)


# previous_session = utl.parse_datetime(DH.getLastSessionDate(Data)).date()
# names = [event['EventName'] for event in temp]
# names = np.unique(names).tolist()
# event_summary = {name: {} for name in names}
# for event in temp:
#     # if utl.parse_datetime(previous_session).date()>utl.parse_datetime(event['DateTime']).date(): continue
#     if event['DateTime'] in event_summary[event['EventName']].keys():
#         event_summary[event['EventName']][event['DateTime']] = event_summary[event['EventName']][event['DateTime']] +1
#     else:
#         event_summary[event['EventName']][event['DateTime']] = 1

# def show_selected_date(sender, data):
#     # Get the selected date from the date picker
#     date = dpg.get_value("##datepicker")
#     new_date = datetime(year=date['year']+1900,month=date['month']+1,day=date['month_day']).date() #C-style time struct
#     old_date = dpg.get_value("selected_date_text")
#     if new_date==old_date: return
#     dpg.delete_item('Events',children_only=True)
#     dpg.set_value("selected_date_text",new_date)
#     count = 0
#     plot_events = {}
#     for event in temp:
#         date = utl.parse_datetime(event['DateTime']).date()
#         time = utl.parse_datetime(event['DateTime']).time()
#         if date == new_date:
#             dpg.add_text(f"{event['EventName']} | {time}",parent='Events')
#             count+=1
#             if event['EventName'] in plot_events.keys():
#                 plot_events[event['EventName']]  = plot_events[event['EventName']] + 1
#             else:
#                 plot_events[event['EventName']] = 1
#     if count==0: 
#         dpg.set_value('text','No marked events on this day!')
#         dpg.configure_item('Events',show=False)
#         dpg.configure_item('pie',show=False)
#     else:
#         dpg.set_value('text','Events:')
#         dpg.configure_item('Events',show=True)
#         values = [plot_events[key] for key in plot_events.keys()]
#         dpg.configure_item('pie',labels=list(plot_events.keys()),values=values,show=True)
#     dpg.configure_item('text',show=True)
    
        

# labels = ["Apples", "Bananas", "Cherries", "Dates"]
# values = [30, 15, 45, 10]

dpg.create_context()

# with dpg.window(tag="Date Picker Example",width=600):
#     with dpg.group(horizontal=True):
#         with dpg.group(width=250):
#             dpg.add_text("Select a date:")
#             dv = {
#                 'year':previous_session.year-1900,
#                 'month':previous_session.month-1,
#                 'month_day':previous_session.day
#             }
#             dpg.add_date_picker(tag="##datepicker", callback=show_selected_date, level=dpg.mvDatePickerLevel_Month,default_value=dv)
#             dpg.add_text("", tag="selected_date_text")
#             dpg.add_text('Events:',show=False,tag='text')
#             dpg.add_child_window(tag='Events',show=False)

#         with dpg.group(width=350):
#             with dpg.plot():
#                 dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
#                 x_axis = dpg.add_plot_axis(dpg.mvXAxis)
#                 y_axis = dpg.add_plot_axis(dpg.mvYAxis)
#                 dpg.add_pie_series(
#                     x=0.0,
#                     y=0.0,  # (x, y) center coordinates
#                     radius=1.0,         # relative radius of the pie
#                     values=values,       # numerical values
#                     labels=labels,       # corresponding labels
#                     normalize=True,      # ensures the values sum to 1
#                     parent=y_axis,
#                     label='Events',
#                     show=False,
#                     tag='pie'
#                 )


#do n# events throught the days until last session
dpg.show_implot_demo()
    # with dpg.plot(width=-1,height=-1):
    #     dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
    #     x_axis = dpg.add_plot_axis(dpg.mvXAxis,scale=dpg.mvPlotScale_Time)
    #     y_axis = dpg.add_plot_axis(dpg.mvYAxis)
    #     for name, events in event_summary.items():
    #         x = [(utl.parse_datetime(key)+daylight_savings).timestamp() for key in events.keys()]
    #         y = [events[key] for key in events.keys()]
    #         b = dpg.add_bar_series(x,y,label=name,parent=y_axis,weight=70)

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()


'''
def show_selected_date(sender, data):
    # Get the selected date from the date picker
    date = dpg.get_value("##datepicker")
    new_date = datetime(year=date['year']+1900,month=date['month']+1,day=date['month_day']).date() #C-style time struct
    old_date = dpg.get_value("selected_date_text")
    if new_date==old_date: return
    dpg.delete_item('Events',children_only=True)
    dpg.set_value("selected_date_text",new_date)
    count = 0
    plot_events = {}
    for event in events:
        date = utl.parse_datetime(event['DateTime']).date()
        time = utl.parse_datetime(event['DateTime']).time()
        if date == new_date:
            dpg.add_text(f"{event['EventName']} | {time}",parent='Events')
            count+=1
            if event['EventName'] in plot_events.keys():
                plot_events[event['EventName']]  = plot_events[event['EventName']] + 1
            else:
                plot_events[event['EventName']] = 1
    if count==0: 
        dpg.set_value('text','No marked events on this day!')
        dpg.configure_item('Events',show=False)
        dpg.configure_item('pie',show=False)
    else:
        dpg.set_value('text','Events:')
        dpg.configure_item('Events',show=True)
        values = [plot_events[key] for key in plot_events.keys()]
        dpg.configure_item('pie',labels=list(plot_events.keys()),values=values,show=True)
    dpg.configure_item('text',show=True)
    
        

labels = ["Apples", "Bananas", "Cherries", "Dates"]
values = [30, 15, 45, 10]

with dpg.window(tag="Date Picker Example",width=600):
    with dpg.group(horizontal=True):
        with dpg.group(width=250):
            dpg.add_text("Select a date:")
            dv = {
                'year':125,
                'month':1,
                'month_day':1
            }
            dpg.add_date_picker(tag="##datepicker", callback=show_selected_date, level=dpg.mvDatePickerLevel_Month,default_value=dv)
            dpg.add_text("", tag="selected_date_text")
            dpg.add_text('Events:',show=False,tag='text')
            dpg.add_child_window(tag='Events',show=False)

        with dpg.group(width=350):
            with dpg.plot():
                dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
                x_axis = dpg.add_plot_axis(dpg.mvXAxis)
                y_axis = dpg.add_plot_axis(dpg.mvYAxis)
                dpg.add_pie_series(
                    x=0.0,
                    y=0.0,  # (x, y) center coordinates
                    radius=1.0,         # relative radius of the pie
                    values=values,       # numerical values
                    labels=labels,       # corresponding labels
                    normalize=True,      # ensures the values sum to 1
                    parent=y_axis,
                    label='Events',
                    show=False,
                    tag='pie'
                )



Data = DH.getData(file)
Events = DH.getSignals(Data,'Events')
Z2L = DH.info_electrodes(Data)['PSD']['SignalPsdValues']
Z2R = DH.info_electrodes(Data,side=1)['PSD']['SignalPsdValues']
electrodes = {'Left': Z2L, 'Right': Z2R}

dpg.create_context()
with dpg.window():
    with dpg.plot(height=-1,width=-1,tag='plot'):
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
        colormap = 1
        dpg.bind_colormap('plot',colormap)
        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)")
        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="PSD Values")

        for event in Events:
            for side in ['Left','Right']:
                stream = event[side]
                label = f"{event['EventName']} | {utl.after_point(stream['Channel'])}_{side}"
                new_y = np.array(stream['Y']) / np.array(electrodes[side])
                dpg.add_line_series(stream['X'], new_y,label = label,parent=y_axis)

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()


'''