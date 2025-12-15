/*
    SkyMonitor Nano
    Reads wind sensor and rain sensor
    Prints sensor data to serial port in JSON format
    Allows toggling debug mode via serial commands
*/

#include <Arduino.h>

// Rain sensor
#define sensorPinAnalog A0

// Wind Sensor
unsigned long lastDebounceTime = 0;  // Last debounce time
unsigned long debounceDelay = 100;  // Debounce delay
int pinInterrupt = 2;               // Interrupt pin for wind sensor
volatile int Count = 0;             // Pulse count (volatile for ISR)

unsigned long previousMillis = 0;
const long interval = 1000;         // Interval for rain sensor reading
unsigned long startTime = 0;
const long measurementPeriod = 5000;  // Measurement period for wind sensor

int rainReadings[5];               // Buffer for rain sensor readings
int readingIndex = 0;

// Debug Mode
bool debugMode = false;  // Default debug mode is OFF

// Debug Macros
#define DEBUG_PRINT(x) if (debugMode) Serial.print(x)
#define DEBUG_PRINTLN(x) if (debugMode) Serial.println(x)

// Interrupt Service Routine for Wind Sensor
void onChange() {
    if (digitalRead(pinInterrupt) == LOW) {
        Count++;
    }
}

void setup() {
    Serial.begin(115200);
    while (!Serial);  // Wait for serial port to connect
    DEBUG_PRINTLN("Serial of Nano connected");

    // Wind sensor setup
    pinMode(pinInterrupt, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(pinInterrupt), onChange, FALLING);
}

void loop() {
    handleSerialCommands();  // Check for incoming commands to toggle debug mode

    unsigned long currentMillis = millis();

    // Perform wind and rain calculations every measurement period
    if (currentMillis - startTime >= measurementPeriod) {
        startTime = currentMillis;

        // Compute wind sensor value
        float windSensorValue = (Count * 8.75) / 100.0;  // Corrected calculation
        DEBUG_PRINT("Wind pulses counted: ");
        DEBUG_PRINTLN(Count);

        // Reset pulse count
        Count = 0;

        // Compute average rain sensor value
        int totalRain = 0;
        for (int i = 0; i < 5; i++) {
            totalRain += rainReadings[i];
        }
        float averageRain = totalRain / 5.0;

        // Generate and send JSON output
        generateSensorJson(windSensorValue, averageRain);
    }

    // Collect rain sensor readings at regular intervals
    if (currentMillis - previousMillis >= interval) {
        previousMillis = currentMillis;

        // Read rain sensor value
        int rainSensorValue = analogRead(sensorPinAnalog);
        rainReadings[readingIndex] = rainSensorValue;
        readingIndex = (readingIndex + 1) % 5;  // Wrap around
    }
}

/*
    Handles incoming serial commands to toggle debug mode.
*/
void handleSerialCommands() {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();

        if (command == "DEBUG ON") {
            debugMode = true;
            Serial.println("Debug mode enabled");
        } else if (command == "DEBUG OFF") {
            debugMode = false;
            Serial.println("Debug mode disabled");
        } else {
            Serial.println("Unknown command");
        }
    }
}

/*
    Generates a JSON string with wind and rain sensor data and sends it to the serial port.
*/
void generateSensorJson(float windSensorValue, float averageRain) {
    String jsonStr = "{";
    jsonStr += "\"wind_speed\":" + String(windSensorValue, 2) + ",";
    jsonStr += "\"rain_intensity\":" + String(averageRain, 2);
    jsonStr += "}";
    Serial.println(jsonStr);  // JSON data is always sent
}
