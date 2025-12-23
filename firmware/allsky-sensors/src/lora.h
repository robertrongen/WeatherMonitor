/*
 * LoRa/LoRaWAN Management
 * 
 * LMIC initialization, event handling, transmission scheduling
 */

#ifndef LORA_H
#define LORA_H

#include <Arduino.h>
#include <lmic.h>
#include <hal/hal.h>

// ============================================================================
// LORA PIN CONFIGURATION
// ============================================================================

// LoRa Pin Mapping (Heltec WiFi LoRa 32 V2 - aligned with BSP)
extern const lmic_pinmap lmic_pins;

// ============================================================================
// LORAWAN STATE
// ============================================================================

extern osjob_t sendjob;
extern bool joined;
extern bool transmitting;
extern uint32_t nextTransmissionTime;
extern const uint32_t TX_INTERVAL_MS;

// ============================================================================
// LORAWAN CALLBACK FUNCTIONS (Required by MCCI LMIC 4.x)
// ============================================================================

// Application EUI for OTAA (from secrets.h)
void os_getArtEui(u1_t* buf);

// Device EUI for OTAA (from secrets.h)
void os_getDevEui(u1_t* buf);

// Application Key for OTAA (from secrets.h)
void os_getDevKey(u1_t* buf);

// ============================================================================
// LORA FUNCTIONS
// ============================================================================

// Initialize LoRa hardware and LMIC
void loraInit();

// LMIC event handler
void onEvent(ev_t ev);

// Transmission job (read sensors, encode, send)
void do_send(osjob_t* j);

// Encode sensor data to binary payload
uint8_t encodePayload(uint8_t* buffer);

// Stop LoRa (called before entering Wi-Fi fallback mode)
void stopLoRa();

// Handle join retry logic with exponential backoff (call from main loop)
void loraHandleJoinRetry();

#endif // LORA_H
