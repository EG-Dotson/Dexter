# ui.py
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import os

# define frame labels throughout proplet extrusion
frame_labels = [
    "Pre Droplet",
    "Before Extrusion",
    "Beginning Extrusion",
    "Max Diameter",
    "Post Extrusion"
]

def get_user_input():
    root = tk.Tk()
    root.withdraw()
# define and initialize dialog window 
    class UnifiedInputDialog(tk.Toplevel):
        def __init__(self, parent):
            super().__init__(parent)
            self.title("Input Parameters")
            self.geometry("300x250")
            self.resizable(False, False)
            self.result = None
            # diamter input
            tk.Label(self, text="Nozzle Diameter (µm):").pack(pady=5)
            self.nozzle_entry = tk.Entry(self)
            self.nozzle_entry.pack()
            # extrusion pressure input
            tk.Label(self, text="Extrusion Pressure (Pa):").pack(pady=5)
            self.pressure_entry = tk.Entry(self)
            self.pressure_entry.pack()
            # fps input
            tk.Label(self, text="Frames Per Second (fps):").pack(pady=5)
            self.fps_entry = tk.Entry(self)
            self.fps_entry.pack()
            # submit parameters button and begin processing
            submit_btn = tk.Button(self, text="Submit", command=self.submit)
            submit_btn.pack(pady=10)

            self.bind("<Return>", lambda event: self.submit())
            self.nozzle_entry.focus()

        def submit(self):
            try:
                nozzle = float(self.nozzle_entry.get())
                pressure = float(self.pressure_entry.get())
                fps = float(self.fps_entry.get())
                self.result = (nozzle, pressure, fps)
                self.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numeric values.")

    input_dialog = UnifiedInputDialog(root)
    root.wait_window(input_dialog)
    if input_dialog.result is None:
        exit()

    nozzle_diameter, pressure, frame_rate = input_dialog.result
# video input
    video_path = filedialog.askopenfilename(
        title="Select Video File",
        filetypes=[("Video Files", "*.mp4 *.mov")]
    )
    if not video_path or not os.path.exists(video_path):
        messagebox.showerror("File Error", "Please select a valid .mp4 or .mov video file.")
        exit()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        messagebox.showerror("Capture Error", "Could not open selected video.")
        exit()
    # total number of frames
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # microns per pixel scaling
    microns_per_pixel = nozzle_diameter / cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    # return all data and calculations
    return nozzle_diameter, pressure, frame_rate, cap, frame_count, microns_per_pixel
