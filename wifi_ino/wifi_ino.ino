/*
    SkyMonitor WiFi
    Starts WiFi and connects to Wodan network
    Starts IR temp and tsl2591 sensors and gets sensor data
    Gets gets external sensor data
    Publishes sensor data to a local webserver
    Triggers a IFTTT notication when raining
*/

#include "secrets.h"
// #include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <Wire.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP8266WiFiMulti.h>
ESP8266WiFiMulti wifiMulti;
// Check stack space
#include "cont.h"

// WiFi connect timeout per AP. Increase when connecting takes longer.
const uint32_t connectTimeoutMs = 5000;
// WIFI
const char *ssid1 = STASSID1;
const char *password1 = STAPSK1;
const char *ssid2 = STASSID2;
const char *password2 = STAPSK2;
const char *ssid3 = STASSID3;
const char *password3 = STAPSK3;
const char *ssid4 = STASSID4;
const char *password4 = STAPSK4;
String activeWifiSSID = ""; // Initialize to an empty string
bool wasConnected = false;  // Flag to track if WiFi was previously connected

// SkyMonitor WebServer
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>
ESP8266WebServer server(80);

// IR Temp Sensor
#include <SparkFunMLX90614.h> //Click here to get the library: http://librarymanager/All#Qwiic_IR_Thermometer by SparkFun
IRTherm therm; // Create an IRTherm object to interact with throughout
String skyTemp, ambientTemp;

// TSL2591 sensor
#include <Adafruit_Sensor.h>
#include "Adafruit_TSL2591.h"
Adafruit_TSL2591 tsl = Adafruit_TSL2591(2591); // pass in a number for the sensor identifier (for your use later)
uint16_t ir, full, Visible;
float Lux;

// Sensor data from Arduino Nano
String lightSensor, raining;
String nanoDataBuffer = "";

// Collect data in JSON file
DynamicJsonDocument doc(1024);

// IFTTT notification
const char* host = "maker.ifttt.com";
const char* apiKey = "dhJGM9-KI-OZ1vktxst18SkrEqIrXoueLfcYR4bIOFt";
const char* eventName = "SkyMonitor_Alarm";

// Logging to webserver
#define SERIAL_BUFFER_SIZE 2000
String serialBuffer = "";
const int MAX_LOG_ENTRIES = 50;  // Adjust as needed
String logEntries[MAX_LOG_ENTRIES];
int logIndex = 0;

void setup() {
  delay(1000);
  Serial.begin(115200);
  // while (!Serial);
  // Serial.println("Serial of D1Mini connected");
  customSerialPrintln("Serial of D1Mini connected");
  startWifiMulti();
  startWebserver();

  Wire.begin();                 //Joing I2C bus
  delay(1000);
  scanDevices();
  therm.begin();                // Start IR temp sensor
  fetchSkyTemp();

  tsl.enable();
  if (tsl.begin()) {
    // Serial.println(F("Found a TSL2591 sensor"));
  } else {
    // Serial.println(F("No TSL2591 sensor found"));
    customSerialPrintln("No TSL2591 sensor found");
    while (1);
  }
  configureSensor();            // Configure the sensor

  pinMode(LED_BUILTIN, OUTPUT); // LED pin as output
  delay(1000);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);

  maintainWifi();
  server.handleClient();
  MDNS.update();

  // Collect and update sensor data
  fetchSkyTemp();
  advancedRead();
  fetchNanoData();
  generateSensorJson();

  delay(9000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
  memoryMonitor();
}

void memoryMonitor() {
    // Print free heap memory every minute
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 60000) {
    customSerialPrint("Free heap: ");
    customSerialPrintln(String(ESP.getFreeHeap()));
    lastPrint = millis();
  }
  // Print stack space left every minute
  static unsigned long lastStackPrint = 0;
  if (millis() - lastStackPrint > 60000) {
    customSerialPrint("Stack space left: ");
    customSerialPrintln(String(cont_get_free_stack(g_pcont)));
    lastStackPrint = millis();
  }
}

void handleRoot() {
  String html = "<html><head>";
  html += "<style>";
  html += "html { font-size:100%; }";
  html += "body { background-color: #000000; color: #FFFFFF; font-family: Arial, sans-serif; }";
  html += "table { border-collapse: collapse; color: #FFFFFF; min-width: 400px}";
  html += "td, th { border: 1px solid #FFFFFF; padding: 5px; text-align: left; }";
  html += "th { background-color: #333333; }";
  html += "@media (min-width:800px) { body {font-size:1.5rem;} } { table { width: 100%}}";
  html += "</style>";
  html += "</head><body>";

  html += "</style></head><body>";

  html += "<h1>Safety monitor</h1>";

  html += "<h2>Safety status</h2>";
  html += "<table border='1'>";
  html += "<tr><th>Sensor</th><th>Data</th></tr>"; // Table headers
  String rainingColor = (raining.indexOf("Yes") != -1) ? "#FF0000" : (raining.indexOf("No") != -1) ? "#008000" : "#808080";
  html += "<tr><td>Is raining?</td><td style='background-color: " + rainingColor + ";'>" + raining + "</td></tr>";
  html += "<tr><td>Is it cloudy?</td><td>tbd</td></tr>";
  html += "<tr><td>Is it dark?</td><td>tbd</td></tr>";
  html += "</table>";

  html += "<h2>Sensor data</h2>";
  html += "<table border='1'>";
  html += "<tr><th>Sensor</th><th>Data</th><th>Unit</th></tr>"; // Table headers
  html += "<tr><td>SEN0390 Light Sensor (from Nano)</td><td>" + lightSensor + "</td><td>lx</td></tr>";
  html += "<tr><td>IR Sky Temp MLX90614</td><td>" + skyTemp + "</td><td>&#8451;</td></tr>";
  html += "<tr><td>Ambient Temperature MLX90614</td><td>" + ambientTemp + "</td><td>&#8451;</td></tr>";
  html += "<tr><td>TSL2591 IR spectrum</td><td>" + String(ir) + "</td><td>-</td></tr>";
  html += "<tr><td>TSL2591 Full spectrum</td><td>" + String(full) + "</td><td>-</td></tr>";
  html += "<tr><td>TSL2591 Visible spectrum</td><td>" + String(Visible) + "</td><td>-</td></tr>";
  html += "<tr><td>TSL2591 Lux</td><td>" + String(Lux) + "</td><td>Lux</td></tr>";
  html += "</table>";

  html += "<h2>Serial Output</h2>";
  html += "<div style='border:1px solid white; padding:10px; font-size:0.6 rem; height:200px; overflow-y:scroll;'>";
  for (int i = 0; i < MAX_LOG_ENTRIES; i++) {
    int idx = (logIndex + i) % MAX_LOG_ENTRIES;
    if (logEntries[idx].length() > 0) {
        html += logEntries[idx] + "<br>";
    }
  }
  html += "</div>";

  html += "<h2>Clear Outside Forecast Tilburg</h2>";
  html += "<a href='https://clearoutside.com/forecast/51.55/5.05'><img src='https://clearoutside.com/forecast_image_small/51.55/5.05/forecast.png'/></a>";

  html += "</body></html>";
  
  server.send(200, "text/html", html);
}

// SkyMonitor_Alarm 2 IFTTT notification
void triggerIFTTT() {
  WiFiClient client;

  if (!client.connect(host, 80)) {
    customSerialPrintln("Connection to IFTTT failed.");
    return;
  }

  String url = "/trigger/";
  url += eventName;
  customSerialPrint("Requesting URL: ");
  customSerialPrintln(url);
  url += "/with/key/";
  url += apiKey;

  client.print(String("GET ") + url + " HTTP/1.1\r\n" +
               "Host: " + host + "\r\n" +
               "Connection: close\r\n\r\n");

  while (client.connected()) {
    String line = client.readStringUntil('\n');
    if (line == "\r") {
      break;
    }
  }

  String line = client.readStringUntil('\n');
  customSerialPrintln(line);
}

void startWifiMulti() {
  WiFi.persistent(false);

  // Set WiFi to station mode
  WiFi.mode(WIFI_STA);

  // Register multi WiFi networks
  wifiMulti.addAP(ssid1, password1);
  wifiMulti.addAP(ssid2, password2);
  wifiMulti.addAP(ssid3, password3);
  wifiMulti.addAP(ssid4, password4);

  // Connect to the first available network
  Serial.println("Looking for a network...");
  if (wifiMulti.run() == WL_CONNECTED) {
      customSerialPrint("Successfully connected to network: ");
      customSerialPrint(WiFi.SSID());
      customSerialPrint(" with IP address: ");
      customSerialPrintln(WiFi.localIP().toString());
      activeWifiSSID = WiFi.SSID();
  } else {
      customSerialPrintln("Failed to connect to a WiFi network");
  }
}

void maintainWifi() {
    // Maintain WiFi connection
  if (wifiMulti.run(connectTimeoutMs) == WL_CONNECTED) {
    if (WiFi.SSID() != activeWifiSSID) {
      Serial.print("New WiFi connected: ");
      Serial.print(WiFi.SSID());
      Serial.print(" with IP address: ");
      Serial.println(WiFi.localIP());
      activeWifiSSID = WiFi.SSID();
    }
    wasConnected = true;
  } else {
    if (wasConnected) { // Only print once when WiFi gets disconnected
      Serial.println("WiFi not connected!");
      wasConnected = false;
    }
  }
}

void fetchSkyTemp() {
  if (therm.isConnected()) {
    readSkyTemp();
  } else {
    therm.begin();
    delay(2000);
    if (!therm.isConnected()){
      // Serial.println("Error connecting to MLX IR thermometer. Check wiring.");
      customSerialPrintln("Error connecting to MLX IR thermometer. Check wiring.");
    } else {
      // Serial.println("MLX sensor IR Thermometer did connect.");
      therm.setUnit(TEMP_C); // Set the library's units to Celcius
      readSkyTemp();
    }
  }
}

void readSkyTemp() {
  if (therm.read()) { // On success, read() will return 1, on fail 0.
    // Use the object() and ambient() functions to grab the object and ambient temperatures
    // They'll be floats, calculated out to the unit you set with setUnit().
    skyTemp = therm.object();
    ambientTemp = therm.ambient();
    customSerialPrint("Sky Temp: " + String(therm.object(), 2));
    customSerialPrint(" C");
    customSerialPrint("    Ambient Temp: " + String(therm.ambient(), 2));
    customSerialPrintln(" C");
  }
}

void fetchNanoData() {
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') {
            processSerialData(nanoDataBuffer);
            nanoDataBuffer = "";
        } else {
            nanoDataBuffer += c;
        }
    }
}

void processSerialData(String data) {
  int commaIndex = data.indexOf(',');
  String sensorID = data.substring(0, commaIndex);
  String sensorValue = data.substring(commaIndex + 1);

  if (sensorID == "LightSensor") {
    if ((sensorValue != "-1") && (sensorValue != "")) {
      lightSensor = sensorValue;
    } else {
      lightSensor = "dataread_failed";
    }
  } else if (sensorID == "Raining") {
    raining = sensorValue;
    Serial.print("SensorValue Raining Received: ");
    Serial.println(raining);
    if (raining.indexOf("Yes") != -1) {
        triggerIFTTT();
    }
  // } else if (sensorID == "RainValue") {
  //   rainValue = sensorValue;
  }
  printNanoData(sensorID, sensorValue);
}

void printNanoData(String sensor, String value) {
  // Serial.print(sensor);
  // Serial.print(": ");
  // Serial.println(value);
  customSerialPrint(sensor);
  customSerialPrint(": ");
  customSerialPrintln(value);
}

void generateSensorJson() {
  // rainValue.trim();     
  lightSensor.trim();     

  doc["raining"] = raining;
  doc["light"] = lightSensor;
  doc["sky_temperature"] = skyTemp;
  doc["ambient_temperature"] = ambientTemp;
  doc["sqm_ir"] = ir;
  doc["sqm_full"] = full;
  doc["sqm_visible"] = Visible;
  doc["sqm_lux"] = Lux;

  String jsonStr;
  serializeJson(doc, jsonStr);
  // Serial.println(jsonStr);
  customSerialPrintln(jsonStr);
}

void startWebserver() {
  if (MDNS.begin("skymonitor")) {
    customSerialPrintln("MDNS responder started");
    customSerialPrintln("access via http://skymonitor.local");
  }
  server.on("/", handleRoot);
  // This will handle GET requests on /json
  server.on("/json", HTTP_GET, []() {
    String jsonStr;
    if (serializeJson(doc, jsonStr) == 0) {
      server.send(500, "application/json", "{\"error\":\"Failed to generate JSON\"}");
    } else {
      server.send(200, "application/json", jsonStr);
    }
  });

  // This will catch all other methods on /json
  server.on("/json", []() {
    server.send(405, "text/plain", "Method Not Allowed. Use GET.");
  });
  server.on("/inline", []() {
    server.send(200, "text/plain", "this works as well");
  });
  server.onNotFound(handleNotFound);
  server.begin();
  customSerialPrintln("HTTP server started");
}

void handleNotFound() {
  String message = "File Not Found";
  message += "URI: ";
  message += server.uri();
  message += "Method: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "Arguments: ";
  message += server.args();
  message += "";

  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "";
  }

  server.send(404, "text/plain", message);
}

// Configures the gain and integration time for the TSL2591
void configureSensor(void) {
  // You can change the gain on the fly, to adapt to brighter/dimmer light situations
  //tsl.setGain(TSL2591_GAIN_LOW);    // 1x gain (bright light)
  // tsl.setGain(TSL2591_GAIN_MED);      // 25x gain
  tsl.setGain(TSL2591_GAIN_HIGH);   // 428x gain
  
  // Changing the integration time gives you a longer time over which to sense light
  // longer timelines are slower, but are good in very low light situtations!
  //tsl.setTiming(TSL2591_INTEGRATIONTIME_100MS);  // shortest integration time (bright light)
  // tsl.setTiming(TSL2591_INTEGRATIONTIME_200MS);
  // tsl.setTiming(TSL2591_INTEGRATIONTIME_300MS);
  // tsl.setTiming(TSL2591_INTEGRATIONTIME_400MS);
  tsl.setTiming(TSL2591_INTEGRATIONTIME_500MS);
  // tsl.setTiming(TSL2591_INTEGRATIONTIME_600MS);  // longest integration time (dim light)

  // Display the gain and integration time for reference sake  
  customSerialPrintln(F("------------------------------------"));
  customSerialPrint(F("Gain:         "));
  tsl2591Gain_t gain = tsl.getGain();
  switch(gain)
  {
    case TSL2591_GAIN_LOW:
      customSerialPrintln(F("1x (Low)"));
      break;
    case TSL2591_GAIN_MED:
      customSerialPrintln(F("25x (Medium)"));
      break;
    case TSL2591_GAIN_HIGH:
      customSerialPrintln(F("428x (High)"));
      break;
    case TSL2591_GAIN_MAX:
      customSerialPrintln(F("9876x (Max)"));
      break;
  }
  customSerialPrint  (F("Timing:       "));
  customSerialPrint(String((tsl.getTiming() + 1) * 100, DEC)); 
  customSerialPrintln(F(" ms"));
  customSerialPrintln(F("------------------------------------"));
  customSerialPrintln(F(""));
}

// Reads IR and Full Spectrum at once and convert to lux
void advancedRead(void) {
  // More advanced data read example. Read 32 bits with top 16 bits IR, bottom 16 bits full spectrum
  // That way you can do whatever math and comparisons you want!
  uint32_t lum = tsl.getFullLuminosity();
  ir = lum >> 16;
  full = lum & 0xFFFF;
  Visible = full - ir;
  Lux = tsl.calculateLux(full, ir);
  // Serial.print(F("[ ")); Serial.print(millis()); Serial.print(F(" ms ] "));
  // Serial.print(F("IR: ")); Serial.print(ir);  Serial.print(F("  "));
  // Serial.print(F("Full: ")); Serial.print(full); Serial.print(F("  "));
  customSerialPrint(F("Visible: ")); customSerialPrint(String(full - ir)); customSerialPrint(F("  "));
  customSerialPrint(F("Lux: ")); customSerialPrintln(String(tsl.calculateLux(full, ir), 6));
}

void scanDevices() {
    byte error, address;
  int nDevices;

  customSerialPrintln("Scanning...");

  nDevices = 0;
  for (address = 1; address < 127; address++ ) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      customSerialPrint("I2C device found at address 0x");
      if (address < 16)
        customSerialPrint("0");
      customSerialPrint(String(address, HEX));
      customSerialPrintln(" !");

      nDevices++;
    }
  }
  if (nDevices == 0)
    customSerialPrintln("Error, No I2C devices found");
  else
    customSerialPrintln("scan done");
}

void addLogEntry(const String &message, bool newLine = true) {
    if (newLine) {
        logEntries[logIndex] = message;
        logIndex = (logIndex + 1) % MAX_LOG_ENTRIES;  // Circular buffer
    } else {
        // Append to the last log entry
        logEntries[(logIndex - 1 + MAX_LOG_ENTRIES) % MAX_LOG_ENTRIES] += message;
    }
}

// Custom function to print to both Serial and the buffer
void customSerialPrint(const String &message) {
  Serial.print(message);
  addLogEntry(message, false);
}

// Custom function to print to both Serial and the buffer with newline
void customSerialPrintln(const String &message) {
  customSerialPrint(message + "\n");
  addLogEntry("\n", false);  // Append a newline to the last log entry
}