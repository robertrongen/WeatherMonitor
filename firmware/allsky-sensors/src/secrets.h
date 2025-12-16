/*
 * AllSky Sensors - LoRaWAN Configuration Template
 * 
 * Copy this file to src/secrets.h and update with your TTN device credentials
 * 
 * Get these values from TTN Console:
 * 1. Go to Console: https://console.thethingsnetwork.org/
 * 2. Select your Application
 * 3. Go to Devices > [Your Device] > Overview
 * 4. Copy the values from the "Activation information" section
 */

#ifndef SECRETS_H
#define SECRETS_H

// TTN Device Credentials - REPLACE WITH YOUR VALUES
// Device EUI (8 bytes, little-endian format)
// Example: 00 11 22 33 44 55 66 77
static const unsigned char DEVEUI[8] = {0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x07, 0x4C, 0x96};

// Application EUI (8 bytes, little-endian format)
// Example: 00 AA BB CC DD EE FF 00
static const unsigned char APPEUI[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// Application Key (16 bytes)
// Example: 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF 00
static const unsigned char APPKEY[16] = {
    0xD1, 0xEB, 0x2E, 0x78, 0xB2, 0x16, 0xEF, 0xF4, 
    0xA3, 0x4C, 0x5D, 0x9A, 0x1E, 0x2B, 0x3C, 0x4D
};

#endif // SECRETS_H