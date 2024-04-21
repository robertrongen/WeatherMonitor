/*
    SkyMonitor Nano
    Starts light sensor and rain sensor and gets sensor data
    Prints sensor data to serial port
*/

// Light Sensor
#include "DFRobot_B_LUX_V30C.h"
DFRobot_B_LUX_V30C    myLux(13);//The sensor chip is set to 13 pins, SCL and SDA adopt default configuration
// DFRobot_B_LUX_V30C    myLux(13,A5,A4);//The sensor chip is set to 13 pins, SCL and SDA adopt default configuration
String lightSensor;

// Rain sensor
#define sensorPinDigital 3
// #define sensorPinAnalog A0
uint16_t rainVal;
boolean isRaining = false;
String raining = "No";  // Initialize to "No"

void setup() {
  delay(2000);
  Serial.begin(115200);
	while (!Serial);
  Serial.println("Serial of Nano connected");

  Wire.begin(); //Joing I2C bus
  delay(2000);
  // Connection test
  scanDevices();

  // Connect rain sensor
  pinMode(sensorPinDigital, INPUT_PULLUP);

  // Start light sensor
  myLux.begin(); // Start the light sensor
  
  delay(1000);
}

void loop() {
  unsigned long currentMillis = millis();  // Get the current time
  static unsigned long previousMillis = 0; // Stores the last time the sensors were read
  static unsigned long delayDuration = 5000; // Initial delay duration of 5000ms or 5 seconds
  const unsigned long hourMillis = 3600000; // Number of milliseconds in an hour

  // Update the delay duration after the first hour
  if (currentMillis >= hourMillis) {
    delayDuration = 60000; // Change to 60000ms or 60 seconds after the first hour
  }

  // Check if it's time to read the sensors again
  if (currentMillis - previousMillis >= delayDuration) {
    previousMillis = currentMillis; // Update the last read time

    // Sensor reading and serial output
    lightSensor = myLux.lightStrengthLux();
    Serial.print("LightSensor,");
    Serial.println(lightSensor);

    boolean isRainingDigital = digitalRead(sensorPinDigital);
    if (isRainingDigital == 0) {
      raining = "Yes";
    } else {
      raining = "No";
    }
    Serial.print("Raining,");
    Serial.println(raining);
  }

  // Other code that needs to run without delay can go here
}


void scanDevices() {
    byte error, address;
  int nDevices;

  Serial.println("Scanning...");

  nDevices = 0;
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
  if (nDevices == 0)
    Serial.println("Error, No I2C devices found\n");
  else
    Serial.println("scan done\n");
}

