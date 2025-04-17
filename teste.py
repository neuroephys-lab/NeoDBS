
import dearpygui.dearpygui as dpg
                                                                                          
'''nSamples = 1000                                                                           
win_size = nSamples // 4                                                                  
# create a slepian sequence of 6 orthogonal tapers                                        
slepians = windows.dpss(win_size, NW=2, Kmax=6)                                           
signal = randn(nSamples)                                                                  
                                                                                          
nSamples = 1000
t = np.linspace(0, 1000, nSamples, endpoint=False)
sig = ss.square(2 * np.pi * 5 * t)

'''

dpg.create_context()

dpg.show_implot_demo()
dpg.show_imgui_demo()

dpg.create_viewport(title="NeoDBS", width=1000, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

