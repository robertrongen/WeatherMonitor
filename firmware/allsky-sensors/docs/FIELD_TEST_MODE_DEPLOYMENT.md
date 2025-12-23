# Field Test Mode Deployment Guide
## BUILD VERSION: 1.0.2 - FIELD TEST MODE (NO SERIAL)

### Overview
Field Test Mode provides visual feedback on the OLED display for LoRaWAN join status and uplink progress without requiring serial monitor access. Perfect for roof deployment where the device runs on a powerbank.

### Key Features Added
- ✅ **OLED Display States**: Shows join progress, TX status, and DevAddr
- ✅ **Status LED**: Visual feedback for TX (double blink) and JOINED (triple blink)
- ✅ **Counters**: Join attempts and TX count display
- ✅ **Non-blocking**: 2Hz refresh rate, doesn't interfere with LMIC timing
- ✅ **Always On**: No compile flags needed, always active for simple deployment

### OLED Display States

| State | Line 1 | Line 2 | Line 3 | Line 4 |
|-------|--------|--------|--------|--------|
| **Boot** | BUILD: 1.0.2 | BOOT OK | Starting LoRaWAN... | |
| **Joining** | JOINING (n) | Attempting OTAA... | TTN Network | |
| **Join TX** | JOIN TX OK | Wait for JOINED | RX Window | |
| **Joined** | JOINED! | DevAddr: 08XXXXXX | TX Count: n | Ready for uplink |
| **Join Failed** | JOIN FAIL | Retry n | Check TTN config | |
| **TX** | UPLINK #n | TX in progress... | RSSI: -XX dBm | |
| **Link Dead** | LINK DEAD | Reconnecting... | TX Count: n | |

### LED Blink Patterns
- **TX Start**: Double blink (2x 100ms)
- **Joined**: Triple blink (3x 150ms)
- **Join Failed**: Single blink (200ms)

### Deployment Instructions

#### 1. Build and Flash
```bash
cd firmware/allsky-sensors
pio device upload
```

#### 2. Deploy Outside
1. Power on the device (powerbank or DC supply)
2. OLED will immediately show "BUILD: 1.0.2" and "BOOT OK"
3. Watch for join progress on OLED display

#### 3. Monitor TTN Live Data
1. Go to [The Things Network Console](https://console.thethingsnetwork.org/)
2. Navigate to your device
3. Open "Live Data" tab
4. You should see join attempts and uplinks

#### 4. Visual Confirmation Sequence
```
Boot → JOINING (1) → JOIN TX OK → JOINED! → UPLINK #1 → UPLINK #2...
         ↑                                      ↓
    Check TTN config                   RSSI: -XX dBm
```

### Troubleshooting

#### OLED Not Showing
- Check power connections
- Verify OLED I2C connections (GPIO4/15)

#### Stuck on "JOINING"
- Check TTN device credentials in `secrets.h`
- Verify antenna connection
- Check TTN Live Data for join attempts

#### No LED Blinks
- Status LED uses GPIO25 (Heltec onboard LED)
- If no LED, check GPIO25 connection

#### "JOIN FAIL" Messages
- Verify DevEUI/AppEUI byte order (LSB format)
- Check AppKey format (MSB format)
- Ensure device is activated in TTN

### Technical Notes
- **Refresh Rate**: 2Hz (500ms intervals)
- **Non-blocking**: Uses timestamp checking, no delays
- **Memory**: Minimal impact on RAM/Flash
- **LMIC Compatibility**: No changes to LoRaWAN behavior
- **Power**: Status LED adds ~2-3mA consumption

### File Changes Summary
**Modified**: `src/main.cpp`
- Added field test mode state management
- Integrated with existing LMIC event handler
- Added LED blink functions
- Enhanced OLED display with 2Hz refresh
- Updated build version to 1.0.2

### Next Steps
1. Deploy device to roof/powerbank
2. Watch OLED for join progress
3. Confirm data in TTN Live Data
4. Monitor TX count incrementing every 60 seconds

**Ready for field deployment!** 🚀