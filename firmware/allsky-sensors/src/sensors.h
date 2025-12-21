/*
 * Sensor Management
 * 
 * Sensor initialization, data acquisition, and validation
 * (No transport logic - pure sensor I/O)
 */

#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <Adafruit_TSL2591.h>

// ============================================================================
// SENSOR PIN CONFIGURATION
// ============================================================================

// Sensor I²C Bus (External GPIO21/22 - separate from display)
#define SENSOR_SDA 21
#define SENSOR_SCL 22

// Rain Sensor (Analog)
#define RAIN_PIN 36  // GPIO36 (ADC1_CH0)

// Wind Sensor (Pulse Interrupt)
#define WIND_PIN 32  // GPIO32 (safe for interrupt, no LoRa conflict)

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

extern SensorData sensorData;

// ============================================================================
// SENSOR OBJECTS
// ============================================================================

extern Adafruit_MLX90614 mlx;
extern Adafruit_TSL2591 tsl;
extern TwoWire sensorWire;

// ============================================================================
// WIND SENSOR STATE (Pulse Counting)
// ============================================================================

extern volatile uint32_t windPulseCount;
extern volatile uint32_t lastWindPulse;
extern const uint32_t WIND_DEBOUNCE_MS;

// Wind pulse ISR
void IRAM_ATTR windPulseISR();

// ============================================================================
// SENSOR FUNCTIONS
// ============================================================================

// Initialize all sensors
void sensorsInit();

// Read all sensors and update sensorData
void sensorsRead();

// Print sensor readings to Serial
void sensorsPrint();

#endif // SENSORS_H
