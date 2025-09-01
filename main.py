import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib_scalebar.scalebar import ScaleBar
import math
from rich.console import Console
from rich.table import Table
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tkinter as tk
from tkinter import filedialog, messagebox
import plotly.io as pio
import uuid
import webbrowser

from frameprocessing import process_video
from frameprocessing import calculate_viscosity
from display import display_plotly_dashboard, show_summary
from ui import get_user_input

from ui import frame_labels


def main():
    # User input defining nozzle diameter, pressure, frame rate, and video file
    nozzle_diameter, pressure, frame_rate, cap, frame_count, microns_per_pixel = get_user_input()

    # Calculate viscosity
    R = (nozzle_diameter / 2) * 1e-6
    viscosity = calculate_viscosity(R, pressure)

    # Process the video frames, detect diameters, key frames
    selected_frames, frame_indices, diameters, max_diameter, max_frame_idx = process_video(
        cap, nozzle_diameter, frame_count, microns_per_pixel
    )

    # Show interactive plotly dashboard with frames and diameter graph
    display_plotly_dashboard(
        selected_frames, frame_labels, frame_indices,
        diameters, microns_per_pixel, frame_rate
    )

    # Print final summary table to terminal
    show_summary(
        nozzle_diameter, pressure, frame_rate,
        viscosity, max_diameter, max_frame_idx
    )

if __name__ == "__main__":
    main()
