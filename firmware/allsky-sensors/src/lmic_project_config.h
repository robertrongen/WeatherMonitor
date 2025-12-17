// Arduino-LMIC Project Configuration for Heltec WiFi LoRa 32 V2
// Region: EU868
// Radio: Semtech SX1276

#define CFG_eu868 1
//#define CFG_us915 1
//#define CFG_au921 1
//#define CFG_as923 1
//#define CFG_in866 1

// Radio type (Heltec WiFi LoRa 32 V2 uses SX1276)
#define CFG_sx1276_radio 1

// Disable features not needed for basic OTAA operation
#define DISABLE_PING 1
#define DISABLE_BEACONS 1

// Enable USB serial debug output for OTAA diagnostics
#define LMIC_PRINTF_TO Serial
#define LMIC_DEBUG_LEVEL 2
