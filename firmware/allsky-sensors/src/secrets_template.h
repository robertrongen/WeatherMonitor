/*
 * TTN Credentials Template for OTAA (Over-The-Air Activation)
 * 
 * Setup Instructions:
 * 1. Copy this file to secrets.h:
 *    cp src/secrets_template.h src/secrets.h
 * 
 * 2. Go to TTN Console: https://console.thethingsnetwork.org/
 *    - Select your application
 *    - Go to "Devices" → Select your device → "Overview"
 * 
 * 3. Copy credentials in LSB format:
 *    - DevEUI: Copy as "Little-endian (LSB)" - paste below
 *    - AppEUI/JoinEUI: Copy as "Little-endian (LSB)" - paste below  
 *    - AppKey: Copy as "MSB" format - paste below
 * 
 * 4. IMPORTANT: Delete this template after creating secrets.h
 * 
 * Example Format:
 * static const uint8_t DEVEUI[8] = { 0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF };
 * static const uint8_t APPEUI[8] = { 0xFE, 0xDC, 0xBA, 0x98, 0x76, 0x54, 0x32, 0x10 };
 * static const uint8_t APPKEY[16] = { 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
 *                                      0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF };
 */

#ifndef SECRETS_H
#define SECRETS_H

#include <stdint.h>

// DevEUI (Device EUI) - 8 bytes, LSB format
// Get from TTN Console > Devices > [Your Device] > Overview > DevEUI
// IMPORTANT: Copy in "Little-endian (LSB)" format from TTN Console
static const uint8_t DEVEUI[8] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

// AppEUI / JoinEUI - 8 bytes, LSB format
// Get from TTN Console > Applications > [Your App] > Overview > AppEUI
// IMPORTANT: Copy in "Little-endian (LSB)" format from TTN Console
static const uint8_t APPEUI[8] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

// AppKey (Application Key) - 16 bytes, MSB format
// Get from TTN Console > Devices > [Your Device] > Overview > AppKey
// IMPORTANT: Copy in "MSB" format from TTN Console (default display)
static const uint8_t APPKEY[16] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

/*
 * OTAA Configuration Notes:
 * 
 * - DevEUI: Unique device identifier (LSB format for TTN)
 * - AppEUI/JoinEUI: Application identifier (LSB format for TTN)
 * - AppKey: Application-specific encryption key (MSB format)
 * 
 * TTN Console will show toggle buttons for "MSB" / "LSB" byte order.
 * Make sure to select the correct format as specified above.
 * 
 * After join, the device will receive:
 * - DevAddr (dynamic network address)
 * - NwkSKey (network session key)
 * - AppSKey (application session key)
 * 
 * These are stored internally by LMIC and do not need to be configured.
 */

#endif // SECRETS_H
