import serial
import time
from flask import Flask, jsonify
import threading

app = Flask(__name__)

# Bluetooth settings
BLUETOOTH_PORT = "/dev/cu.HC-06"
BAUD_RATE = 9600
TIMEOUT = 5  # Longer timeout

# Global variables
last_tilt_status = "Unknown"
last_update_time = 0
connection_status = "Initializing"

def bluetooth_monitor():
    """Ultra-conservative Bluetooth monitoring approach"""
    global last_tilt_status, last_update_time, connection_status
    
    while True:
        try:
            # Open connection
            print(f"Attempting to connect to {BLUETOOTH_PORT}...")
            connection_status = "Connecting..."
            
            ser = serial.Serial(
                BLUETOOTH_PORT,
                BAUD_RATE,
                timeout=TIMEOUT,
                write_timeout=5,  # Add write timeout
                dsrdtr=False,     # Disable hardware flow control
                rtscts=False,     # Disable hardware flow control
                xonxoff=False     # Disable software flow control
            )
            
            print("✅ Connected to Bluetooth")
            connection_status = "Connected"
            
            # Allow connection to stabilize
            time.sleep(3)
            
            # Main reading loop - extremely conservative
            while True:
                try:
                    # Only read when there's data, no writing at all
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore').strip()
                        if data:
                            print(f"Received: {data}")
                            
                            # Process multiple lines if present
                            lines = data.split('\r\n')
                            if lines:
                                last_tilt_status = lines[-1]  # Take the most recent line
                                last_update_time = time.time()
                    
                    # Very long sleep to reduce connection stress
                    time.sleep(10)
                    
                except Exception as e:
                    print(f"Read error: {e}")
                    break
            
            # Clean up
            try:
                ser.close()
            except:
                pass
                
        except Exception as e:
            print(f"Connection error: {e}")
            connection_status = f"Error: {e}"
        
        # Very long delay before reconnecting
        connection_status = "Waiting to reconnect..."
        print("Waiting 30 seconds before reconnection attempt...")
        time.sleep(10)

@app.route("/", methods=["GET"])
def home():
    """Homepage Route"""
    return "Welcome to the Tilt Sensor API! Visit /tilt to check status."

@app.route("/tilt", methods=["GET"])
def get_tilt_status():
    """Read tilt status from Bluetooth and return JSON response."""
    current_time = time.time()
    time_since_update = current_time - last_update_time if last_update_time > 0 else 0
    
    return jsonify({
        "status": last_tilt_status,
        "connection_status": connection_status,
        "last_updated_seconds_ago": round(time_since_update, 1),
        "timestamp": current_time
    })

if __name__ == "__main__":
    # Start the Bluetooth monitor thread
    print("Starting Bluetooth monitor thread...")
    bt_thread = threading.Thread(target=bluetooth_monitor, daemon=True)
    bt_thread.start()
    
    # Start Flask server
    print("Starting Flask server...")
    app.run(debug=False, host="0.0.0.0", port=5000)  # Disable debug mode for stability