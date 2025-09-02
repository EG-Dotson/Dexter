import cv2
import numpy as np
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from rich.console import Console
from rich.table import Table

# style settings
plt.style.use('seaborn-v0_8-whitegrid')  #seaborn whitegrid
plt.rcParams.update({  
    "font.family": "sans-serif",  # sans-serif fonts
    "font.sans-serif": ["Helvetica", "Arial"], 
    "font.size": 13,  
    "axes.titlesize": 20, 
    "axes.labelsize": 18,  
    "axes.edgecolor": "#DDDDDD",  # Light grey 
    "axes.linewidth": 5,  
    "xtick.color": "#333333",  
    "ytick.color": "#333333", 
    "grid.color": "#CCCCCC", 
    "grid.alpha": 0.3, 
    "grid.linestyle": "--",  
    "figure.facecolor": "white", 
    "savefig.facecolor": "white",  
    "axes.facecolor": "#FAFAFA",
    "legend.frameon": True,
    "legend.framealpha": 0.8, 
    "legend.facecolor": "white", 
    "legend.edgecolor": "#DDDDDD",
})

fsu_garnet = "#782F40"
fsu_gold = "#CEB888"

# Dashboard output
def display_plotly_dashboard(selected_frames, frame_labels, frame_indices, diameters, microns_per_pixel, frame_rate):
    rows = 2
    cols = 3
    time_axis = np.arange(len(diameters)) / frame_rate
    selected_labels = [label for label in frame_labels if label in selected_frames]
    titles = [label for label in selected_labels]
    titles.append("Droplet Diameter Over Time")

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=tuple(titles),
        vertical_spacing=0.15,
        horizontal_spacing=0.08
    )

    for i, label in enumerate(selected_labels):
        img = cv2.cvtColor(selected_frames[label], cv2.COLOR_BGR2RGB)
        row = i // cols + 1
        col = i % cols + 1
        fig.add_trace(go.Image(z=img), row=row, col=col)

        fig.add_annotation(
            text=f"<b>{label}</b><br>Frame {frame_indices[label]}",
            xref="x domain", yref="y domain",
            x=0.5, y=1.15,
            showarrow=False,
            row=row, col=col,
            font=dict(color=fsu_gold, size=14),
            align="center"
        )

        fig.update_xaxes(title_text="X Pixels", row=row, col=col, showgrid=False, tickfont=dict(size=10))
        fig.update_yaxes(title_text="Y Pixels", row=row, col=col, showgrid=False, tickfont=dict(size=10))

    #Diameter over time graph
    total_plots = len(selected_labels) + 1
    row = (total_plots - 1) // cols + 1
    col = (total_plots - 1) % cols + 1

    fig.add_trace(
        go.Scatter(
            x=time_axis,
            y=diameters,
            mode='lines+markers',
            line=dict(color=fsu_garnet, width=3),
            marker=dict(size=5),
            name="Droplet Diameter"
        ),
        row=row,
        col=col
    )

    fig.update_xaxes(title_text="Time (s)", row=row, col=col, tickfont=dict(size=12), title_font=dict(size=14))
    fig.update_yaxes(title_text="Diameter (µm, log scale)", type="log", row=row, col=col, tickfont=dict(size=12), title_font=dict(size=14))

    fig.update_layout(
        title=dict(
            text="Droplet Extrusion Analysis Dashboard",
            font=dict(size=22, color="white"),
            x=0.5,
            xanchor="center"
        ),
        height=950,
        width=1400,
        showlegend=False,
        template="plotly_dark",
        plot_bgcolor="#000000",
        paper_bgcolor="#000000",
        font=dict(family="Helvetica", size=13, color="white"),
        margin=dict(t=80, b=80, l=60, r=60)
    )

    fig.show()

# final summary
def show_summary(nozzle_diameter, pressure, frame_rate, viscosity, max_diameter, max_frame_idx):
    console = Console()
    table = Table(title="Final Summary", style="bold blue")

    table.add_column("Parameter", justify="right", style="cyan")
    table.add_column("Value", justify="left", style="white")

    table.add_row("Nozzle Diameter (μm)", f"{nozzle_diameter:.2f}")
    table.add_row("Extrusion Pressure (Pa)", f"{pressure:.2f}")
    table.add_row("Frames Per Second", f"{frame_rate:.2f}")
    table.add_row("Calculated Viscosity (Pa·s)", f"{viscosity:.4e}")
    table.add_row("Max Droplet Diameter (μm)", f"{max_diameter:.2f}")
    table.add_row("Max Diameter Frame", f"{max_frame_idx}")

    console.print(table)
