/*
    Starts IR temp (MLX90614) and Sky quality (TSL2591) sensors
    Collects sensor data in JSON file
    Sends JSON file to serial port
    Allows toggling debug mode via serial commands
    - Enable debug mode: echo "DEBUG ON" > /dev/ttyUSB0
    - Disable debug mode: echo "DEBUG OFF" > /dev/ttyUSB0
*/

#include "wifi_sensors.h"

#define SENSOR_INTERVAL 30000 // Data sent every 30 seconds

// JSON Document Declaration
JsonDocument doc = StaticJsonDocument<1024>();

// Sensor Objects
Adafruit_TSL2591 tsl = Adafruit_TSL2591(2591);
IRTherm therm;

// Sensor Status Flags
bool TSL2591_working = false;
bool MLX90614_working = false;

// Temperature Buffers
char skyTemp[16] = ""; 
char ambientTemp[16] = "";

// Debug Mode
bool debugMode = false; // Default debug mode is OFF

// Debug Macros
#define DEBUG_PRINT(x) if (debugMode) Serial.print(x)
#define DEBUG_PRINTLN(x) if (debugMode) Serial.println(x)

void setup() {
    Serial.begin(115200);
    while (!Serial);
    DEBUG_PRINTLN("Serial of D1Mini connected");

    Wire.begin();                 // Initialize I2C bus
    scanDevices();
    configureMLX90614();
    configureTSL2591();

    pinMode(LED_BUILTIN, OUTPUT); // LED pin as output
    delay(1000);
}

void loop() {
    handleSerialCommands(); // Check for incoming commands to toggle debug mode

    if (!MLX90614_working) configureMLX90614();
    if (!TSL2591_working) configureTSL2591();

    // LED Feedback for Sensor Status
    if (MLX90614_working && TSL2591_working) {
        digitalWrite(LED_BUILTIN, LOW);
        delay(500);
        digitalWrite(LED_BUILTIN, HIGH);
    } else {
        for (int i = 0; i < 3; i++) {
            digitalWrite(LED_BUILTIN, LOW);
            delay(200);
            digitalWrite(LED_BUILTIN, HIGH);
            delay(200);
        }
    }

    if (MLX90614_working) fetchSkyTemp();
    if (TSL2591_working) advancedRead();

    generateSensorJson();
    delay(SENSOR_INTERVAL);
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
    Generates JSON with sensor data and sends it to the serial port.
*/
void generateSensorJson() {
    if (MLX90614_working && strlen(skyTemp) > 0 && strlen(ambientTemp) > 0) {
        doc["sky_temperature"] = skyTemp;
        doc["ambient_temperature"] = ambientTemp;
    } else {
        doc["sky_temperature"] = "N/A";
        doc["ambient_temperature"] = "N/A";
    }

    if (!TSL2591_working) {
        doc["sqm_ir"] = "N/A";
        doc["sqm_full"] = "N/A";
        doc["sqm_visible"] = "N/A";
        doc["sqm_lux"] = "N/A";
    }

    String jsonStr;
    if (!serializeJson(doc, jsonStr)) {
        DEBUG_PRINTLN("Error: Failed to serialize JSON");
    } else {
        Serial.println(jsonStr); // JSON data sent to serial port
    }
}

/*
    Configures the MLX90614 sensor.
*/
void configureMLX90614() {
    therm.begin();
    if (therm.isConnected()) {
        therm.setUnit(TEMP_C);
        MLX90614_working = true;
        DEBUG_PRINTLN("MLX90614 IR temp sensor initialized.");
    } else {
        MLX90614_working = false;
        DEBUG_PRINTLN("No MLX90614 IR temp sensor found.");
    }
}

/*
    Reads temperatures from the MLX90614 sensor.
*/
void fetchSkyTemp() {
    if (!therm.isConnected()) {
        therm.begin();
        delay(2000);
        if (!therm.isConnected()) {
            DEBUG_PRINTLN("Error: MLX IR thermometer not connected.");
            return;
        }
        therm.setUnit(TEMP_C);
    }
    readSkyTemp();
}

/*
    Stores temperature data into buffers.
*/
void readSkyTemp() {
    if (therm.read()) {
        snprintf(skyTemp, sizeof(skyTemp), "%.2f", therm.object());
        snprintf(ambientTemp, sizeof(ambientTemp), "%.2f", therm.ambient());
        DEBUG_PRINT("Sky Temperature: ");
        DEBUG_PRINTLN(skyTemp);
        DEBUG_PRINT("Ambient Temperature: ");
        DEBUG_PRINTLN(ambientTemp);
    } else {
        DEBUG_PRINTLN("Error: Failed to read temperatures from MLX90614");
    }
}

/*
    Configures the TSL2591 sensor.
*/
void configureTSL2591() {
    if (tsl.begin()) {
        configureSensor();
        TSL2591_working = true;
        DEBUG_PRINTLN("TSL2591 sky quality sensor initialized.");
    } else {
        TSL2591_working = false;
        DEBUG_PRINTLN("No TSL2591 sky quality sensor found.");
    }
}

/*
    Configures gain and integration time for the TSL2591 sensor.
*/
void configureSensor(void) {
    tsl.setGain(TSL2591_GAIN_HIGH);
    tsl.setTiming(TSL2591_INTEGRATIONTIME_500MS);
}

/*
    Reads IR and Full Spectrum data and calculates lux.
*/
void advancedRead(void) {
    uint32_t lum = tsl.getFullLuminosity();
    if (lum == 0) {
        DEBUG_PRINTLN("Error: Failed to read luminosity");
        return;
    }
    uint16_t ir = lum >> 16;
    uint16_t full = lum & 0xFFFF;
    uint16_t visible = full - ir;
    if (full > 0 && ir > 0) {
        float lux = tsl.calculateLux(full, ir);
        doc["sqm_lux"] = lux;
    } else {
        doc["sqm_lux"] = "N/A";
        DEBUG_PRINTLN("Error: Invalid luminosity values");
    }
    doc["sqm_ir"] = ir;
    doc["sqm_full"] = full;
    doc["sqm_visible"] = visible;
}

/*
    Scans for I2C devices on the bus.
*/
void scanDevices() {
    byte error, address;
    int nDevices = 0;

    DEBUG_PRINTLN("Scanning...");
    for (address = 1; address < 127; address++ ) {
        Wire.beginTransmission(address);
        error = Wire.endTransmission();

        if (error == 0) {
            DEBUG_PRINT("I2C device found at address 0x");
            DEBUG_PRINT((address < 16 ? "0" : ""));
            DEBUG_PRINTLN(String(address, HEX) + "!");
            nDevices++;
        }
    }
    if (nDevices == 0)
        DEBUG_PRINTLN("Error: No I2C devices found");
    else
        DEBUG_PRINTLN("Scan complete");
}
