/*
 * AllSky Sensors - Minimal LoRaWAN Firmware (Step 1)
 * ESP32 DevKit V1 + RFM95W LoRa Module
 * 
 * This firmware implements minimal LoRaWAN OTAA join and test uplink
 * to The Things Network (TTN) without any sensor functionality.
 * 
 * Hardware Configuration:
 * - Board: ESP32 DevKit V1
 * - LoRa Module: RFM95W (SX1276)
 * - SPI Pins: GPIO18 (SCK), GPIO19 (MISO), GPIO23 (MOSI)
 * - Control Pins: GPIO2 (CS), GPIO4 (DIO0), GPIO5 (DIO1)
 * 
 * Setup Instructions:
 * 1. Copy src/secrets_template.h to src/secrets.h
 * 2. Update secrets.h with your TTN device credentials
 * 3. Run: pio device list (to find ESP32 port)
 * 4. Run: pio device monitor (to see serial output)
 * 5. Run: pio run --target upload (to upload firmware)
 */

#include <Arduino.h>
#include <lmic.h>
#include <hal/hal.h>
#include "secrets.h"

// Pin mapping for RFM95W module
const lmic_pinmap lmic_pins = {
    .nss = 2,        // GPIO2 (CS)
    .rxtx = LMIC_UNUSED_PIN,
    .rst = LMIC_UNUSED_PIN,
    .dio = {4, 5, LMIC_UNUSED_PIN},  // GPIO4 (DIO0), GPIO5 (DIO1)
    .rx_level = LMIC_UNUSED_PIN,
    .rssi_cal = 10,  // RSSI calibration
    .spi_freq = 8000000  // 8 MHz SPI frequency
};

// Global state
static osjob_t sendjob;
bool joined = false;
bool data_sent = false;

// Function prototypes
void do_send(osjob_t* j);
void onEvent (ev_t ev);

// Serial logging helper
void serial_log(const char* format, ...) {
    char buffer[256];
    va_list args;
    va_start(args, format);
    vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    Serial.println(buffer);
}

// LMIC event handler
void onEvent (ev_t ev) {
    serial_log("Event: %d", ev);
    
    switch(ev) {
        case EV_SCAN_TIMEOUT:
            serial_log("EV_SCAN_TIMEOUT");
            break;
        case EV_BEACON_FOUND:
            serial_log("EV_BEACON_FOUND");
            break;
        case EV_BEACON_MISSED:
            serial_log("EV_BEACON_MISSED");
            break;
        case EV_BEACON_TRACKED:
            serial_log("EV_BEACON_TRACKED");
            break;
        case EV_JOINING:
            serial_log("EV_JOINING");
            break;
        case EV_JOINED:
            serial_log("EV_JOINED");
            joined = true;
            
            // Disable link check validation (optional)
            LMIC_setLinkCheckMode(0);
            
            // Start sending data after successful join
            serial_log("Starting data transmission...");
            do_send(&sendjob);
            break;
        case EV_JOIN_FAILED:
            serial_log("EV_JOIN_FAILED");
            break;
        case EV_REJOIN_FAILED:
            serial_log("EV_REJOIN_FAILED");
            break;
        case EV_TXCOMPLETE:
            serial_log("EV_TXCOMPLETE");
            data_sent = true;
            if (LMIC.txrxFlags & TXRX_ACK) {
                serial_log("Received ACK");
            }
            if (LMIC.dataLen) {
                serial_log("Received %d bytes of data", LMIC.dataLen);
                for (int i = 0; i < LMIC.dataLen; i++) {
                    Serial.printf("%02X ", LMIC.frame[LMIC.dataBeg + i]);
                }
                Serial.println();
            }
            break;
        case EV_LOST_TSYNC:
            serial_log("EV_LOST_TSYNC");
            break;
        case EV_RESET:
            serial_log("EV_RESET");
            break;
        case EV_RXCOMPLETE:
            serial_log("EV_RXCOMPLETE");
            break;
        case EV_LINK_DEAD:
            serial_log("EV_LINK_DEAD");
            break;
        case EV_LINK_ALIVE:
            serial_log("EV_LINK_ALIVE");
            break;
        default:
            serial_log("Unknown event: %d", ev);
            break;
    }
}

// Send function - transmits hardcoded test payload
void do_send(osjob_t* j) {
    // Check if there's not a pending TX/RX job running
    if (LMIC.opmode & OP_TXRXPEND) {
        serial_log("OP_TXRXPEND, not sending");
        return;
    }
    
    // Prepare payload
    static uint8_t payload[] = {0x01, 0x02, 0x03};  // 3-byte test payload
    
    // Prepare upstream data transmission at the next possible time.
    LMIC_setTxData2(1, payload, sizeof(payload), 0);
    serial_log("Packet queued for transmission");
}

// Setup function
void setup() {
    // Initialize serial
    Serial.begin(115200);
    delay(100);
    
    serial_log("=== AllSky Sensors - LoRaWAN Firmware (Step 1) ===");
    serial_log("ESP32 DevKit V1 + RFM95W LoRa Module");
    serial_log("Boot completed at %lu ms", millis());
    
    // Check if DEVEUI/APPEUI/APPKEY are configured
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
        serial_log("WARNING: TTN credentials not configured!");
        serial_log("Please update src/secrets.h with your TTN device credentials");
        serial_log("Get these from TTN Console > Devices > [Your Device] > Overview");
        while(1) {
            delay(1000);
        }
    }
    
    serial_log("TTN credentials detected - starting LMIC initialization");
    
    // Initialize LMIC
    serial_log("Initializing LMIC...");
    os_init();
    LMIC_reset();
    
    // Set session parameters using values from secrets.h
    uint8_t appskey[sizeof(APPKEY)];
    uint8_t nwkskey[sizeof(APPKEY)];
    memcpy(appskey, APPKEY, sizeof(APPKEY));
    memcpy(nwkskey, APPKEY, sizeof(APPKEY));
    
    LMIC_setSession(0x13, 0x12345678, appskey, nwkskey);
    
    // Set up the channels used by the Things Network, which corresponds
    // to the defaults of many gateways. Without this, only three base
    // channels from the LoRaWAN specification are used, which certainly
    // works, so it is good for debugging, but can overload those
    // frequencies.
    LMIC_setupChannel(0, 868100000, DR_RANGE_MAP(DR_SF12, DR_SF7),  BAND_CENTI);      // g-band
    LMIC_setupChannel(1, 868300000, DR_RANGE_MAP(DR_SF12, DR_SF7),  BAND_CENTI);      // g-band  
    LMIC_setupChannel(2, 868500000, DR_RANGE_MAP(DR_SF12, DR_SF7),  BAND_CENTI);      // g-band
    LMIC_setupChannel(3, 867100000, DR_RANGE_MAP(DR_SF12, DR_SF7),  BAND_CENTI);      // g-band
    LMIC_setupChannel(4, 867300000, DR_RANGE_MAP(DR_SF12, DR_SF7),  BAND_CENTI);      // g-band
    LMIC_setupChannel(5, 867500000, DR_RANGE_MAP(DR_SF12, DR_SF7),  BAND_CENTI);      // g-band
    LMIC_setupChannel(6, 867700000, DR_RANGE_MAP(DR_SF12, DR_SF7),  BAND_CENTI);      // g-band
    LMIC_setupChannel(7, 867900000, DR_RANGE_MAP(DR_SF12, DR_SF7),  BAND_CENTI);      // g-band
    
    // Disable link check validation
    LMIC_setLinkCheckMode(0);
    
    // TTN uses SF9 for its RX2 window
    LMIC.dn2Dr = DR_SF9;
    
    // Set data rate and transmit power for uplink
    LMIC_setDrTxpow(DR_SF7, 14);
    
    serial_log("LMIC initialization complete");
    serial_log("Starting OTAA join procedure...");
    
    // Start join process
    LMIC_startJoining();
}

// Main loop
void loop() {
    os_runloop_once();
    
    // After successful join and data transmission, stop the application
    if (joined && data_sent) {
        serial_log("=== Step 1 Complete: Join and Test Uplink Successful ===");
        serial_log("Device joined TTN and transmitted test payload");
        serial_log("Stopping firmware - Step 1 verification complete");
        while(1) {
            delay(60000);  // Keep alive but do nothing
        }
    }
    
    // Small delay to prevent watchdog issues
    delay(10);
}