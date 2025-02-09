import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import plotly.subplots as sp
import serial
from datetime import datetime
import csv
import os
import re
from plotly.subplots import make_subplots
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

data_file = 'data.csv'

def read_data_from_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            return [(datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S'), float(row[1]), float(row[2])) for row in reader]
    return []

def write_data_to_file(file_path, data):
    with open(file_path, 'a') as file:
        writer = csv.writer(file)
        for row in data:
            writer.writerow(row)

def parse_message(message):
    """Extract battery and solar voltage from the incoming message."""
    battery_voltage = None
    solar_voltage = None
    
    matches = re.findall(r'([A-Za-z])(\d+)', message)
    for key, value in matches:
        if key == 'V':
            battery_voltage = int(value) / 1000.0  # Convert to volts
        elif key == 's':
            solar_voltage = int(value) / 1000.0  # Convert to volts
    
    return battery_voltage, solar_voltage

def read_serial_data(serial_port, baudrate=115600):
    """Read data from the serial port."""
    ser = serial.Serial(serial_port, baudrate, timeout=1)
    data = read_data_from_file(data_file)
    
    def update_data():
        nonlocal data
        if ser.in_waiting > 0:
            line = ser.readline()
            print(line)  # Print the raw line for debugging
            decoded_line = line.decode('utf-8', errors='ignore').strip()
            print(decoded_line)  # Print the raw line for debugging
            battery, solar = parse_message(decoded_line)
            print(f"Parsed: Battery={battery}, Solar={solar}")  # Print parsed values for debugging
            if battery is not None and solar is not None:
                timestamp = datetime.now()
                print(datetime.now())  # Print the timestamp for debugging
                data.append((timestamp, battery, solar))
                write_data_to_file(data_file, [(timestamp.strftime('%Y-%m-%d %H:%M:%S'), battery, solar)])
        
        # Limit data to the last 10000 points
        data = data[-10000:]
        
        return data

    return update_data

app = Dash(__name__)
update_data = read_serial_data('/dev/ttyUSB0')

app.layout = html.Div([
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # in milliseconds
        n_intervals=0
    )
])

@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    data = update_data()
    df = pd.DataFrame(data, columns=['Timestamp', 'Battery Voltage (V)', 'Solar Voltage (V)'])
    df.set_index('Timestamp', inplace=True)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(x=df.index, y=df['Battery Voltage (V)'], name='Battery Voltage'),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=df.index, y=df['Solar Voltage (V)'], name='Solar Voltage'),
        secondary_y=True,
    )
    
    fig.update_layout(title_text="Battery and Solar Voltage Over Time")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Battery Voltage (V)", secondary_y=False)
    fig.update_yaxes(title_text="Solar Voltage (V)", secondary_y=True)
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)