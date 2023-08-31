import os
import wget
import json
import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import Button, LinearAxis, LogAxis, FixedTicker, ColumnDataSource
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
        df.loc[:, 'time_tag'] = pd.to_datetime(df['time_tag'])

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

p = figure(x_axis_type="datetime", title="Real-time Xrays Plot", width=800, height=400)

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
    
    if is_log:
        p.y_range.start = 1e-9
        p.y_range.end = 1e-3
    #adjust_yaxis()

def adjust_yaxis():
    if is_log:
        p.y_range.start = 1e-9
        p.y_range.end = 1e-3
        p.yaxis[0].ticker = FixedTicker(ticks=[1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3])
    else:
        all_data = []
        for key, source in sources.items():
            all_data.extend(source.data['flux'])
        max_val = max(all_data)
        p.y_range.start = 0
        p.y_range.end = max_val


# Update data every 5 seconds
curdoc().add_periodic_callback(update_data, 5000)

is_log = False

def toggle_yaxis():
    global is_log
    if is_log:
        p.yaxis[0].axis_label = "Flux"
        p.yaxis[0].ticker.base = 10
        p.yaxis[0].ticker = LinearAxis().ticker
    else:
        p.yaxis[0].axis_label = "Log(Flux)"
        p.yaxis[0].ticker.base = 10
        p.yaxis[0].ticker = LogAxis().ticker
    is_log = not is_log

    adjust_yaxis()  # Adjust y-axis after toggling

button = Button(label="Toggle Y-Axis (Linear/Log)", button_type="default")
button.on_click(toggle_yaxis)

curdoc().add_root(column(button, p))
