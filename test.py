import serial
import time
import sys

# Change this to your actual Bluetooth port
BLUETOOTH_PORT = "/dev/cu.HC-06"  
BAUD_RATE = 9600

print(f"Trying to connect to {BLUETOOTH_PORT} at {BAUD_RATE} baud...")

try:
    # Attempt to open the port
    ser = serial.Serial(BLUETOOTH_PORT, BAUD_RATE, timeout=2)
    print("✅ Successfully connected!")
    
    # Wait a moment
    time.sleep(1)
    
    # Try a simple write operation
    print("Sending test message...")
    try:
        ser.write(b"TEST\n")
        print("✅ Write operation successful")
    except Exception as e:
        print(f"❌ Write failed: {e}")
    
    # Try a simple read operation
    print("Attempting to read data...")
    try:
        # Wait for potential data
        time.sleep(2)
        bytes_waiting = ser.in_waiting
        print(f"Bytes waiting to be read: {bytes_waiting}")
        
        if bytes_waiting > 0:
            data = ser.read(bytes_waiting)
            print(f"✅ Read successful: {data}")
        else:
            print("No data received")
    except Exception as e:
        print(f"❌ Read failed: {e}")
    
    # Try to close the connection
    try:
        ser.close()
        print("✅ Connection closed properly")
    except Exception as e:
        print(f"❌ Close failed: {e}")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")