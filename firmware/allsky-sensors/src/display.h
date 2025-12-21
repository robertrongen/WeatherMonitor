/*
 * Display Management
 * 
 * OLED display initialization, update, sleep/wake control
 */

#ifndef DISPLAY_H
#define DISPLAY_H

#include <Arduino.h>
#include <SSD1306Wire.h>

// ============================================================================
// DISPLAY PIN CONFIGURATION
// ============================================================================

#define OLED_SDA 4
#define OLED_SCL 15
#define OLED_RST 16
#define OLED_ADDR 0x3C

// ============================================================================
// DISPLAY STATE
// ============================================================================

extern SSD1306Wire display;
extern bool displayOn;
extern uint32_t displayTimeout;
extern const uint32_t DISPLAY_TIMEOUT_MS;

// ============================================================================
// DISPLAY FUNCTIONS
// ============================================================================

// Initialize display hardware and turn it on
void displayInit();

// Update display content (up to 4 lines)
void displayUpdate(const char* line1, const char* line2 = "", const char* line3 = "", const char* line4 = "");

// Turn display off (power save)
void displaySleep();

// Turn display on (wake from sleep)
void displayWake();

// Check if display should timeout and sleep
void displayCheck();

#endif // DISPLAY_H
