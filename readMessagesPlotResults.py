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
    ser = serial.Serial(serial_port, baudrate, timeout=1)
    data = read_data_from_file(data_file)
    print(f"Initial data loaded from {data_file}: {data}")
    
    def update(frame, data):
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
        
        for ax in axs.flat:
            ax.clear()

        axs[0, 0].plot(df.index, df['Ultrasonic Range'], label='Ultrasonic Range', color='tab:green')
        axs[0, 0].set_ylim(500, max(2000, df['Ultrasonic Range'].max()))
        axs[0, 0].set_xlabel("Time", fontsize=8)
        axs[0, 0].set_ylabel("Ultrasonic Range", fontsize=8)
        axs[0, 0].set_title("Ultrasonic Range Over Time", fontsize=10)
        axs[0, 0].legend(loc='upper left', fontsize=8)
        
        axs[0, 1].plot(df.index, df['RSSI'], label='RSSI', color='tab:green')
        axs[0, 1].set_ylim(-250, max(0, df['RSSI'].max()))
        axs[0, 1].set_xlabel("Time", fontsize=8)
        axs[0, 1].set_ylabel("RSSI", fontsize=8)
        axs[0, 1].set_title("RSSI Over Time", fontsize=10)
        axs[0, 1].legend(loc='upper left', fontsize=8)
        
        axs[1, 0].plot(df.index, df['Battery Voltage (V)'], label='Battery Voltage', color='tab:blue')
        axs[1, 0].set_ylim(1.0, max(4.0, df['Battery Voltage (V)'].max()))
        axs[1, 0].set_xlabel("Time", fontsize=8)
        axs[1, 0].set_ylabel("Battery Voltage (V)", fontsize=8)
        axs[1, 0].set_title("Battery Voltage Over Time", fontsize=10)
        axs[1, 0].legend(loc='upper left', fontsize=8)
        
        axs[1, 1].plot(df.index, df['Solar Voltage (V)'], label='Solar Voltage', color='tab:orange')
        axs[1, 1].set_ylim(0, 9)
        axs[1, 1].set_xlabel("Time", fontsize=8)
        axs[1, 1].set_ylabel("Solar Voltage (V)", fontsize=8)
        axs[1, 1].set_title("Solar Voltage Over Time", fontsize=10)
        axs[1, 1].legend(loc='upper left', fontsize=8)
        
        

    fig, axs = plt.subplots(2, 2, figsize=(18, 12))  # Create 4 subplots in a 2x2 grid with larger figure size
    fig.tight_layout(pad=3.0)  # Adjust layout to prevent overlap
    ani = animation.FuncAnimation(fig, update, fargs=(data,), interval=1000, cache_frame_data=False)
    plt.show()

    ser.close()

if __name__ == "__main__":
    read_serial_data('/dev/cu.usbserial-0001')

