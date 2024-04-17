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
  pinMode(sensorPinDigital, INPUT);

  // Start light sensor
  myLux.begin(); // Start the light sensor
  
  delay(1000);
}

void loop() {
  lightSensor = myLux.lightStrengthLux();
  Serial.print("LightSensor,");
  Serial.println(lightSensor);

  boolean isRainingDigital = digitalRead(sensorPinDigital);
  Serial.print("isRainingDigital,");
  Serial.println(isRainingDigital);
  if (isRainingDigital == 1) {
    raining = "Yes";
  } else {
    raining = "No";
  }
  Serial.print("Raining,");
  Serial.println(raining);

  delay(5000);
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

