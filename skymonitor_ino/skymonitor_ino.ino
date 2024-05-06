/*
    SkyMonitor Nano
    Starts light sensor and rain sensor and gets sensor data
    Prints sensor data to serial port
*/

// Light Sensor
#include "DFRobot_B_LUX_V30C.h"
DFRobot_B_LUX_V30C    myLux(13);//The sensor chip is set to 13 pins, SCL and SDA adopt default configuration

// Rain sensor
#define sensorPinAnalog A0

void setup() {
    Serial.begin(115200);
    while (!Serial);
    Serial.println("Serial of Nano connected");

    Wire.begin(); //Joing I2C bus
    // Connection test
    scanDevices();

    // Start light sensor
    myLux.begin(); // Start the light sensor
}

unsigned long previousMillis = 0;
const long interval = 1000; // Interval at which to read sensors

void loop() {
    unsigned long currentMillis = millis();

    if (currentMillis - previousMillis >= interval) {
        previousMillis = currentMillis;
        
        int lightSensorValue = myLux.lightStrengthLux();
        Serial.print("LightSensor,");
        Serial.println(lightSensorValue);

        int rainSensorValue = analogRead(sensorPinAnalog);
        Serial.print("Rainsensor,");
        Serial.println(rainSensorValue);
    }
}

bool scanDevices() {
    byte error, address;
    int nDevices = 0;
    Serial.println("Scanning...");

    for (address = 1; address < 127; address++ ) {
        Wire.beginTransmission(address);
        error = Wire.endTransmission();

        if (error == 0) {
            Serial.print("I2C device found at address 0x");
            if (address < 16)
                Serial.print("0");
            Serial.print(address, HEX);
            Serial.println(" !");
            nDevices++;
        }
    }
    if (nDevices == 0) {
        Serial.println("Error, No I2C devices found");
        return false;
    } else {
        Serial.println("Scan done.");
        return true;
    }
}
