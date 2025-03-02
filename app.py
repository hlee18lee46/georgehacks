import serial
import time
from flask import Flask, jsonify
import threading
import smtplib
import sys
import os


app = Flask(__name__)

# Bluetooth settings
BLUETOOTH_PORT = "/dev/cu.HC-06"
BAUD_RATE = 9600
TIMEOUT = 5  # Longer timeout

# Global variables
last_tilt_status = "Unknown"
last_update_time = 0
connection_status = "Initializing"

tilt_counter = 0  # Counter to track "Tilted" occurrences

def send_sms():
    """Send SMS alerts to multiple contacts."""
    #EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    #EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    # Debug: Check if variables are loaded correctly
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("⚠️ ERROR: EMAIL_ADDRESS or EMAIL_PASSWORD is not set!")
        exit(1)  # Stop the program if credentials are missing
    else:
        print("✅ Email credentials loaded successfully.")
    contacts = {
        "Venkat": "8133694575@tmomail.net",
        "911": "7248311777@vtext.com",
        "Emergency Contact": "4125032988@vtext.com"
    }

    messages = {
        "Venkat": "Hey Venkat, I fell down and can't move. Please come and help me.",
        "911": "911, Please Help, I just fell down!.",
        "Emergency Contact": "Hi. I am in Danger! Please save me."
    }

    try:
        for name, gateway in contacts.items():
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, gateway, messages[name])
            server.quit()
            print(f"✅ SMS alert sent to {name}")

    except Exception as e:
        print(f"⚠️ Failed to send SMS: {e}")

def bluetooth_monitor():
    """Ultra-conservative Bluetooth monitoring approach"""
    global last_tilt_status, last_update_time, connection_status, tilt_counter

    while True:
        try:
            # Open connection
            print(f"🔄 Attempting to connect to {BLUETOOTH_PORT}...")
            connection_status = "Connecting..."
            
            ser = serial.Serial(
                BLUETOOTH_PORT,
                BAUD_RATE,
                timeout=TIMEOUT,
                write_timeout=5,
                dsrdtr=False,
                rtscts=False,
                xonxoff=False
            )

            print("✅ Connected to Bluetooth")
            connection_status = "Connected"

            # Allow connection to stabilize
            time.sleep(3)

            while True:
                try:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore').strip()
                        if data:
                            print(f"📩 Received: {data}")  # Log received data

                            # Check if "Tilted" appears in the message
                            if "Tilted" in data:
                                tilt_counter += 1
                                print(f"⚠️ 'Tilted' detected ({tilt_counter}/2)")

                                # If "Tilted" is detected twice, trigger the alert
                                if tilt_counter >= 2:
                                    print("🚨 Detected 'Tilted' twice! Sending SMS alerts...")
                                    send_sms()
                                    print("🛑 Exiting program due to 'Tilted' status.")
                                    ser.close()
                                    sys.exit(0)  # Exit the program
                            elif "Stable" in data:
                                tilt_counter = 0
                            # Process multiple lines if present
                            lines = data.split('\r\n')
                            if lines:
                                last_tilt_status = lines[-1]  # Take the most recent line
                                last_update_time = time.time()
                    
                    time.sleep(5)  # Moderate sleep time
                
                except Exception as e:
                    print(f"⚠️ Read error: {e}")
                    break

            ser.close()

        except Exception as e:
            print(f"❌ Connection error: {e}")
            connection_status = f"Error: {e}"
        
        print("⏳ Waiting 10 seconds before reconnection attempt...")
        time.sleep(10)

@app.route("/", methods=["GET"])
def home():
    """Homepage Route"""
    return "Welcome to the Tilt Sensor API! Visit /tilt to check status."


@app.route("/tilt", methods=["GET"])
def get_tilt_status():
    """Read tilt status from Bluetooth and return JSON response."""
    global last_tilt_status, last_update_time

    current_time = time.time()
    time_since_update = current_time - last_update_time if last_update_time > 0 else 0

    # Check for tilt status and send SMS
    if last_tilt_status == "Tilted":
        
        email = "skagen146@gmail.com"
        password = "mxjujtpobaeuwgcq"
        sms_gateway = "8133694575@tmomail.net"  # Replace with recipient carrier's gateway

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, sms_gateway, "Hi. I am in Danger! Please save me.")
        server.quit()

        sms_gateway = "7248311777@vtext.com"  # Replace with recipient carrier's gateway
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, sms_gateway, "Hi. I am in Danger! Please save me.")
        server.quit()

        sms_gateway = "4125032988@vtext.com"  # Replace with recipient carrier's gateway
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, sms_gateway, "Hi. I am in Danger! Please save me.")
        server.quit()

        print("Exiting program due to Tilted status.")
        sys.exit(0)  # Exit the program
    elif "Stable" in data:
        tilt_counter = 0
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
