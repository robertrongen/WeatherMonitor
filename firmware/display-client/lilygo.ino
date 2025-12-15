// add additional board manager:
// https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_dev_index.json
// install esp32 board by Espressif Systems
// install TFT_eSPI library
// Select the board ESP32S3 Dev Module
// Reference: https://github.com/Xinyuan-LilyGO/T-Display-S3
// Flash new firmware mode: Hold bottom-right button down, plug USB in, release button

#include <WiFi.h>
#include <HTTPClient.h>
#include <TFT_eSPI.h> 
#include <ArduinoJson.h>
#include "secrets.h"

const char *ssid1 = STASSID1;
const char *password1 = STAPSK1;
const char *ssid2 = STASSID2;
const char *password2 = STAPSK2;
const char *ssid3 = STASSID3;
const char *password3 = STAPSK3;
const char *ssid4 = STASSID4;
const char *password4 = STAPSK4;

const char* serverName = "http://allsky.local:5000/api/sky_data";

TFT_eSPI tft = TFT_eSPI();
int page = 1; // Track the current page

void setup() {
  Serial.begin(115200);

  // Initialize the display
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);

  // Connect to Wi-Fi
  connectToWiFi();

  // Fetch and display weather data
  fetchWeatherData();
}

void loop() {
  // Update weather data periodically
  fetchWeatherData();
  delay(60000); // Update every 60 seconds

  // Check for button press to change page
  if (digitalRead(0) == LOW) { // Assuming a button is connected to GPIO 0
    page = (page == 1) ? 2 : 1;
    fetchWeatherData(); // Refresh data on page change
  }
}

void connectToWiFi() {
  // Try connecting to each SSID until one is successful
  WiFi.begin(ssid1, password1);
  if (waitForConnectResult() != WL_CONNECTED) {
    WiFi.begin(ssid2, password2);
  }
  if (waitForConnectResult() != WL_CONNECTED) {
    WiFi.begin(ssid3, password3);
  }
  if (waitForConnectResult() != WL_CONNECTED) {
    WiFi.begin(ssid4, password4);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Connected to WiFi");
  } else {
    Serial.println("Failed to connect to any WiFi network");
  }
}

int waitForConnectResult() {
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - start > 10000) { // Wait for 10 seconds
      return WiFi.status();
    }
    delay(100);
  }
  return WiFi.status();
}

void fetchWeatherData() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);

    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
      String payload = http.getString();
      Serial.println(payload);
      displayWeatherData(payload);
    } else {
      Serial.println("Error in HTTP request");
    }

    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
}

void displayWeatherData(String data) {
  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, data);
  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return;
  }

  // Clear the screen
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0, 0);

  if (page == 1) {
    tft.println("Page 1 (DAY):");
    tft.println("Ambient Temp: " + String(doc["ambient_temperature"].as<float>()) + " C");
    tft.println("Camera Temp: " + String(doc["camera_temp"].as<int>()) + " C");
    tft.println("Fan Status: " + String(doc["fan_status"].as<const char*>()));
    tft.println("Heater Status: " + String(doc["heater_status"].as<const char*>()));
    tft.println("Humidity: " + String(doc["humidity"].as<float>()) + " %");
    tft.println("Raining: " + String(doc["raining"].as<const char*>()));
    tft.println("Temperature: " + String(doc["temperature"].as<float>()) + " C");
    tft.println("Wind: " + String(doc["wind"].as<int>()) + " km/h");
  } else {
    tft.println("Page 2 (NIGHT):");
    tft.println("Cloud Coverage: " + String(doc["cloud_coverage"].as<float>()));
    tft.println("Cloud Coverage Ind: " + String(doc["cloud_coverage_indicator"].as<float>()));
    tft.println("Light: " + String(doc["light"].as<const char*>()));
    tft.println("Sky Temp: " + String(doc["sky_temperature"].as<float>()) + " C");
    tft.println("SQM Full: " + String(doc["sqm_full"].as<int>()));
    tft.println("SQM IR: " + String(doc["sqm_ir"].as<int>()));
    tft.println("SQM Lux: " + String(doc["sqm_lux"].as<float>()));
    tft.println("SQM Visible: " + String(doc["sqm_visible"].as<int>()));
    tft.println("Star Count: " + String(doc["star_count"].as<int>()));
  }
}
