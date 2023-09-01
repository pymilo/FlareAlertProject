import os
import wget
import json
import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Range1d, LogAxis, FuncTickFormatter
from bokeh.plotting import figure

# Define primary and secondary URLs
PRIMARY_URL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json"
SECONDARY_URL = "https://services.swpc.noaa.gov/json/goes/secondary/xrays-6-hour.json"

def fetch_data(url):
    json_file = url.split('/')[-1]
    if os.path.exists(json_file):
        os.remove(json_file)
    wget.download(url, json_file, bar=None)

    with open(json_file) as f:
        df = pd.DataFrame(json.load(f))
        df.loc[:, 'time_tag'] = pd.to_datetime(df['time_tag'], format='ISO8601')

    return df

def get_data():
    df_primary = fetch_data(PRIMARY_URL)
    df_secondary = fetch_data(SECONDARY_URL)

    primary_05_04 = df_primary[df_primary.energy == '0.05-0.4nm']
    primary_10_08 = df_primary[df_primary.energy == '0.1-0.8nm']

    secondary_05_04 = df_secondary[df_secondary.energy == '0.05-0.4nm']
    secondary_10_08 = df_secondary[df_secondary.energy == '0.1-0.8nm']

    return primary_05_04, primary_10_08, secondary_05_04, secondary_10_08

# Initial data
primary_05_04, primary_10_08, secondary_05_04, secondary_10_08 = get_data()

sources = {
    "primary_05_04": ColumnDataSource(data=dict(time_tag=primary_05_04['time_tag'][-100:], flux=primary_05_04['flux'][-100:])),
    "primary_10_08": ColumnDataSource(data=dict(time_tag=primary_10_08['time_tag'][-100:], flux=primary_10_08['flux'][-100:])),
    "secondary_05_04": ColumnDataSource(data=dict(time_tag=secondary_05_04['time_tag'][-100:], flux=secondary_05_04['flux'][-100:])),
    "secondary_10_08": ColumnDataSource(data=dict(time_tag=secondary_10_08['time_tag'][-100:], flux=secondary_10_08['flux'][-100:]))
}

p = figure(x_axis_type="datetime", y_axis_type="log", title="Real-time Xrays Plot", width=800, height=400, y_range=(1e-8, 1e-4))

# Add the y-axis label
p.yaxis.axis_label = "Watts • m⁻²"

# Plot data with specified colors
p.line(x='time_tag', y='flux', source=sources["primary_05_04"], line_width=2, color='blue', legend_label="GOES-16 (0.05-0.4nm)")
p.line(x='time_tag', y='flux', source=sources["primary_10_08"], line_width=2, color='red', legend_label="GOES-16 (0.1-0.8nm)")
p.line(x='time_tag', y='flux', source=sources["secondary_05_04"], line_width=2, color='purple', legend_label="GOES-18 (0.05-0.4nm)")
p.line(x='time_tag', y='flux', source=sources["secondary_10_08"], line_width=2, color='orange', legend_label="GOES-18 (0.1-0.8nm)")
p.legend.location = "top_left"

def update_data():
    primary_05_04, primary_10_08, secondary_05_04, secondary_10_08 = get_data()

    sources["primary_05_04"].stream(dict(time_tag=primary_05_04['time_tag'], flux=primary_05_04['flux']), rollover=100)
    sources["primary_10_08"].stream(dict(time_tag=primary_10_08['time_tag'], flux=primary_10_08['flux']), rollover=100)
    sources["secondary_05_04"].stream(dict(time_tag=secondary_05_04['time_tag'], flux=secondary_05_04['flux']), rollover=100)
    sources["secondary_10_08"].stream(dict(time_tag=secondary_10_08['time_tag'], flux=secondary_10_08['flux']), rollover=100)
    
    # For simplicity, using the latest time from primary dataset
    latest_time = primary_05_04['time_tag'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')
    p.title.text = f"Real-time Xray plot (Last update: {latest_time})"

# Create the secondary Y-axis
extra_y_ranges = {}
extra_y_ranges["FlareClass"] = Range1d(start=1e-8, end=1e-4)

# Add the extra y-axis to the figure
p.add_layout(LogAxis(y_range_name="FlareClass", axis_label="Xray Flare Class"), 'right')

# Specify the tick labels and values for the flare classes
flare_class_ticks = {
    1e-7: "B",
    1e-6: "C",
    1e-5: "M",
}

# Apply the custom ticks to the secondary y-axis
p.extra_y_ranges = extra_y_ranges

code = """
    const labels = {1e-8: "A", 1e-7: "B", 1e-6: "C", 1e-5: "M", 1e-4: "X"};
    return labels[tick] || "";
"""

p.right[0].formatter = FuncTickFormatter(code=code)

# Update data every 5 seconds
curdoc().add_periodic_callback(update_data, 5000)

curdoc().add_root(p)
