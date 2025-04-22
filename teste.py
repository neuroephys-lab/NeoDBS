import dearpygui.dearpygui as dpg
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os

# Simulate wavelet data
wavelet_data = np.random.rand(256, 1024)

# Function to convert to image (for DPG display)
def wavelet_to_image(data, cmap="jet"):
    norm_data = (data - np.min(data)) / (np.max(data) - np.min(data))
    colormapped = plt.cm.get_cmap(cmap)(norm_data)
    img = (colormapped[:, :, :3] * 255).astype(np.uint8)
    return img

# Image for display
img_array = wavelet_to_image(wavelet_data)
image = Image.fromarray(img_array).convert("RGBA")
width, height = image.size
image_data = np.array(image).flatten() / 255.0

# Save function using matplotlib
def save_wavelet_plot():
    fig, ax = plt.subplots(figsize=(10, 5))
    cax = ax.imshow(wavelet_data, aspect='auto', cmap='jet', origin='lower')
    ax.set_title("Wavelet Transform")
    ax.set_xlabel("Time")
    ax.set_ylabel("Frequency")
    fig.colorbar(cax, ax=ax, label="Amplitude")
    save_path = os.path.join(os.getcwd(), "wavelet_full_plot.png")
    plt.savefig(save_path, dpi=600, bbox_inches='tight')
    plt.close()
    print(f"Wavelet plot saved to: {save_path}")

# DPG UI
dpg.create_context()

with dpg.texture_registry():
    dpg.add_static_texture(width, height, image_data, tag="wavelet_texture")

with dpg.window(label="Wavelet Viewer"):
    with dpg.plot(label="Wavelet Transform", width=800, height=400):
        dpg.add_plot_axis(dpg.mvXAxis, label="Time")
        with dpg.plot_axis(dpg.mvYAxis, label="Frequency"):
            dpg.add_image_series("wavelet_texture", [0, 0], [width, height])
    dpg.add_button(label="Save Plot with Axes", callback=lambda: save_wavelet_plot())

dpg.create_viewport(title="Wavelet Transform Viewer", width=900, height=500)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
