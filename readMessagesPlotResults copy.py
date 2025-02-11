import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
from datetime import datetime
import csv
import os
import re

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
    
    def update(frame, data):
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
        
        # Limit data to the last 1000 points
        data = data[-10000:]
        
        # Convert to DataFrame for easy plotting
        df = pd.DataFrame(data, columns=['Timestamp', 'Battery Voltage (V)', 'Solar Voltage (V)'])
        df.set_index('Timestamp', inplace=True)
        
        ax.clear()
        ax.plot(df.index, df['Battery Voltage (V)'], label='Battery Voltage')
        ax.plot(df.index, df['Solar Voltage (V)'], label='Solar Voltage')
        ax.set_ylim(0, max(7, df.max().max()))
        ax.set_xlabel("Time")
        ax.set_ylabel("Voltage (V)")
        ax.set_title("Battery and Solar Voltage Over Time")
        ax.legend()

    fig, ax = plt.subplots()
    ani = animation.FuncAnimation(fig, update, fargs=(data,), interval=1000, cache_frame_data=False)
    plt.show()

    ser.close()

if __name__ == "__main__":
    read_serial_data('/dev/cu.usbserial-0001')