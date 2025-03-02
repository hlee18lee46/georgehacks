import serial
import time
from flask import Flask, jsonify
import threading
import smtplib
import sys
import os

app = Flask(__name__)

# Bluetooth settings
BLUETOOTH_PORT = "/dev/cu.HC-06"  # Change to COMx on Windows
BAUD_RATE = 9600
TIMEOUT = 5  # Bluetooth timeout

# Global variables
last_buzzer_status = "Unknown"
last_update_time = 0
connection_status = "Initializing"

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
    """Monitor Bluetooth for 'Buzzer ON' signal and send email alert."""
    global last_buzzer_status, last_update_time, connection_status

    while True:
        try:
            print(f"🔄 Connecting to {BLUETOOTH_PORT}...")
            connection_status = "Connecting..."
            
            ser = serial.Serial(
                BLUETOOTH_PORT,
                BAUD_RATE,
                timeout=TIMEOUT,
                write_timeout=5
            )

            print("✅ Connected to Bluetooth")
            connection_status = "Connected"
            time.sleep(3)  # Stabilize connection

            while True:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore').strip()
                    if data:
                        print(f"📩 Received: {data}")

                        if "ON" in data:
                            print("🚨 Buzzer ON detected! Sending alert...")
                            send_sms()
                            print("🛑 Exiting program due to 'Buzzer ON' signal.")
                            ser.close()
                            sys.exit(0)  # Exit after sending the email

                        # Store last status update
                        last_buzzer_status = data
                        last_update_time = time.time()

                time.sleep(1)  # Reduce CPU usage

        except Exception as e:
            print(f"❌ Bluetooth error: {e}")
            connection_status = f"Error: {e}"
        
        print("⏳ Retrying Bluetooth connection in 10 seconds...")
        time.sleep(10)

@app.route("/", methods=["GET"])
def home():
    """Homepage Route"""
    return "Welcome to the Buzzer API! Visit /buzzer to check status."

@app.route("/buzzer", methods=["GET"])
def get_buzzer_status():
    """Return buzzer status via API."""
    global last_buzzer_status, last_update_time

    current_time = time.time()
    time_since_update = current_time - last_update_time if last_update_time > 0 else 0

    if "ON" in last_buzzer_status:
        print("🚨 Buzzer ON detected! Sending alert...")
        send_sms()
        print("🛑 Exiting program due to 'Buzzer ON' signal.")
        #ser.close()
        #sys.exit(0)  # Exit after sending the email

    return jsonify({
        "status": last_buzzer_status,
        "connection_status": connection_status,
        "last_updated_seconds_ago": round(time_since_update, 1),
        "timestamp": current_time
    })

if __name__ == "__main__":
    print("Starting Bluetooth monitor thread...")
    bt_thread = threading.Thread(target=bluetooth_monitor, daemon=True)
    bt_thread.start()
    
    print("Starting Flask server...")
    app.run(debug=False, host="0.0.0.0", port=5000)
