/*
 * LoRa/LoRaWAN Management - Implementation
 */

#include "lora.h"
#include "system_state.h"
#include "display.h"
#include "sensors.h"
#include "diagnostics.h"
#include "secrets.h"
#include <SPI.h>

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
// LORA PIN CONFIGURATION
// ============================================================================

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
// LORAWAN STATE
// ============================================================================

osjob_t sendjob;
bool joined = false;
bool transmitting = false;
uint32_t nextTransmissionTime = 0;
const uint32_t TX_INTERVAL_MS = 60000;  // 60 seconds

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
            consecutiveCycleFails = 0;  // Reset failure counter on successful join
            LMIC_setLinkCheckMode(0);
            fieldTestModeSetState(STATE_JOINED);
            ledBlinkJoined();  // Triple blink for successful join
            // Schedule first transmission
            nextTransmissionTime = millis() + 5000;  // 5 seconds after join
            break;
        case EV_JOIN_FAILED:
            Serial.println("EV_JOIN_FAILED");
            fieldTestModeSetState(STATE_JOIN_FAILED);
            // Note: Join failures will be counted as cycle failures in do_send
            break;
        case EV_REJOIN_FAILED:
            Serial.println("EV_REJOIN_FAILED");
            fieldTestModeSetState(STATE_JOIN_FAILED);
            // Note: Join failures will be counted as cycle failures in do_send
            break;
        case EV_TXCOMPLETE:
            Serial.println("EV_TXCOMPLETE (TXDONE IRQ received)");
            transmitting = false;
            txCount++;  // Increment TX counter
            
            // Track transmission cycle success
            static bool awaitingTXComplete = false;
            if (awaitingTXComplete) {
                // Successfully completed transmission cycle
                Serial.println("[LORA] Transmission cycle completed successfully");
                consecutiveCycleFails = 0;  // Reset failure counter
                awaitingTXComplete = false;
            } else {
                // Unexpected TX complete without pending cycle
                Serial.println("[LORA] TX complete without pending cycle");
            }
            
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
            
            // Track transmission cycle failure
            Serial.println("[LORA] Transmission cycle failed - TX canceled");
            consecutiveCycleFails++;
            Serial.printf("[LORA] Consecutive transmission failures: %u / %u\n", 
                         consecutiveCycleFails, AUTO_WIFI_AFTER_N_CYCLE_FAILURES);
            
            // Auto-activate Wi-Fi fallback after N cycle failures
            if (consecutiveCycleFails >= AUTO_WIFI_AFTER_N_CYCLE_FAILURES && !wifiFallbackEnabled) {
                Serial.println("[LORA] Too many transmission failures - auto-enabling Wi-Fi fallback");
                wifiFallbackEnabled = true;
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
    
    // Track transmission cycle for failure counting
    static bool awaitingTXComplete = false;
    awaitingTXComplete = true;  // Mark that we're awaiting TX completion
    
    // Queue packet
    LMIC_setTxData2(1, payload, payloadLen, 0);
    transmitting = true;
}

// ============================================================================
// LORA INITIALIZATION
// ============================================================================

void loraInit() {
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
// STOP LORA (for Wi-Fi Fallback Mode)
// ============================================================================

void stopLoRa() {
    Serial.println("[WIFI] Stopping LMIC...");
    // Cancel pending LMIC jobs to prevent retries, joins, or uplinks
    os_clearCallback(&sendjob);
    Serial.println("[WIFI] Cleared pending LMIC jobs");
}
