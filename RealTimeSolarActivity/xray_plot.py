import pandas as pd
import json
import wget
from bokeh.plotting import figure, show
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import layout
from tornado.ioloop import IOLoop
from functools import partial
from datetime import datetime

# Create a blank ColumnDataSource
source = ColumnDataSource(data=dict(time=[], flux=[]))

# Initialize plot
p = figure(width=800, height=400, x_axis_type="datetime", 
           title="Real-time Xray plot", x_axis_label='Time', y_axis_label='Flux')
p.line(x='time', y='flux', source=source, legend_label='0.05-0.4nm', line_width=2)

def update_plot():
    json_url = "https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json"
    wget.download(json_url, "xrays-6-hour.json", bar=None)
    
    with open('xrays-6-hour.json') as f:
        df = pd.DataFrame(json.load(f))

    xrsa_current = df[df.energy == '0.05-0.4nm']
    xrsa_current.loc[:, 'time_tag'] = pd.to_datetime(xrsa_current['time_tag'])

    new_data = {
        'time': xrsa_current['time_tag'].tolist(),
        'flux': xrsa_current['flux'].tolist()
    }

    source.stream(new_data, rollover=100)  # Keep last 100 data points

# Update the plot every minute
curdoc().add_periodic_callback(update_plot, 60 * 1000)
curdoc().add_root(p)
