import os
import wget
import json
import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import Button, LinearAxis, LogAxis, ColumnDataSource
from bokeh.plotting import figure

def get_data():
    json_file = "xrays-6-hour.json"
    json_url = "https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json"
    if os.path.exists(json_file):
        os.remove(json_file)
    wget.download(json_url, json_file, bar=None)
    
    with open(json_file) as f:
        df = pd.DataFrame(json.load(f))

    df_05_04 = df[df.energy == '0.05-0.4nm']
    df_10_08 = df[df.energy == '0.1-0.8nm']

    return df_05_04, df_10_08

# Initial data
xrsa_05_04, xrsa_10_08 = get_data()
xrsa_05_04.loc[:, 'time_tag'] = pd.to_datetime(xrsa_05_04['time_tag'])
xrsa_10_08.loc[:, 'time_tag'] = pd.to_datetime(xrsa_10_08['time_tag'])

source_05_04 = ColumnDataSource(data=dict(time_tag=xrsa_05_04['time_tag'][-100:], flux=xrsa_05_04['flux'][-100:]))
source_10_08 = ColumnDataSource(data=dict(time_tag=xrsa_10_08['time_tag'][-100:], flux=xrsa_10_08['flux'][-100:]))

p = figure(x_axis_type="datetime", title="Real-time Xrays Plot", width=800, height=400)
p.line(x='time_tag', y='flux', source=source_05_04, line_width=2, color='blue', legend_label="0.05-0.4nm")
p.line(x='time_tag', y='flux', source=source_10_08, line_width=2, color='red', legend_label="0.1-0.8nm")
p.legend.location = "top_left"

def update_data():
    new_data_05_04, new_data_10_08 = get_data()
    new_data_05_04.loc[:, 'time_tag'] = pd.to_datetime(new_data_05_04['time_tag'])
    new_data_10_08.loc[:, 'time_tag'] = pd.to_datetime(new_data_10_08['time_tag'])

    source_05_04.stream(dict(time_tag=new_data_05_04['time_tag'], flux=new_data_05_04['flux']), rollover=100)
    source_10_08.stream(dict(time_tag=new_data_10_08['time_tag'], flux=new_data_10_08['flux']), rollover=100)
    
    latest_time = max(new_data_05_04['time_tag'].iloc[-1], new_data_10_08['time_tag'].iloc[-1]).strftime('%Y-%m-%d %H:%M:%S')
    p.title.text = f"Real-time Xray plot (Last update: {latest_time})"
    
    adjust_yaxis()

def adjust_yaxis():
    data_05_04 = source_05_04.data['flux']
    data_10_08 = source_10_08.data['flux']
    combined_data = data_05_04 + data_10_08

    min_val, max_val = min(combined_data), max(combined_data)
    
    if is_log:
        p.y_range.start = min_val if min_val > 0 else 0.001
        p.y_range.end = max_val
    else:
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
