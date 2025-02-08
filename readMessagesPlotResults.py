import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import re

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
    data = []
    
    def update(frame):
        nonlocal data
        if ser.in_waiting > 0:
            line = ser.readline()
            print(line)  # Print the raw line for debugging
            decoded_line = line.decode('utf-8', errors='ignore').strip()
            print(decoded_line)  # Print the raw line for debugging
            battery, solar = parse_message(decoded_line)
            print(f"Parsed: Battery={battery}, Solar={solar}")  # Print parsed values for debugging
            if battery is not None and solar is not None:
                data.append((battery, solar))
            
        # Limit data to the last 100 points
        data = data[-1000:]
        
        # Convert to DataFrame for easy plotting
        df = pd.DataFrame(data, columns=['Battery Voltage (V)', 'Solar Voltage (V)'])
        
        ax.clear()
        ax.plot(df.index, df['Battery Voltage (V)'], label='Battery Voltage')
        ax.plot(df.index, df['Solar Voltage (V)'], label='Solar Voltage')
        ax.set_ylim(0, max(7, df.max().max()))
        ax.set_xlabel("Time")
        ax.set_ylabel("Voltage (V)")
        ax.set_title("Battery and Solar Voltage Over Time")
        ax.legend()
    
    fig, ax = plt.subplots()
    ani = animation.FuncAnimation(fig, update, interval=1000, cache_frame_data=False)
    plt.show()
    
    ser.close()

if __name__ == "__main__":
    serial_port = "/dev/cu.usbserial-0001"  # Change this to match your system (e.g., "/dev/ttyUSB0" on Linux/Mac)
    read_serial_data(serial_port)