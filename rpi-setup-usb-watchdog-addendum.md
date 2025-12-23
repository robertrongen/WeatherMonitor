# Addendum – USB Stability & Watchdog Hardening

This addendum documents **post-baseline changes** made to stabilize the AllSky + Safety Monitor Raspberry Pi system under real-world failure conditions.

It is intended to complement `rpi-setup.md` and should be read **after** the baseline setup.

---

## 1. Context and Problem Summary

After long-term operation, the system began exhibiting:

- Repeated USB reset storms:
  ```
  reset high-speed USB device using xhci_hcd
  ```
- Loss of WiFi connectivity while userland processes (AllSky) continued running
- Eventual loss of `/current/tmp/image.jpg`
- Recovery possible **only via power cycling**

A full OS reinstall and default AllSky configuration **did not resolve** the issue.

Root cause analysis showed this to be a **kernel-level USB host degradation** scenario rather than application failure.

---

## 2. Hardware Context (Important)

- Platform: **Compute Module 4 (CM4)**
- Camera: **ZWO ASI224MC**
- USB topology:
  - Camera connected directly
  - No space for USB hub in enclosure
- CM4 constraint:
  - USB traffic always passes through `xhci_hcd`
  - `dtoverlay=disable-usb3` does **not** remove xHCI on CM4

This limits available mitigation options to **USB traffic reduction and recovery hardening**.

---

## 3. USB Configuration Changes

### 3.1 Force USB 2 Operation (Physical)

- Camera moved to **black USB port**
- Verified with:
  ```bash
  lsusb -t
  ```
  Camera enumerates at `480M` (High-Speed)

> Note: On CM4, xHCI remains active even for USB2 devices.

---

### 3.2 Disable USB Autosuspend (Kernel)

In `/boot/firmware/cmdline.txt` (single line):

```
usbcore.autosuspend=-1
```

Purpose:
- Prevents USB power-state transitions
- Reduces endpoint timing jitter

---

### 3.3 Increase Available USB Current

In `/boot/firmware/config.txt`:

```
max_usb_current=1
```

Purpose:
- Reduces marginal power dips during camera readout

---

### 3.4 Lock Camera USB Bandwidth (AllSky)

In **AllSky WebUI → Camera Settings**:

- USB Bandwidth: **30**
- USB Auto: **OFF**

Purpose:
- Prevents dynamic burst ramp-up
- Reduces xHCI transaction pressure
- Critical for CM4 stability

---

## 4. Persistent Logging (Required for Debugging)

Enable persistent journaling:

```bash
sudo mkdir -p /var/log/journal
sudo systemctl restart systemd-journald
```

This allows post-crash inspection:

```bash
journalctl -b -1
```

---

## 5. Recovery Strategy Overview

Because failures occur in stages, recovery is **layered**:

| Layer | Action | Scope |
|-----|------|------|
| 1 | WiFi reset | Recover radio / firmware issues |
| 2 | Controlled reboot | Recover partial kernel degradation |
| 3 | Power cycle | Last resort (external) |

This addendum implements **Layers 1 and 2**.

---

## 6. WiFi Reset Mechanism (Layer 1)

### 6.1 WiFi Reset Script

`/usr/local/bin/reset_wifi.sh`

```bash
#!/bin/bash
logger -t wifiwatch "Resetting WiFi interface"

nmcli radio wifi off
sleep 3
nmcli radio wifi on
sleep 5

nmcli device disconnect wlan0
sleep 2
nmcli device connect wlan0
```

```bash
sudo chmod +x /usr/local/bin/reset_wifi.sh
```

---

### 6.2 WiFi Health Check

`/usr/local/bin/check_wifi.sh`

```bash
#!/bin/bash
GW=$(ip route | awk '/default/ {print $3; exit}')
[ -z "$GW" ] && exit 0

if ping -c 1 -W 2 "$GW" >/dev/null 2>&1; then
  exit 0
fi

logger -t wifiwatch "Gateway unreachable, attempting WiFi reset"
/usr/local/bin/reset_wifi.sh
```

Scheduled via cron:

```bash
*/5 * * * * /usr/local/bin/check_wifi.sh
```

---

## 7. System Watchdog (Layer 2)

This watchdog escalates to reboot **only after sustained failure**.

### 7.1 Watchdog Script

`/usr/local/bin/system_watchdog.sh`

```bash
#!/bin/bash

STATE="/var/run/syswatch_failcount"
MAX_FAILS=3
fail=0

# Network check
GW=$(ip route | awk '/default/ {print $3; exit}')
if [ -z "$GW" ] || ! ping -c 1 -W 2 "$GW" >/dev/null 2>&1; then
  fail=1
fi

# AllSky image freshness
IMG="/home/robert/allsky/current/tmp/image.jpg"
MAX_AGE=300

if [ ! -f "$IMG" ]; then
  fail=1
else
  AGE=$(( $(date +%s) - $(stat -c %Y "$IMG") ))
  [ "$AGE" -gt "$MAX_AGE" ] && fail=1
fi

COUNT=$(cat "$STATE" 2>/dev/null || echo 0)

if [ "$fail" -eq 0 ]; then
  rm -f "$STATE"
  exit 0
fi

COUNT=$((COUNT+1))
echo "$COUNT" > "$STATE"

logger -t syswatch "Health failure $COUNT/$MAX_FAILS"

if [ "$COUNT" -ge "$MAX_FAILS" ]; then
  logger -t syswatch "System unhealthy, rebooting"
  reboot
fi
```

```bash
sudo chmod +x /usr/local/bin/system_watchdog.sh
```

---

### 7.2 Watchdog Scheduling

```bash
*/5 * * * * /usr/local/bin/system_watchdog.sh
```

Effect:
- Single transient failure → ignored
- Repeated failure over ~15 minutes → reboot
- Prevents reboot flapping

---

## 8. Explicitly Out of Scope

The following are **not** solved by software watchdogs:

- Hard xHCI lockups
- USB PHY electrical failure
- Kernel deadlocks

For these cases, **remote power control** (smart plug) remains mandatory.

---

## 9. Final Notes

- The system architecture remains correct
- Failures are handled gracefully where possible
- Reboots are controlled, not reactive
- Evidence is preserved for post-mortem analysis

This addendum reflects a **production-grade hardening strategy** for unattended AllSky installations with marginal USB hardware.

---

## 10. USB Reset Storm Interceptor (Early-Failure Watchdog)

This section extends the watchdog strategy with **early interception of USB reset storms**, which are a reliable precursor to full system failure.

### 10.1 Rationale

Kernel log events of the form:

```
usb X-Y.Z: reset high-speed USB device using xhci_hcd
```

indicate that the USB host controller is repeatedly resetting a misbehaving device.
When this happens multiple times in a short window, system degradation is imminent.

This interceptor reacts **before WiFi loss or kernel wedging occurs**.

---

### 10.2 Detection Policy

Default thresholds:

- Event pattern: `reset high-speed USB device`
- Window: **180 seconds**
- Threshold: **5 events**

These values are intentionally conservative and can be tuned if needed.

---

### 10.3 USB Reset Watchdog Script

`/usr/local/bin/usb_reset_watchdog.sh`

```bash
#!/bin/bash

PATTERN="reset high-speed USB device"
WINDOW_SECONDS=180
MAX_EVENTS=5

STATE="/var/run/usb_reset_events"

journalctl -k --since "-${WINDOW_SECONDS} seconds"   | grep "$PATTERN"   | awk '{print $1" "$2" "$3}'   | while read -r ts; do
      date -d "$ts" +%s
    done > "$STATE.new" 2>/dev/null

count=$(wc -l < "$STATE.new" 2>/dev/null || echo 0)
mv "$STATE.new" "$STATE" 2>/dev/null

if [ "$count" -ge "$MAX_EVENTS" ]; then
  logger -t usbwatch "USB reset storm detected ($count events in ${WINDOW_SECONDS}s)"

  systemctl stop allsky.service
  sleep 5

  logger -t usbwatch "Rebooting system to prevent USB lockup"
  reboot
fi
```

Make executable:

```bash
sudo chmod +x /usr/local/bin/usb_reset_watchdog.sh
```

---

### 10.4 Scheduling

```bash
*/2 * * * * /usr/local/bin/usb_reset_watchdog.sh
```

---

### 10.5 Escalation Model

1. WiFi reset
2. AllSky restart
3. USB reset storm interceptor
4. Controlled reboot
5. External power reset

---

### 10.6 Limitations

This mechanism cannot recover from:

- hard kernel lockups
- USB PHY electrical faults
- xHCI controller deadlocks

External power cycling remains mandatory for full recovery in those cases.