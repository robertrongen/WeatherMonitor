/*
 * Display Management - Implementation
 */

#include "display.h"

// ============================================================================
// DISPLAY OBJECTS
// ============================================================================

// Display (128x64 OLED on internal I²C bus)
SSD1306Wire display(OLED_ADDR, OLED_SDA, OLED_SCL);

// ============================================================================
// DISPLAY STATE
// ============================================================================

bool displayOn = false;
uint32_t displayTimeout = 0;
const uint32_t DISPLAY_TIMEOUT_MS = 10000;  // 10 seconds

// ============================================================================
// DISPLAY FUNCTIONS
// ============================================================================

void displayInit() {
    pinMode(OLED_RST, OUTPUT);
    digitalWrite(OLED_RST, LOW);
    delay(50);
    digitalWrite(OLED_RST, HIGH);
    
    display.init();
    display.flipScreenVertically();
    display.setFont(ArialMT_Plain_10);
    
    displayOn = true;
    displayTimeout = millis() + DISPLAY_TIMEOUT_MS;
}

void displayUpdate(const char* line1, const char* line2, const char* line3, const char* line4) {
    if (!displayOn) return;
    
    display.clear();
    display.setTextAlignment(TEXT_ALIGN_LEFT);
    display.drawString(0, 0, line1);
    if (strlen(line2) > 0) display.drawString(0, 16, line2);
    if (strlen(line3) > 0) display.drawString(0, 32, line3);
    if (strlen(line4) > 0) display.drawString(0, 48, line4);
    display.display();
    
    displayTimeout = millis() + DISPLAY_TIMEOUT_MS;
}

void displaySleep() {
    if (displayOn) {
        display.displayOff();
        displayOn = false;
    }
}

void displayWake() {
    if (!displayOn) {
        display.displayOn();
        displayOn = true;
        displayTimeout = millis() + DISPLAY_TIMEOUT_MS;
    }
}

void displayCheck() {
    if (displayOn && millis() > displayTimeout) {
        displaySleep();
    }
}
