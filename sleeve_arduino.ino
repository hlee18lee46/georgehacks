#include <SoftwareSerial.h>

const int buttonPin = 3;  // Push button connected to D3
const int buzzerPin = 9;  // Buzzer connected to D9
SoftwareSerial BTSerial(10, 11);  // RX, TX (HC-06 TX → D10, RX → D11)

bool buzzerState = false;
bool lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

void setup() {
    pinMode(buttonPin, INPUT_PULLUP);  // Internal pull-up resistor
    pinMode(buzzerPin, OUTPUT);
    Serial.begin(9600);  // Debugging via Serial Monitor
    BTSerial.begin(9600);  // Bluetooth communication
    BTSerial.println("Bluetooth Buzzer Ready...");
}

void loop() {
    bool buttonState = digitalRead(buttonPin);
    unsigned long currentTime = millis();

    // Debounce logic
    if (buttonState != lastButtonState) {
        lastDebounceTime = currentTime;
    }

    if ((currentTime - lastDebounceTime) > debounceDelay) {
        if (buttonState == LOW && !buzzerState) {  // Button Pressed
            tone(buzzerPin, 1000);  // 1000 Hz tone
            Serial.println("Buzzer ON");
            BTSerial.println("Buzzer ON");  // Send to Bluetooth
            buzzerState = true;
        } 
        else if (buttonState == HIGH && buzzerState) {  // Button Released
            noTone(buzzerPin);  // Stop buzzer
            Serial.println("Buzzer OFF");
            BTSerial.println("Buzzer OFF");  // Send to Bluetooth
            buzzerState = false;
        }
    }

    lastButtonState = buttonState;
}
