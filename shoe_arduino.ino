#include <SoftwareSerial.h>

const int switchPin = 2; // Tilt switch connected to D2
SoftwareSerial BTSerial(10, 11); // RX, TX (Connect HC-06 TX to D10, RX to D11)

int lastSwitchState = -1; // Track previous state
unsigned long lastSendTime = 0; // Track when we last sent an update

void setup() {
  pinMode(switchPin, INPUT_PULLUP); // Use internal pull-up resistor
  BTSerial.begin(9600); // Bluetooth communication
  BTSerial.println("Bluetooth Tilt Sensor Ready...");
}

void loop() {
  int switchState = digitalRead(switchPin);
  unsigned long currentTime = millis();
  
  // Only send data when the state changes OR every 5 seconds as a heartbeat
  if (switchState != lastSwitchState || currentTime - lastSendTime >= 5000) {
    lastSwitchState = switchState;
    lastSendTime = currentTime;
    
    if (switchState == LOW) {
      BTSerial.println("Stable");
    } else {
      BTSerial.println("Tilted");
    }
  }
  
  delay(500); // Longer delay to reduce processing frequency
}