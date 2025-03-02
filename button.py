import serial
import time
from flask import Flask, jsonify
import threading
import smtplib
import sys
import os
import openai
import pyttsx3
import speech_recognition as sr
import requests
import os
from dotenv import load_dotenv
import smtplib

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
    load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
PRIMARY_SMS_GATEWAY = os.getenv("PRIMARY_SMS_GATEWAY")
SECONDARY_SMS_GATEWAY = os.getenv("SECONDARY_SMS_GATEWAY")
THIRD_SMS_GATEWAY = os.getenv("THIRD_SMS_GATEWAY")


def coordinates():
    try:
        response = requests.get('https://ipinfo.io')
        data = response.json()
        location = data['loc'].split(',')
        lat, long = float(location[0]), float(location[1])
        city = data.get('city', 'Unknown')
        state = data.get('region', 'Unknown')
        return lat, long, city, state
    except:
        return False

try:
    lat, long, city, state = coordinates()
    print(f"The patient is in {city}, {state}")
    print(f"The latitude is {lat} and longitude is {long}")
except:
    print("No Location")

r = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("voice", "com.apple.voice.compact.en-GB.Daniel")

engine.say("Hello, I am Alex, a first responder assistant. Did you fall?")
engine.runAndWait()
engine.stop()

count = 0

def speech(count):
    with sr.Microphone() as source:
        print("Talk")
        audio_text = r.listen(source, timeout=30, phrase_time_limit=45)
        print("Time over, thanks")
    try:
        print("Text: "+r.recognize_google(audio_text))
        return r.recognize_google(audio_text)
    except sr.WaitTimeoutError:
        print("No Response")
        return "(Patient Cannot Speak)"
    except:
        print("Cannot understand")
        return "(Patient Cannot Speak)"

openai.api_key = OPENAI_API_KEY
messages = []
messages.append({"role": "system", "content": "You are my personal AI assistant, Alex. Your main role is to communicate with me, and ask if I took a fall and got injured. If I say that I did not fall, express your gratitude that I am safe and end prompting immediately without asking any questions. If I do not reply and you get no response, assume I am unconscious and alert emergency services about my fall and stop prompting immediately and ask no more questions. If you get a response saying that I did fall, proceed forward. To successfully alert, you need several things: my location, my pain on a scale from 1 to 10, location of the injury, if I can move or not. If I do respond with an affirmative, then ask me the questions one at a time, and also ask me individually if I want to contact emergency and if I want to alert my contact. Depending on these responses, determine a triage level of either red meaning immediate assistance needed, yellow meaning moderate injury, and green meaning lower level injury. Make sure you maintain a calm and soothing voice and make sure to reassure me that everything will be alright and that assistance will be arriving. Include key information such as location, triage level, pain information, etc. that you gathered from me. Based on my replies to your questions, draft a response message that contains all the information you have gathered and send it to both parties. Let me know what triage level you informed the emergencies I am at, the description of the location of the pain and the severity of it, and my ability to move. General Interaction Guidelines: Be courteous and patient for responses. You are working with old people, so it is very important to talk to them in a soothing and sentimental manner. Ensure clarity and maintain a professional demeanor throughout. Don't provide lengthy responses."})
message = ""
activate = False

while True:
    message = speech(count)
    print(message)
    messages.append({"role": "user", "content": message})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages)
    reply = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": reply})
    print("\n" + reply + "\n")
    engine.setProperty("rate", 175)
    engine.say(reply)
    engine.runAndWait()
    engine.stop()
    if message.lower() == "satisfied" or message == "(Patient Cannot Speak)":
        break
    if ("Help" in reply or "help" in reply) and activate == False:
        activate = True
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, PRIMARY_SMS_GATEWAY, "Hi Family! I am feeling very bad! Please help me! My coordinates are: (" + str(lat) + ", " + str(long) + ")")
        server.quit()

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, SECONDARY_SMS_GATEWAY, "Hi 911! I am feeling very bad! Please help me! My coordinates are: (" + str(lat) + ", " + str(long) + ")")
        server.quit()

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, THIRD_SMS_GATEWAY, "Hi Friend! I am feeling very bad! Please help me! My coordinates are: (" + str(lat) + ", " + str(long) + ")")
        server.quit()

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
