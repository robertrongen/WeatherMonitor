/*
    SkyMonitor Nano
    Reads wind sensor and rain sensor
    Prints sensor data to serial port
*/
#include <Arduino.h>

// Rain sensor
#define sensorPinAnalog A0

// Wind Sensor
unsigned long lastDebounceTime = 0;  // The last time the output pin was toggled
unsigned long debounceDelay = 1000;  // The debounce time; increase if the output flickers

int pinInterrupt = 2;  // Blue - NPNR pulse output

volatile int Count = 0;  // Pulse count (volatile because it changes in an ISR)

void onChange() {
    if (digitalRead(pinInterrupt) == LOW) {
        Count++;
    }
}

void setup() {
    Serial.begin(115200);
    while (!Serial) {
        ;  // Wait for serial port to connect. Needed for native USB
    }
    Serial.println("Serial of Nano connected");

    // Wind sensor
    pinMode(pinInterrupt, INPUT_PULLUP);                                      // Set the interrupt pin
    attachInterrupt(digitalPinToInterrupt(pinInterrupt), onChange, FALLING);  // Enable interrupt on falling edge
}

unsigned long previousMillis = 0;
const long interval = 1000;  // Interval at which to read sensors

void loop() {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval) {
        previousMillis = currentMillis;

        if ((currentMillis - lastDebounceTime) > debounceDelay) {
            lastDebounceTime = currentMillis;
            float windSensorValue = (Count * 8.75) / 100.0;  // Corrected calculation
            Serial.print("WindSensor,");
            Serial.println(windSensorValue);

            Count = 0;

            int rainSensorValue = analogRead(sensorPinAnalog);
            Serial.print("RainSensor,");
            Serial.println(rainSensorValue);
        }
    }
}
