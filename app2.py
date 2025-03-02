import serial
import time
from flask import Flask, jsonify
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Bluetooth settings
BLUETOOTH_PORT = "/dev/cu.HC-06"
BAUD_RATE = 9600
TIMEOUT = 5

# Global variables
last_tilt_status = "Unknown"
last_update_time = 0
connection_history = []  # Track connection status history

def attempt_read_bluetooth():
    """Try to get a single reading from Bluetooth and immediately disconnect"""
    global last_tilt_status, last_update_time
    
    ser = None
    success = False
    message = ""
    
    try:
        # Open connection with a fresh instance every time
        ser = serial.Serial(BLUETOOTH_PORT, BAUD_RATE, timeout=TIMEOUT)
        logger.info("Connected to Bluetooth")
        
        # Allow connection to stabilize
        time.sleep(1)
        
        # Read any available data and immediately close
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore').strip()
            if data:
                logger.info(f"Received: {data}")
                lines = data.split('\r\n')
                if lines:
                    last_tilt_status = lines[-1]  # Take most recent reading
                    last_update_time = time.time()
                    success = True
                    message = "Data received"
        else:
            message = "No data available"
            
    except Exception as e:
        logger.error(f"Bluetooth error: {e}")
        message = f"Error: {e}"
    finally:
        # Always close the connection
        if ser:
            try:
                ser.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
    
    # Record this attempt in history
    connection_history.append({
        "timestamp": time.time(),
        "success": success,
        "message": message
    })
    
    # Keep history to last 20 attempts
    if len(connection_history) > 20:
        connection_history.pop(0)
        
    return success

def bluetooth_poller():
    """Periodically poll for new data with connection isolation"""
    while True:
        try:
            logger.info("Attempting to read Bluetooth data...")
            attempt_read_bluetooth()
        except Exception as e:
            logger.error(f"Unexpected error in polling thread: {e}")
        
        # Wait before next attempt - long delay to reduce connection stress
        logger.info("Waiting 15 seconds until next read attempt...")
        time.sleep(15)

@app.route("/", methods=["GET"])
def home():
    """Homepage Route"""
    return "Welcome to the Tilt Sensor API! Visit /tilt to check status."

@app.route("/tilt", methods=["GET"])
def get_tilt_status():
    """Get tilt status and connection info"""
    current_time = time.time()
    time_since_update = current_time - last_update_time if last_update_time > 0 else 0
    
    # Calculate success rate
    if connection_history:
        success_rate = sum(1 for entry in connection_history if entry["success"]) / len(connection_history) * 100
    else:
        success_rate = 0
    
    return jsonify({
        "status": last_tilt_status,
        "last_updated_seconds_ago": round(time_since_update, 1),
        "connection_success_rate": round(success_rate, 1),
        "recent_attempts": len(connection_history),
        "timestamp": current_time
    })

@app.route("/history", methods=["GET"])
def connection_history_endpoint():
    """View connection history"""
    return jsonify(connection_history)

@app.route("/force-read", methods=["GET"])
def force_read():
    """Force an immediate read attempt"""
    success = attempt_read_bluetooth()
    return jsonify({
        "success": success, 
        "status": last_tilt_status,
        "timestamp": time.time()
    })

if __name__ == "__main__":
    # Start the Bluetooth poller thread
    logger.info("Starting Bluetooth poller thread...")
    bt_thread = threading.Thread(target=bluetooth_poller, daemon=True)
    bt_thread.start()
    
    # Start Flask server
    logger.info("Starting Flask server...")
    app.run(debug=False, host="0.0.0.0", port=5000)