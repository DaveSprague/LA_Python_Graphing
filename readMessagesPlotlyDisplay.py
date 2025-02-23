import pandas as pd
import plotly.graph_objs as go
import plotly.subplots as sp
import serial
from datetime import datetime
import csv
import os
import re
import time

data_file = 'data.csv'

def read_data_from_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            return [(datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S'), float(row[1]), float(row[2]), float(row[3]), float(row[4])) for row in reader]
    return []

def write_data_to_file(file_path, data):
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Timestamp', 'Battery Voltage (V)', 'Solar Voltage (V)', 'Ultrasonic Range', 'RSSI'])
        for row in data:
            writer.writerow(row)
    print(f"Data written to {file_path}")

def parse_message(message):
    """Extract field values from the incoming message."""
    field_map = {
        'V': 'battery_voltage',
        's': 'solar_voltage',
        'S': 'sensor_id',
        'C': 'msg_count',
        'U': 'ultrasonic_range',
        'r': 'rssi',
        'n': 'signal_to_noise_ratio'
    }
    
    data = {}
    
    matches = re.findall(r'([A-Za-z])(-?\d+)', message)
    # example: S1,V4106,C55,U841,s6835,r-58,n12
    for key, value in matches:
        if key in field_map:
            if key == 'V' or key == 's':
                data[field_map[key]] = int(value) / 1000.0  # Convert to volts
            else:
                data[field_map[key]] = int(value)
    
    return data

def read_serial_data(serial_port, baudrate=115200):
    """Read data from the serial port."""
    try:
        ser = serial.Serial(serial_port, baudrate, timeout=1)
    except serial.SerialException as e:
        print(f"Error opening serial port {serial_port}: {e}")
        return

    data = read_data_from_file(data_file)
    print(f"Initial data loaded from {data_file}: {data}")
    
    # Create the initial figure
    fig = sp.make_subplots(rows=2, cols=2, subplot_titles=("Ultrasonic Range Over Time", "RSSI Over Time", "Battery Voltage Over Time", "Solar Voltage Over Time"))
    
    ultrasonic_trace = go.Scatter(x=[], y=[], mode='lines', name='Ultrasonic Range', line=dict(color='green'))
    rssi_trace = go.Scatter(x=[], y=[], mode='lines', name='RSSI', line=dict(color='red'))
    battery_trace = go.Scatter(x=[], y=[], mode='lines', name='Battery Voltage', line=dict(color='blue'))
    solar_trace = go.Scatter(x=[], y=[], mode='lines', name='Solar Voltage', line=dict(color='orange'))
    
    fig.add_trace(ultrasonic_trace, row=1, col=1)
    fig.add_trace(rssi_trace, row=1, col=2)
    fig.add_trace(battery_trace, row=2, col=1)
    fig.add_trace(solar_trace, row=2, col=2)
    
    fig.update_yaxes(title_text="Ultrasonic Range", row=1, col=1)
    fig.update_yaxes(title_text="RSSI", row=1, col=2)
    fig.update_yaxes(title_text="Battery Voltage (V)", row=2, col=1)
    fig.update_yaxes(title_text="Solar Voltage (V)", row=2, col=2)
    
    fig.update_layout(height=800, width=1200, title_text="Sensor Data Over Time", showlegend=True)
    
    def update(data):
        if ser.in_waiting > 0:
            line = ser.readline()
            # example: S1,V4106,C55,U841,s6835,r-58,n12
            print(line)  # Print the raw line for debugging
            decoded_line = line.decode('utf-8', errors='ignore').strip()
            # print(decoded_line)  # Print the raw line for debugging
            if len(decoded_line) < 10 or decoded_line[0] != 'S' or len(decoded_line) > 40:
                return
            parsed_data = parse_message(decoded_line)
            battery = parsed_data.get('battery_voltage')
            solar = parsed_data.get('solar_voltage')
            ultrasonic = parsed_data.get('ultrasonic_range')
            rssi = parsed_data.get('rssi')
            print(f"{datetime.now()}  Battery={battery}, Solar={solar}, Ultrasonic={ultrasonic}, RSSI={rssi}")  # Print parsed values for debugging
            if battery is not None and solar is not None and ultrasonic is not None and rssi is not None:
                timestamp = datetime.now()
                data.append((timestamp, battery, solar, ultrasonic, rssi))
                write_data_to_file(data_file, [(timestamp.strftime('%Y-%m-%d %H:%M:%S'), battery, solar, ultrasonic, rssi)])
        
        # Limit data to the last 10000 points
        data = data[-10000:]
        
        # Only create plots if there is data
        if not data:
            return
        
        # Convert to DataFrame for easy plotting
        df = pd.DataFrame(data, columns=['Timestamp', 'Battery Voltage (V)', 'Solar Voltage (V)', 'Ultrasonic Range', 'RSSI'])
        df.set_index('Timestamp', inplace=True)
        
        fig.data[0].x = df.index
        fig.data[0].y = df['Ultrasonic Range']
        
        fig.data[1].x = df.index
        fig.data[1].y = df['RSSI']
        
        fig.data[2].x = df.index
        fig.data[2].y = df['Battery Voltage (V)']
        
        fig.data[3].x = df.index
        fig.data[3].y = df['Solar Voltage (V)']

        fig.show()

    try:
        while True:
            update(data)
            time.sleep(1)  # Add a delay to avoid high CPU usage
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        ser.close()

# Example usage
if __name__ == "__main__":
    read_serial_data('/dev/cu.usbserial-0001')  # Replace with your actual serial port