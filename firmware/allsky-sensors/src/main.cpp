/*
 * AllSky Sensors - Heltec WiFi LoRa 32 V2 Firmware
 * BUILD VERSION: 1.0.2 - FIELD TEST MODE (NO SERIAL)
 *
 * Hardware: Heltec WiFi LoRa 32 V2 (ESP32-PICO-D4 + SX1276 LoRa + OLED)
 * Backend: The Things Network (TTN) v3 or Chirpstack
 *
 * Integrated Components (Pre-wired):
 * - LoRa Radio: SX1276 (868/915 MHz) internally connected via SPI
 * - OLED Display: 0.96" SSD1306 (I²C 0x3C) for field diagnostics
 * - Status LED: GPIO25 (for field test mode visual feedback)
 *
 * External Sensors (GPIO21/22 I²C bus - separate from display):
 * - MLX90614 IR Temperature Sensor (I²C 0x5A)
 * - TSL2591 Sky Quality Meter (I²C 0x29)
 * - RG-9 Rain Sensor (Analog GPIO36 with voltage divider)
 * - Wind Sensor (Pulse mode GPIO32 with optocoupler - moved from GPIO34 to avoid LoRa DIO conflict)
 *
 * Pin Mappings (Heltec WiFi LoRa 32 V2):
 * LoRa SPI (internal):    GPIO5 (SCK), GPIO19 (MISO), GPIO27 (MOSI)
 * LoRa Control (internal): GPIO18 (CS), GPIO14 (RST), GPIO26 (DIO0), GPIO33 (DIO1)
 * Display I²C (internal):  GPIO4 (SDA), GPIO15 (SCL), GPIO16 (RST)
 * Sensor I²C (external):   GPIO21 (SDA), GPIO22 (SCL)
 * Rain ADC:                GPIO36 (ADC1_CH0) with 5.1kΩ/10kΩ divider
 * Wind Pulse:              GPIO32 (interrupt, moved from GPIO34 to avoid DIO2 conflict)
 * Status LED:              GPIO25 (for field test mode)
 *
 * Architecture: docs/architecture/board-esp32-lora-display/ARCHITECTURE_BOARD_ESP32_LORA_DISPLAY.md
 * Wiring: docs/architecture/board-esp32-lora-display/HARDWARE_WIRING_ESP32_LORA_DISPLAY.md
 */

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <lmic.h>
#include <hal/hal.h>
#include <SSD1306Wire.h>
#include <Adafruit_MLX90614.h>
#include <Adafruit_TSL2591.h>
#include "secrets.h"

// ============================================================================
// LORAWAN OTAA CALLBACK FUNCTIONS (Required by MCCI LMIC 4.x)
// ============================================================================

// Application EUI for OTAA (from secrets.h)
void os_getArtEui (u1_t* buf) {
    memcpy_P(buf, APPEUI, 8);
}

// Device EUI for OTAA (from secrets.h)
void os_getDevEui (u1_t* buf) {
    memcpy_P(buf, DEVEUI, 8);
}

// Application Key for OTAA (from secrets.h)
void os_getDevKey (u1_t* buf) {
    memcpy_P(buf, APPKEY, 16);
}

// ============================================================================
// HARDWARE CONFIGURATION
// ============================================================================

// OLED Display (Internal I²C bus GPIO4/15)
#define OLED_SDA 4
#define OLED_SCL 15
#define OLED_RST 16
#define OLED_ADDR 0x3C

// Sensor I²C Bus (External GPIO21/22 - separate from display)
#define SENSOR_SDA 21
#define SENSOR_SCL 22

// Rain Sensor (Analog)
#define RAIN_PIN 36  // GPIO36 (ADC1_CH0)

// Wind Sensor (Pulse Interrupt)
// NOTE: Moved from GPIO34 to GPIO32 to avoid conflict with LoRa DIO pins
// GPIO34 is input-only and close to SX1276 internal routing
#define WIND_PIN 32  // GPIO32 (safe for interrupt, no LoRa conflict)

// Status LED for Field Test Mode
#define STATUS_LED 25  // GPIO25 (Heltec V2 onboard LED)

// LoRa Pin Mapping (Heltec WiFi LoRa 32 V2 - aligned with BSP)
// These pins are hardware-wired on the Heltec board - do NOT change
const lmic_pinmap lmic_pins = {
    .nss = 18,         // GPIO18 (LoRa CS) - Heltec hardwired
    .rxtx = LMIC_UNUSED_PIN,
    .rst = 14,         // GPIO14 (LoRa RST) - Heltec hardwired
    .dio = {26, 35, 34},  // DIO0=26, DIO1=35, DIO2=34 (Heltec V2 wiring)
    .rxtx_rx_active = 0,
    .rssi_cal = 10,
    .spi_freq = 8000000  // 8 MHz SPI (standard for SX1276)
};

// ============================================================================
// GLOBAL OBJECTS
// ============================================================================

// Display (128x64 OLED on internal I²C bus)
SSD1306Wire display(OLED_ADDR, OLED_SDA, OLED_SCL);

// Sensor Objects (on external I²C bus GPIO21/22)
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
Adafruit_TSL2591 tsl = Adafruit_TSL2591(2591);

// Sensor I²C Bus (separate from display)
TwoWire sensorWire = TwoWire(1);  // Use I2C bus 1 for sensors

// ============================================================================
// SENSOR DATA STRUCTURE
// ============================================================================

struct SensorData {
    // Rain sensor (0-1023, lower = wetter)
    uint16_t rain_intensity;
    
    // Wind sensor (m/s)
    float wind_speed;
    
    // MLX90614 IR temperature (°C)
    float sky_temperature;
    float ambient_temperature;
    
    // TSL2591 Sky Quality Meter
    uint16_t sqm_ir;
    uint16_t sqm_full;
    uint16_t sqm_visible;
    float sqm_lux;
    
    // Diagnostics
    uint32_t uptime_seconds;
    int16_t rssi;
    int8_t snr;
    uint16_t battery_mv;  // Battery voltage if applicable
    
    // Data quality flags
    bool mlx_valid;
    bool tsl_valid;
    bool rain_valid;
    bool wind_valid;
};

SensorData sensorData = {0};

// ============================================================================
// WIND SENSOR STATE (Pulse Counting)
// ============================================================================

volatile uint32_t windPulseCount = 0;
volatile uint32_t lastWindPulse = 0;
const uint32_t WIND_DEBOUNCE_MS = 10;  // 10ms debounce

void IRAM_ATTR windPulseISR() {
    uint32_t now = millis();
    if (now - lastWindPulse > WIND_DEBOUNCE_MS) {
        windPulseCount++;
        lastWindPulse = now;
    }
}

// ============================================================================
// LORAWAN STATE
// ============================================================================

static osjob_t sendjob;
bool joined = false;
bool transmitting = false;
uint32_t nextTransmissionTime = 0;
const uint32_t TX_INTERVAL_MS = 60000;  // 60 seconds

// Loop diagnostic counters
uint32_t loopCount = 0;
uint32_t lastLoopLog = 0;
const uint32_t LOOP_LOG_INTERVAL_MS = 5000;  // Log every 5 seconds

// ============================================================================
// FIELD TEST MODE STATE
// ============================================================================

// Field test mode counters
uint32_t joinAttempts = 0;
uint32_t txCount = 0;
uint32_t lastJoinAttempt = 0;

// Field test mode display state
bool fieldTestModeActive = true;
uint32_t lastFieldTestUpdate = 0;
const uint32_t FIELD_TEST_REFRESH_MS = 500;  // 2Hz refresh rate (500ms)
char fieldTestLine1[32] = "";
char fieldTestLine2[32] = "";
char fieldTestLine3[32] = "";
char fieldTestLine4[32] = "";

// Current LoRaWAN state for field test display
enum LoRaState {
    STATE_INIT,
    STATE_BOOT,
    STATE_JOINING,
    STATE_JOIN_TX,
    STATE_JOINED,
    STATE_JOIN_FAILED,
    STATE_TX,
    STATE_LINK_DEAD
};

LoRaState currentLoRaState = STATE_INIT;

// ============================================================================
// DISPLAY MANAGEMENT
// ============================================================================

bool displayOn = false;
uint32_t displayTimeout = 0;
const uint32_t DISPLAY_TIMEOUT_MS = 10000;  // 10 seconds

void displayInit() {
    pinMode(OLED_RST, OUTPUT);
    digitalWrite(OLED_RST, LOW);
    delay(50);
    digitalWrite(OLED_RST, HIGH);
    
    display.init();
    display.flipScreenVertically();
    display.setFont(ArialMT_Plain_10);
    
    displayOn = true;
    displayTimeout = millis() + DISPLAY_TIMEOUT_MS;
}

void displayUpdate(const char* line1, const char* line2 = "", const char* line3 = "", const char* line4 = "") {
    if (!displayOn) return;
    
    display.clear();
    display.setTextAlignment(TEXT_ALIGN_LEFT);
    display.drawString(0, 0, line1);
    if (strlen(line2) > 0) display.drawString(0, 16, line2);
    if (strlen(line3) > 0) display.drawString(0, 32, line3);
    if (strlen(line4) > 0) display.drawString(0, 48, line4);
    display.display();
    
    displayTimeout = millis() + DISPLAY_TIMEOUT_MS;
}

void displaySleep() {
    if (displayOn) {
        display.displayOff();
        displayOn = false;
    }
}

void displayWake() {
    if (!displayOn) {
        display.displayOn();
        displayOn = true;
        displayTimeout = millis() + DISPLAY_TIMEOUT_MS;
    }
}

void displayCheck() {
    if (displayOn && millis() > displayTimeout) {
        displaySleep();
    }
}

// ============================================================================
// LED BLINK FUNCTIONS (Field Test Mode)
// ============================================================================

void ledBlink(int duration_ms = 200) {
    digitalWrite(STATUS_LED, HIGH);
    delay(duration_ms);
    digitalWrite(STATUS_LED, LOW);
}

void ledBlinkTx() {
    // Quick double blink for TX
    ledBlink(100);
    delay(50);
    ledBlink(100);
}

void ledBlinkJoined() {
    // Triple blink for successful join
    for (int i = 0; i < 3; i++) {
        ledBlink(150);
        delay(100);
    }
}

// ============================================================================
// FIELD TEST MODE DISPLAY
// ============================================================================

void fieldTestModeUpdate() {
    if (!fieldTestModeActive) return;
    
    // Non-blocking 2Hz refresh
    if (millis() - lastFieldTestUpdate < FIELD_TEST_REFRESH_MS) {
        return;
    }
    lastFieldTestUpdate = millis();
    
    // Update display based on current LoRaWAN state
    switch (currentLoRaState) {
        case STATE_INIT:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "BUILD: 1.0.2");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "FIELD TEST MODE");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "Initializing...");
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_BOOT:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "BUILD: 1.0.2");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "BOOT OK");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "Starting LoRaWAN...");
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_JOINING:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "JOINING (%lu)", joinAttempts);
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "Attempting OTAA...");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "TTN Network");
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_JOIN_TX:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "JOIN TX OK");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "Wait for JOINED");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "RX Window");
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_JOINED:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "JOINED!");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "DevAddr: %08lX", LMIC.devaddr);
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "TX Count: %lu", txCount);
            snprintf(fieldTestLine4, sizeof(fieldTestLine4), "Ready for uplink");
            break;
            
        case STATE_JOIN_FAILED:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "JOIN FAIL");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "Retry %lu", joinAttempts);
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "Check TTN config");
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_TX:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "UPLINK #%lu", txCount);
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "TX in progress...");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "RSSI: %d dBm", sensorData.rssi);
            fieldTestLine4[0] = '\0';
            break;
            
        case STATE_LINK_DEAD:
            snprintf(fieldTestLine1, sizeof(fieldTestLine1), "LINK DEAD");
            snprintf(fieldTestLine2, sizeof(fieldTestLine2), "Reconnecting...");
            snprintf(fieldTestLine3, sizeof(fieldTestLine3), "TX Count: %lu", txCount);
            fieldTestLine4[0] = '\0';
            break;
    }
    
    // Update OLED display
    displayUpdate(fieldTestLine1, fieldTestLine2, fieldTestLine3, fieldTestLine4);
}

void fieldTestModeSetState(LoRaState newState) {
    currentLoRaState = newState;
    // Force immediate update on state change
    lastFieldTestUpdate = 0;
}

// ============================================================================
// SENSOR ACQUISITION
// ============================================================================

void sensorsInit() {
    Serial.println("Initializing sensors on GPIO21/22 I²C bus...");
    
    // Initialize sensor I²C bus (GPIO21=SDA, GPIO22=SCL)
    // Use Wire1 instead of Wire to avoid conflicts with display
    if (!sensorWire.begin(SENSOR_SDA, SENSOR_SCL, 100000)) {
        Serial.println("✗ Failed to initialize sensor I²C bus!");
        sensorData.mlx_valid = false;
        sensorData.tsl_valid = false;
    } else {
        Serial.println("✓ Sensor I²C bus initialized");
    }
    
    // MLX90614 IR Temperature Sensor (with timeout protection)
    if (sensorWire.available()) {
        sensorData.mlx_valid = mlx.begin(MLX90614_I2CADDR, &sensorWire);
        if (sensorData.mlx_valid) {
            Serial.println("✓ MLX90614 initialized (0x5A)");
        } else {
            Serial.println("✗ MLX90614 not found!");
        }
    } else {
        Serial.println("✗ MLX90614 skipped (I²C bus error)");
        sensorData.mlx_valid = false;
    }
    
    // TSL2591 Sky Quality Meter (with timeout protection)
    if (sensorWire.available()) {
        sensorData.tsl_valid = tsl.begin(&sensorWire);
        if (sensorData.tsl_valid) {
            tsl.setGain(TSL2591_GAIN_LOW);  // 1x gain for bright sky
            tsl.setTiming(TSL2591_INTEGRATIONTIME_100MS);
            Serial.println("✓ TSL2591 initialized (0x29)");
        } else {
            Serial.println("✗ TSL2591 not found!");
        }
    } else {
        Serial.println("✗ TSL2591 skipped (I²C bus error)");
        sensorData.tsl_valid = false;
    }
    
    // Rain Sensor (Analog ADC)
    pinMode(RAIN_PIN, INPUT);
    sensorData.rain_valid = true;
    Serial.println("✓ Rain sensor on GPIO36");
    
    // Wind Sensor (Pulse Interrupt)
    pinMode(WIND_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(WIND_PIN), windPulseISR, FALLING);
    sensorData.wind_valid = true;
    Serial.println("✓ Wind sensor on GPIO32");
}

void sensorsRead() {
    // MLX90614 IR Temperature
    if (sensorData.mlx_valid) {
        sensorData.sky_temperature = mlx.readObjectTempC();
        sensorData.ambient_temperature = mlx.readAmbientTempC();
        
        // Validation: reasonable range check
        if (sensorData.sky_temperature < -60 || sensorData.sky_temperature > 60) {
            sensorData.mlx_valid = false;
        }
        if (sensorData.ambient_temperature < -30 || sensorData.ambient_temperature > 60) {
            sensorData.mlx_valid = false;
        }
    }
    
    // TSL2591 Sky Quality Meter
    if (sensorData.tsl_valid) {
        uint32_t lum = tsl.getFullLuminosity();
        sensorData.sqm_ir = lum >> 16;
        sensorData.sqm_full = lum & 0xFFFF;
        sensorData.sqm_visible = sensorData.sqm_full - sensorData.sqm_ir;
        sensorData.sqm_lux = tsl.calculateLux(sensorData.sqm_full, sensorData.sqm_ir);
        
        // Validation: check for overflow
        if (sensorData.sqm_lux < 0 || sensorData.sqm_full == 0xFFFF) {
            sensorData.tsl_valid = false;
        }
    }
    
    // Rain Sensor (Analog ADC 0-4095, map to 0-1023)
    if (sensorData.rain_valid) {
        uint32_t adcSum = 0;
        for (int i = 0; i < 10; i++) {
            adcSum += analogRead(RAIN_PIN);
            delay(10);
        }
        uint16_t adcValue = adcSum / 10;  // Average of 10 readings
        sensorData.rain_intensity = map(adcValue, 0, 4095, 0, 1023);
        
        // Validation: sanity check
        if (adcValue > 4095) {
            sensorData.rain_valid = false;
        }
    }
    
    // Wind Sensor (Pulse Counting)
    if (sensorData.wind_valid) {
        // Calculate wind speed from pulse count over last interval
        // Assuming: 1 pulse = 0.1 m/s (calibration depends on sensor datasheet)
        static uint32_t lastWindCount = 0;
        static uint32_t lastWindTime = 0;
        uint32_t now = millis();
        uint32_t deltaCount = windPulseCount - lastWindCount;
        uint32_t deltaTime = now - lastWindTime;
        
        if (deltaTime > 0) {
            // Wind speed = (pulses * calibration_factor * 1000) / time_ms
            sensorData.wind_speed = (deltaCount * 0.1f * 1000.0f) / deltaTime;
        }
        
        lastWindCount = windPulseCount;
        lastWindTime = now;
        
        // Validation: reasonable range
        if (sensorData.wind_speed < 0 || sensorData.wind_speed > 70.0f) {
            sensorData.wind_valid = false;
        }
    }
    
    // Diagnostics
    sensorData.uptime_seconds = millis() / 1000;
    
    // Battery voltage (if LiPo connected)
    // TODO: Read battery voltage from ADC if applicable
    sensorData.battery_mv = 0;  // Not implemented yet
}

void sensorsPrint() {
    Serial.println("\n=== Sensor Readings ===");
    
    if (sensorData.mlx_valid) {
        Serial.printf("MLX90614: Sky=%.2f°C, Ambient=%.2f°C\n",
                      sensorData.sky_temperature, sensorData.ambient_temperature);
    } else {
        Serial.println("MLX90614: INVALID");
    }
    
    if (sensorData.tsl_valid) {
        Serial.printf("TSL2591: IR=%u, Full=%u, Vis=%u, Lux=%.2f\n",
                      sensorData.sqm_ir, sensorData.sqm_full,
                      sensorData.sqm_visible, sensorData.sqm_lux);
    } else {
        Serial.println("TSL2591: INVALID");
    }
    
    if (sensorData.rain_valid) {
        Serial.printf("Rain: %u (0=wet, 1023=dry)\n", sensorData.rain_intensity);
    } else {
        Serial.println("Rain: INVALID");
    }
    
    if (sensorData.wind_valid) {
        Serial.printf("Wind: %.2f m/s (%lu pulses)\n", 
                      sensorData.wind_speed, windPulseCount);
    } else {
        Serial.println("Wind: INVALID");
    }
    
    Serial.printf("Uptime: %lu seconds\n", sensorData.uptime_seconds);
    Serial.println("=======================\n");
}

// ============================================================================
// LORAWAN PAYLOAD ENCODING
// ============================================================================

uint8_t encodePayload(uint8_t* buffer) {
    /*
     * Payload Format (Binary, 30 bytes):
     * 
     * Byte 0-1:   Rain intensity (uint16, 0-1023)
     * Byte 2-3:   Wind speed (int16, m/s * 100)
     * Byte 4-5:   Sky temperature (int16, °C * 100)
     * Byte 6-7:   Ambient temperature (int16, °C * 100)
     * Byte 8-9:   SQM IR (uint16)
     * Byte 10-11: SQM Full (uint16)
     * Byte 12-13: SQM Visible (uint16)
     * Byte 14-17: SQM Lux (float32)
     * Byte 18-21: Uptime seconds (uint32)
     * Byte 22-23: Battery voltage (uint16, mV)
     * Byte 24:    Data validity flags (uint8)
     * Byte 25-26: RSSI (int16, updated after TX)
     * Byte 27:    SNR (int8, updated after TX)
     * Byte 28-29: Reserved
     */
    
    uint8_t idx = 0;
    
    // Rain intensity (uint16)
    buffer[idx++] = (sensorData.rain_intensity >> 8) & 0xFF;
    buffer[idx++] = sensorData.rain_intensity & 0xFF;
    
    // Wind speed (int16, m/s * 100)
    int16_t wind_scaled = (int16_t)(sensorData.wind_speed * 100.0f);
    buffer[idx++] = (wind_scaled >> 8) & 0xFF;
    buffer[idx++] = wind_scaled & 0xFF;
    
    // Sky temperature (int16, °C * 100)
    int16_t sky_temp_scaled = (int16_t)(sensorData.sky_temperature * 100.0f);
buffer[idx++] = (sky_temp_scaled >> 8) & 0xFF;
    buffer[idx++] = sky_temp_scaled & 0xFF;
    
    // Ambient temperature (int16, °C * 100)
    int16_t amb_temp_scaled = (int16_t)(sensorData.ambient_temperature * 100.0f);
    buffer[idx++] = (amb_temp_scaled >> 8) & 0xFF;
    buffer[idx++] = amb_temp_scaled & 0xFF;
    
    // SQM IR (uint16)
    buffer[idx++] = (sensorData.sqm_ir >> 8) & 0xFF;
    buffer[idx++] = sensorData.sqm_ir & 0xFF;
    
    // SQM Full (uint16)
    buffer[idx++] = (sensorData.sqm_full >> 8) & 0xFF;
    buffer[idx++] = sensorData.sqm_full & 0xFF;
    
    // SQM Visible (uint16)
    buffer[idx++] = (sensorData.sqm_visible >> 8) & 0xFF;
    buffer[idx++] = sensorData.sqm_visible & 0xFF;
    
    // SQM Lux (float32)
    union {
        float f;
        uint8_t bytes[4];
    } lux_union;
    lux_union.f = sensorData.sqm_lux;
    buffer[idx++] = lux_union.bytes[3];
    buffer[idx++] = lux_union.bytes[2];
    buffer[idx++] = lux_union.bytes[1];
    buffer[idx++] = lux_union.bytes[0];
    
    // Uptime seconds (uint32)
    buffer[idx++] = (sensorData.uptime_seconds >> 24) & 0xFF;
    buffer[idx++] = (sensorData.uptime_seconds >> 16) & 0xFF;
    buffer[idx++] = (sensorData.uptime_seconds >> 8) & 0xFF;
    buffer[idx++] = sensorData.uptime_seconds & 0xFF;
    
    // Battery voltage (uint16, mV)
    buffer[idx++] = (sensorData.battery_mv >> 8) & 0xFF;
    buffer[idx++] = sensorData.battery_mv & 0xFF;
    
    // Data validity flags (bit-packed uint8)
    uint8_t flags = 0;
    if (sensorData.mlx_valid) flags |= (1 << 0);
    if (sensorData.tsl_valid) flags |= (1 << 1);
    if (sensorData.rain_valid) flags |= (1 << 2);
    if (sensorData.wind_valid) flags |= (1 << 3);
    buffer[idx++] = flags;
    
    // RSSI (int16, filled after TX)
    buffer[idx++] = (sensorData.rssi >> 8) & 0xFF;
    buffer[idx++] = sensorData.rssi & 0xFF;
    
    // SNR (int8, filled after TX)
    buffer[idx++] = (uint8_t)sensorData.snr;
    
    // Reserved
    buffer[idx++] = 0x00;
    buffer[idx++] = 0x00;
    
    return idx;  // Should be 30 bytes
}

// ============================================================================
// LORAWAN EVENT HANDLER
// ============================================================================

void onEvent(ev_t ev) {
    Serial.printf("[%lu] Event: ", millis() / 1000);
    
    switch(ev) {
        case EV_SCAN_TIMEOUT:
            Serial.println("EV_SCAN_TIMEOUT");
            break;
        case EV_BEACON_FOUND:
            Serial.println("EV_BEACON_FOUND");
            break;
        case EV_BEACON_MISSED:
            Serial.println("EV_BEACON_MISSED");
            break;
        case EV_BEACON_TRACKED:
            Serial.println("EV_BEACON_TRACKED");
            break;
        case EV_JOINING:
            Serial.println("EV_JOINING");
            joinAttempts++;
            lastJoinAttempt = millis();
            fieldTestModeSetState(STATE_JOINING);
            break;
        case EV_JOINED:
            Serial.println("EV_JOINED");
            joined = true;
            LMIC_setLinkCheckMode(0);
            fieldTestModeSetState(STATE_JOINED);
            ledBlinkJoined();  // Triple blink for successful join
            // Schedule first transmission
            nextTransmissionTime = millis() + 5000;  // 5 seconds after join
            break;
        case EV_JOIN_FAILED:
            Serial.println("EV_JOIN_FAILED");
            fieldTestModeSetState(STATE_JOIN_FAILED);
            break;
        case EV_REJOIN_FAILED:
            Serial.println("EV_REJOIN_FAILED");
            fieldTestModeSetState(STATE_JOIN_FAILED);
            break;
        case EV_TXCOMPLETE:
            Serial.println("EV_TXCOMPLETE (TXDONE IRQ received)");
            transmitting = false;
            txCount++;  // Increment TX counter
            
            // Capture signal quality
            sensorData.rssi = LMIC.rssi;
            sensorData.snr = LMIC.snr;
            
            Serial.printf("RSSI: %d dBm, SNR: %d dB\n", sensorData.rssi, sensorData.snr);
            
            // Return to JOINED state after successful TX
            if (joined) {
                fieldTestModeSetState(STATE_JOINED);
            }
            
            if (LMIC.txrxFlags & TXRX_ACK) {
                Serial.println("Received ACK");
            }
            if (LMIC.dataLen) {
                Serial.printf("Received %d bytes downlink\n", LMIC.dataLen);
            }
            
            // Schedule next transmission
            nextTransmissionTime = millis() + TX_INTERVAL_MS;
            break;
        case EV_LOST_TSYNC:
            Serial.println("EV_LOST_TSYNC");
            break;
        case EV_RESET:
            Serial.println("EV_RESET");
            break;
        case EV_RXCOMPLETE:
            Serial.println("EV_RXCOMPLETE");
            break;
        case EV_LINK_DEAD:
            Serial.println("EV_LINK_DEAD");
            fieldTestModeSetState(STATE_LINK_DEAD);
            break;
        case EV_LINK_ALIVE:
            Serial.println("EV_LINK_ALIVE");
            if (joined) {
                fieldTestModeSetState(STATE_JOINED);
            }
            break;
        case EV_TXSTART:
            Serial.println("EV_TXSTART");
            displayWake();
            fieldTestModeSetState(STATE_TX);
            ledBlinkTx();  // Double blink for TX start
            break;
        case EV_TXCANCELED:
            Serial.println("EV_TXCANCELED");
            if (joined) {
                fieldTestModeSetState(STATE_JOINED);
            }
            break;
        case EV_RXSTART:
            Serial.println("EV_RXSTART");
            break;
        case EV_JOIN_TXCOMPLETE:
            Serial.println("EV_JOIN_TXCOMPLETE");
            fieldTestModeSetState(STATE_JOIN_TX);
            break;
        default:
            Serial.printf("Unknown event: %u\n", (unsigned)ev);
            break;
    }
}

// ============================================================================
// LORAWAN TRANSMISSION
// ============================================================================

void do_send(osjob_t* j) {
    // Check if LMIC is busy
    if (LMIC.opmode & OP_TXRXPEND) {
        Serial.println("OP_TXRXPEND, not sending");
        return;
    }
    
    // Read sensors
    sensorsRead();
    sensorsPrint();
    
    // Encode payload
    uint8_t payload[30];
    uint8_t payloadLen = encodePayload(payload);
    
    Serial.printf("Encoded %u bytes, queueing for transmission\n", payloadLen);
    
    // Queue packet
    LMIC_setTxData2(1, payload, payloadLen, 0);
    transmitting = true;
}

// ============================================================================
// SETUP
// ============================================================================

void setup() {
    // Initialize serial
    Serial.begin(115200);
    delay(500);
    
    Serial.println("\n\n=== AllSky Sensors - Heltec WiFi LoRa 32 V2 ===");
    Serial.println("BUILD VERSION: 1.0.2 - FIELD TEST MODE (NO SERIAL)");
    Serial.println("Hardware: ESP32-PICO-D4 + SX1276 LoRa + OLED");
    Serial.printf("Boot completed at %lu ms\n\n", millis());
    
    // Initialize status LED for field test mode
    pinMode(STATUS_LED, OUTPUT);
    digitalWrite(STATUS_LED, LOW);
    Serial.println("✓ Status LED initialized (GPIO25)");
    
    // Initialize display
    displayInit();
    fieldTestModeSetState(STATE_INIT);
    delay(1000);
    
    // Initialize sensors
    sensorsInit();
    delay(1000);
    
    // Set boot state
    fieldTestModeSetState(STATE_BOOT);
    delay(1000);
    
    // Check TTN credentials
    bool configured = false;
    for (int i = 0; i < 8; i++) {
        if (DEVEUI[i] != 0x00 || APPEUI[i] != 0x00) {
            configured = true;
            break;
        }
    }
    for (int i = 0; i < 16; i++) {
        if (APPKEY[i] != 0x00) {
            configured = true;
            break;
        }
    }
    
    if (!configured) {
        Serial.println("\n⚠️  WARNING: TTN credentials not configured!");
        Serial.println("Please update src/secrets.h with your TTN device credentials");
        displayUpdate("ERROR", "No TTN Config", "Check secrets.h");
        while(1) {
            delay(1000);
        }
    }
    
    Serial.println("TTN credentials detected");
    
    // Print credentials for TTN verification BEFORE join
    Serial.println("\n=== TTN CREDENTIAL VERIFICATION ===");
    Serial.println("Compare these values with your TTN Console:\n");
    
    // DevEUI - LMIC expects LSB format, TTN shows both formats
    Serial.print("DevEUI (LSB->MSB as stored): ");
    for (int i = 0; i < 8; i++) {
        Serial.printf("%02X", DEVEUI[i]);
        if (i < 7) Serial.print("-");
    }
    Serial.println();
    
    Serial.print("DevEUI (MSB->LSB reversed):   ");
    for (int i = 7; i >= 0; i--) {
        Serial.printf("%02X", DEVEUI[i]);
        if (i > 0) Serial.print("-");
    }
    Serial.println(" ← Use this if TTN shows MSB format\n");
    
    // AppEUI/JoinEUI - LMIC expects LSB format
    Serial.print("AppEUI (LSB->MSB as stored): ");
    for (int i = 0; i < 8; i++) {
        Serial.printf("%02X", APPEUI[i]);
        if (i < 7) Serial.print("-");
    }
    Serial.println();
    
    Serial.print("AppEUI (MSB->LSB reversed):   ");
    for (int i = 7; i >= 0; i--) {
        Serial.printf("%02X", APPEUI[i]);
        if (i > 0) Serial.print("-");
    }
    Serial.println(" ← Use this if TTN shows MSB format\n");
    
    // AppKey - MSB format (NOT reversed)
    Serial.print("AppKey (MSB as-is):          ");
    for (int i = 0; i < 16; i++) {
        Serial.printf("%02X", APPKEY[i]);
        if (i < 15) Serial.print("-");
    }
    Serial.println(" ← Must match TTN exactly\n");
    
    Serial.println("TTN Console Notes:");
    Serial.println("- DevEUI & AppEUI: Toggle 'LSB' in TTN Console, copy-paste to secrets.h");
    Serial.println("- AppKey: Use default MSB format from TTN Console");
    Serial.println("- If join fails, verify byte order and check TTN Live Data tab");
    Serial.println("===================================\n");
    
    Serial.println("Initializing LoRaWAN...\n");
    
    // Initialize SPI explicitly for Heltec V2 BEFORE os_init()
    // SCK=GPIO5, MISO=GPIO19, MOSI=GPIO27 (hardware-wired to SX1276)
    SPI.begin(5, 19, 27);
    Serial.println("✓ SPI initialized (SCK=5, MISO=19, MOSI=27)");
    
    // Initialize LMIC
    Serial.println("Calling os_init()...");
    os_init();
    Serial.println("✓ LMIC initialized");
    LMIC_reset();
    Serial.println("✓ LMIC reset complete");
    
    // EU868 channels configured by library - no manual setup needed for LMIC 3.x
    
    LMIC_setLinkCheckMode(0);
    LMIC.dn2Dr = DR_SF9;
    LMIC_setDrTxpow(DR_SF7, 14);
    
    Serial.println("Starting OTAA join...");
    // Field test mode will show join state automatically via onEvent()
    
    // Start join
    LMIC_startJoining();
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
    // Increment loop counter for diagnostics
    loopCount++;
    
    // Periodic loop execution confirmation
    if (millis() - lastLoopLog >= LOOP_LOG_INTERVAL_MS) {
        Serial.printf("[LOOP] Running normally - %lu iterations in last %lu ms\n",
                      loopCount, millis() - lastLoopLog);
        loopCount = 0;
        lastLoopLog = millis();
    }
    
    // Run LMIC scheduler (time-critical, must not be blocked)
    os_runloop_once();
    
    // Update field test mode display (non-blocking 2Hz refresh)
    fieldTestModeUpdate();
    
    // Check display timeout
    displayCheck();
    
    // Transmission scheduling
    if (joined && !transmitting && millis() >= nextTransmissionTime) {
        do_send(&sendjob);
    }
    
    // No delay - LMIC requires continuous servicing for RX windows
    // Watchdog is automatically handled by yield() inside os_runloop_once()
}
