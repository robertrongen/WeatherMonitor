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
unsigned long debounceDelay = 100;  // The debounce time; increase if the output flickers

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

unsigned long startTime = 0;
const long measurementPeriod = 5000;  // 5-second period for wind sensor

int rainReadings[5];  // Array to hold rain sensor readings
int readingIndex = 0;

void loop() {
    unsigned long currentMillis = millis();

    if (currentMillis - startTime >= measurementPeriod) {
        startTime = currentMillis;

        // Compute wind sensor value
        float windSensorValue = (Count * 8.75) / 100.0;  // Corrected calculation
        Serial.print("WindSensor,");
        Serial.println(windSensorValue);

        if (Count == 0) {
            Serial.println("Warning: No wind sensor pulses detected");
        }

        // Reset pulse count for next period
        Count = 0;

        // Compute average rain sensor value
        int totalRain = 0;
        for (int i = 0; i < 5; i++) {
            totalRain += rainReadings[i];
        }
        float averageRain = totalRain / 5.0;
        Serial.print("RainSensor,");
        Serial.println(averageRain);

        // Reset rain readings array
        readingIndex = 0;
    }

    if (currentMillis - previousMillis >= interval) {
        previousMillis = currentMillis;

        // Read rain sensor value
        int rainSensorValue = analogRead(sensorPinAnalog);
        rainReadings[readingIndex] = rainSensorValue;
        readingIndex++;

        // Ensure the reading index wraps around after 5 readings
        if (readingIndex >= 5) {
            readingIndex = 0;
        }
    }
}
