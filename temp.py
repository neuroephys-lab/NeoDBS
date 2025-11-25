# Updating ft.export_plot()

import DataHandling as DH
import dearpygui.dearpygui as dpg
import numpy as np
import matplotlib.pyplot as plt
'''
BASE

dpg.create_context()
with dpg.window():

dpg.create_viewport(title='Temporario', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

# # file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"
file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json"
# # file = "C:\\Users\\OCD\\Desktop\\DATA\\RN\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"

'''
file = "C:\\Users\\Patricia\\Desktop\\FEUP\\Tese\\Recordings\\2025-01-23\\Report_Json_Session_Report_20250212T122746.json"
summary = DH.getEventSummary(DH.getData(file))

def export_plot(info, plot_type, show=True):

    signals, labels, colors, title, axis, limits  = info

    ys = [signal['Y'] for signal in signals if 'Y' in signal.keys()]
    miny = min(np.min(y) for y in ys)
    maxy = max(np.max(y) for y in ys)

    if plot_type == '2D':
        fig, ax = plt.subplots()
        ax.set_title(title)
        ax.set_xlabel(axis[0])
        ax.set_ylabel(axis[1])
        ax.set_xlim(*limits[0])
        ax.set_ylim(*limits[1])

        for i, signal in enumerate(signals):
            label = labels[i]
            if 'Y1' in signal.keys():
                x, y1,y2 = signal['X'], signal['Y1'], signal['Y2']
                ax.fill_between(x,y1,y2,label=label,color=colors[i][:3],alpha=colors[i][-1])
            elif len(list(signal.keys()))==1: #infinte lines
                ax.vlines(signal['X'],miny,maxy,label=label,color=colors[i])
            else:
                x, y = signal['X'], signal['Y']
                ax.plot(x, y, label=label, color=colors[i])

        ax.legend()
        fig.tight_layout()

    elif plot_type == '3D':
        n_signals = len(signals)
        fig, axs = plt.subplots(
            n_signals, 1,
            figsize=(8, 3 * n_signals),
            constrained_layout=True,
            sharex=True
        )
        if n_signals == 1:
            axs = [axs]

        fig.suptitle(title)
        for i, signal in enumerate(signals):
            f, t, sxx = signal
            ax = axs[i]
            pcm = ax.pcolormesh(t, f, sxx, shading='gouraud', cmap='viridis')
            fig.colorbar(pcm, ax=ax, label=axis[2])
            ax.set_ylabel(axis[1])
            ax.set_title(labels[i])
        axs[-1].set_xlabel(axis[0])

    fig.savefig(f'{title}.png', bbox_inches='tight', dpi=300)

    plt.close(fig)

import datetime

# create data
customdate = datetime.datetime(2016, 1, 1, 13, 30)
y = [ 2,4,6,8,10,12,14,16,18,20 ]
x = [customdate + datetime.timedelta(hours=i) for i in range(len(y))]
print(x)
#datetime.datetime(2024, 11, 8, 23, 59, 44)
# plot
plt.plot(x,y)
plt.gcf().autofmt_xdate()
plt.show()

# dpg.create_context()
# # with dpg.window():

# dpg.create_viewport(title='Temporario', width=800, height=600)
# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()