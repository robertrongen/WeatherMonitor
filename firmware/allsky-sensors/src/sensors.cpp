/*
 * Sensor Management - Implementation
 */

#include "sensors.h"

// ============================================================================
// SENSOR DATA
// ============================================================================

SensorData sensorData = {0};

// ============================================================================
// SENSOR OBJECTS
// ============================================================================

// Sensor Objects (on external I²C bus GPIO21/22)
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
Adafruit_TSL2591 tsl = Adafruit_TSL2591(2591);

// Sensor I²C Bus (separate from display)
TwoWire sensorWire = TwoWire(1);  // Use I2C bus 1 for sensors

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
// SENSOR INITIALIZATION
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

// ============================================================================
// SENSOR READING
// ============================================================================

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

// ============================================================================
// SENSOR PRINTING
// ============================================================================

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
