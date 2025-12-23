/*
 * Wi-Fi Fallback Mode
 * 
 * Wi-Fi connection management and HTTP status server
 */

#ifndef WIFI_FALLBACK_H
#define WIFI_FALLBACK_H

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>

// ============================================================================
// WIFI CONFIGURATION
// ============================================================================

extern const uint32_t WIFI_RETRY_INTERVAL_MS;
extern const uint32_t WIFI_CONNECTION_TIMEOUT_MS;

// ============================================================================
// WIFI WEB SERVER
// ============================================================================

extern WebServer wifiServer;

// ============================================================================
// WIFI FUNCTIONS
// ============================================================================

// Start Wi-Fi fallback mode (stop LoRa, connect Wi-Fi, start HTTP server)
void wifiFallbackStart();

// Stop Wi-Fi fallback mode and return to LoRa
void wifiFallbackStop();

// Handle Wi-Fi fallback loop (handle HTTP requests, check connection)
void wifiFallbackLoop();

// HTTP status endpoint handler
void handleWifiStatus();

// Test Wi-Fi connection (diagnose connectivity issues)
void wifiTestConnection();

#endif // WIFI_FALLBACK_H
